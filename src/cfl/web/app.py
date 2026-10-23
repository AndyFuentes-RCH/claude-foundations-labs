"""API e interfaz web de los laboratorios.

    uvicorn cfl.web.app:app --reload --port 8000
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterator

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from cfl.assistant import SupportAssistant
from cfl.config import REPO_ROOT, Settings
from cfl.evidence import EvidenceRecorder, record_assistant_result
from cfl.labs.catalog import LABS, LABS_BY_KEY
from cfl.labs.prompt_lab import PROMPT_LABS, run_lab
from cfl.providers import PROVIDERS, ProviderUnavailable, all_statuses, build_provider, provider_status
from cfl.tools import Toolbox, build_default_toolbox

STATIC_DIR = Path(__file__).parent / "static"


class AssistantRequest(BaseModel):
    lab: str = Field(default="02", pattern=r"^\d{2}$")
    provider: str = "mock"
    query: str = Field(min_length=1, max_length=2000)


class McpRequest(BaseModel):
    transaction_id: str | int | None = None


class PromptLabRequest(BaseModel):
    provider: str = "anthropic"


def create_app(settings: Settings | None = None, toolbox: Toolbox | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    toolbox = toolbox or build_default_toolbox(settings)
    recorder = EvidenceRecorder(settings.evidence_dir)
    app = FastAPI(title="claude-foundations-labs", version="0.1.0")
    app.state.settings, app.state.toolbox, app.state.recorder = settings, toolbox, recorder

    @app.get("/", include_in_schema=False)
    def index() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    @app.get("/api/labs")
    def labs() -> dict[str, Any]:
        return {"labs": [lab.to_dict() for lab in LABS], "providers": [s.to_dict() for s in all_statuses(settings)]}

    @app.get("/api/labs/{key}")
    def lab_detail(key: str) -> dict[str, Any]:
        lab = LABS_BY_KEY.get(key)
        if lab is None:
            raise HTTPException(404, "Laboratorio no encontrado")
        base = REPO_ROOT / "labs" / lab.folder
        materials = []
        for rel in lab.materials:
            path = base / rel
            if path.exists():
                materials.append({"path": f"labs/{lab.folder}/{rel}", "content": path.read_text(encoding="utf-8")})
        outputs = []
        if key in PROMPT_LABS:
            out_dir = base / PROMPT_LABS[key].output_dir
            outputs = sorted(p.name for p in out_dir.glob("*.md") if p.name != "README.md") if out_dir.exists() else []
        return {"lab": lab.to_dict(), "materials": materials, "outputs": outputs,
                "providers": [provider_status(p, settings).to_dict() for p in lab.providers]}

    @app.get("/api/providers")
    def providers() -> list[dict[str, Any]]:
        return [s.to_dict() for s in all_statuses(settings)]

    @app.post("/api/assistant/stream")
    def assistant_stream(req: AssistantRequest) -> StreamingResponse:
        lab = LABS_BY_KEY.get(req.lab)
        if lab is None or lab.kind not in {"assistant", "cache"}:
            raise HTTPException(400, "El laboratorio no usa el asistente")
        if req.provider not in PROVIDERS or req.provider not in lab.providers:
            raise HTTPException(400, f"Proveedor no válido para el laboratorio {req.lab}")
        return StreamingResponse(_sse(_assistant_events(req, lab.folder)), media_type="text/event-stream")

    def _assistant_events(req: AssistantRequest, folder: str) -> Iterator[dict[str, Any]]:
        status = provider_status(req.provider, settings)
        yield {"type": "meta", "provider": status.label, "provider_key": status.provider, "model": status.model,
               "mode": status.mode, "query": req.query}
        try:
            provider = build_provider(req.provider, settings)
        except ProviderUnavailable as exc:
            yield {"type": "pending", "missing": exc.missing}
            return
        assistant = SupportAssistant(provider, toolbox, max_iterations=settings.max_tool_iterations)
        for event in assistant.stream(req.query):
            if event["type"] == "done":
                result = event["result"]
                entry = record_assistant_result(recorder, folder, result, notes="Interfaz web")
                yield {"type": "done", "answer": result.answer, "model": result.model, "mode": result.mode,
                       "tools_used": result.tools_used, "iterations": result.iterations, "stop_reason": result.stop_reason,
                       "request_ids": result.request_ids, "usage": result.usage, "records_consulted": result.records_consulted,
                       "ungrounded_ids": result.ungrounded_ids, "error": result.error, "duration_ms": result.duration_ms,
                       "run_id": entry["run_id"], "extra": _extra_metrics(toolbox)}
            else:
                yield event

    @app.post("/api/mcp/call")
    async def mcp_call(req: McpRequest) -> dict[str, Any]:
        from mcp import Client

        from cfl.mcp_server.server import create_server

        args = {} if req.transaction_id is None else {"transaction_id": req.transaction_id}
        async with Client(create_server(toolbox)) as client:
            result = await client.call_tool("get_transaction_status", args)
        text = " ".join(getattr(b, "text", "") for b in result.content)
        entry = recorder.record(
            project="07-model-context-protocol", mode="MOCK", provider="cliente MCP local (in-memory) — sin Claude",
            model=None, input=args, output=result.structured_content or text,
            tools_invoked=[{"name": "get_transaction_status", "arguments": args, "is_error": result.is_error}],
            notes="Interfaz web: prueba del cliente MCP local, no conectada a Claude.",
        )
        return {"mode": "MOCK", "provider": "Cliente MCP local (sin Claude)", "model": None, "query": args,
                "is_error": result.is_error, "structured": result.structured_content, "text": text,
                "tools_used": [{"name": "get_transaction_status", "input": args, "is_error": result.is_error}],
                "run_id": entry["run_id"]}

    @app.post("/api/prompt-labs/{key}/run")
    def prompt_lab_run(key: str, req: PromptLabRequest) -> dict[str, Any]:
        if key not in PROMPT_LABS:
            raise HTTPException(404, "Laboratorio de prompts no encontrado")
        status = provider_status(req.provider, settings)
        if status.mode != "LIVE":
            return {"mode": status.mode, "provider": status.label, "model": status.model, "missing": status.missing, "outputs": []}
        try:
            paths = run_lab(key, req.provider, settings)
        except ProviderUnavailable as exc:  # pragma: no cover - carrera improbable
            return {"mode": "PENDIENTE", "missing": exc.missing, "outputs": []}
        return {"mode": "LIVE", "provider": status.label, "model": status.model,
                "outputs": [str(p.relative_to(REPO_ROOT)) for p in paths]}

    @app.get("/api/evidence")
    def evidence(limit: int = 20) -> list[dict[str, Any]]:
        return recorder.read_all()[-limit:][::-1]

    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    return app


def _extra_metrics(toolbox: Toolbox) -> dict[str, Any]:
    stats = getattr(toolbox.repository, "stats", None)
    return {"cache": stats()} if callable(stats) else {}


def _sse(events: Iterator[dict[str, Any]]) -> Iterator[str]:
    for event in events:
        yield f"data: {json.dumps(event, ensure_ascii=False, default=str)}\n\n"


app = create_app()
