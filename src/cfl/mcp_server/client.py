"""Cliente MCP de prueba (Proyecto 7): lanza el servidor por stdio y ejercita tool, resource y prompt.

    python -m cfl.mcp_server.client            # stdio (subproceso real)
    python -m cfl.mcp_server.client --in-memory

Esto es una prueba del **cliente local**: no interviene Claude. La conexión real con Claude se documenta
en labs/07-model-context-protocol/README.md.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

import anyio
from mcp import Client, StdioServerParameters
from mcp.types import TextContent

from cfl.config import REPO_ROOT, Settings
from cfl.evidence import EvidenceRecorder

CASES = [
    ("existente", {"transaction_id": "RMX-2026-000104"}),
    ("inexistente", {"transaction_id": "RMX-2026-999999"}),
    ("formato inválido", {"transaction_id": "RMX-12"}),
    ("tipo inválido", {"transaction_id": 12345}),
    ("argumento faltante", {}),
]


def stdio_params() -> StdioServerParameters:
    return StdioServerParameters(command=sys.executable, args=["-m", "cfl.mcp_server.server"], cwd=str(REPO_ROOT))


def _text(result: Any) -> str:
    return " ".join(b.text for b in result.content if isinstance(b, TextContent))


async def exercise(target: Any) -> dict[str, Any]:
    """Recorre las capacidades del servidor y devuelve un informe serializable."""
    report: dict[str, Any] = {"tools": [], "resources": [], "prompts": [], "calls": []}
    async with Client(target) as client:
        tools = await client.list_tools()
        report["tools"] = [{"name": t.name, "read_only": bool(t.annotations and t.annotations.read_only_hint)} for t in tools.tools]
        resources = await client.list_resources()
        report["resources"] = [str(r.uri) for r in resources.resources]
        policies = await client.read_resource("policies://soporte-remesas")
        report["resource_preview"] = policies.contents[0].text[:120]
        prompts = await client.list_prompts()
        report["prompts"] = [p.name for p in prompts.prompts]
        prompt = await client.get_prompt("investigar_incidente", {"transaction_id": "RMX-2026-000111"})
        report["prompt_preview"] = prompt.messages[0].content.text[:120]
        for label, args in CASES:
            result = await client.call_tool("get_transaction_status", args)
            report["calls"].append({
                "case": label,
                "arguments": args,
                "is_error": result.is_error,
                "structured": result.structured_content,
                "text": None if result.structured_content else _text(result)[:200],
            })
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Cliente MCP de prueba (sin Claude)")
    parser.add_argument("--in-memory", action="store_true", help="Conecta en memoria en lugar de stdio")
    parser.add_argument("--no-record", action="store_true")
    args = parser.parse_args(argv)

    if args.in_memory:
        from cfl.mcp_server.server import create_server

        target: Any = create_server()
        transport = "in-memory"
    else:
        target, transport = stdio_params(), "stdio"
    report = anyio.run(exercise, target)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not args.no_record:
        entry = EvidenceRecorder(Settings.from_env().evidence_dir).record(
            project="07-model-context-protocol",
            mode="MOCK",
            provider=f"cliente MCP local ({transport}) — sin Claude",
            model=None,
            input=[c[1] for c in CASES],
            output={"calls": [{k: c[k] for k in ("case", "is_error")} for c in report["calls"]],
                    "tools": report["tools"], "resources": report["resources"], "prompts": report["prompts"]},
            tools_invoked=[{"name": "get_transaction_status", "arguments": c[1]} for c in CASES],
            notes="Prueba del cliente MCP local. No es una ejecución conectada a Claude.",
        )
        print(f"Registrado en evidencia: run_id={entry['run_id']}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
