"""Registro de ejecuciones en docs/evidence/runs/runs.jsonl.

Cada línea es un JSON con los campos acordados. Si un dato no está disponible se guarda `null`;
nunca se rellena con valores inventados. Las claves y tokens de acceso nunca se registran.
"""

from __future__ import annotations

import json
import subprocess
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cfl.config import REPO_ROOT

_LOCK = threading.Lock()
FIELDS = (
    "run_id",
    "timestamp_utc",
    "project",
    "mode",
    "provider",
    "model",
    "input",
    "output",
    "tools_invoked",
    "tests",
    "request_ids",
    "usage",
    "code_state",
    "notes",
)


def code_state(repo: Path = REPO_ROOT) -> dict[str, Any]:
    """Commit actual y si hay cambios sin confirmar; null si git no está disponible."""
    def _git(*args: str) -> str | None:
        try:
            out = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, timeout=5, check=True)
            return out.stdout.strip()
        except (OSError, subprocess.SubprocessError):
            return None

    commit = _git("rev-parse", "--short", "HEAD")
    status = _git("status", "--porcelain")
    return {"commit": commit, "dirty": (bool(status) if status is not None else None)}


class EvidenceRecorder:
    def __init__(self, evidence_dir: Path) -> None:
        self.path = Path(evidence_dir) / "runs" / "runs.jsonl"

    def record(self, **fields: Any) -> dict[str, Any]:
        unknown = set(fields) - set(FIELDS)
        if unknown:
            raise ValueError(f"Campos no reconocidos: {sorted(unknown)}")
        entry: dict[str, Any] = {key: None for key in FIELDS}
        entry.update(fields)
        entry["run_id"] = entry["run_id"] or uuid.uuid4().hex[:12]
        entry["timestamp_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        if entry["code_state"] is None:
            entry["code_state"] = code_state()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with _LOCK, self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")
        return entry

    def read_all(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        return [json.loads(line) for line in self.path.read_text(encoding="utf-8").splitlines() if line.strip()]


def record_assistant_result(recorder: EvidenceRecorder, project: str, result: Any, notes: str | None = None) -> dict[str, Any]:
    """Atajo para registrar un AssistantResult del Proyecto 2/4/5/6."""
    return recorder.record(
        project=project,
        mode=result.mode,
        provider=result.provider,
        model=result.model,
        input=result.query,
        output=result.answer or None,
        tools_invoked=result.tools_used or [],
        request_ids=result.request_ids or None,
        usage=result.usage or None,
        notes=notes if result.ok else f"{notes + ' | ' if notes else ''}error: {result.error}",
    )
