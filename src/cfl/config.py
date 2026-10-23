"""Configuración centralizada leída de variables de entorno (y de .env si existe)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data" / "synthetic"


def _bool(value: str | None, default: bool = False) -> bool:
    if value is None or value.strip() == "":
        return default
    return value.strip().lower() in {"1", "true", "yes", "si", "sí", "on"}


def _int(value: str | None, default: int) -> int:
    try:
        return int(value) if value not in (None, "") else default
    except ValueError:
        return default


def _str(value: str | None, default: str) -> str:
    return value.strip() if value and value.strip() else default


@dataclass(frozen=True)
class Settings:
    default_provider: str = "mock"
    allow_live_calls: bool = False
    max_tool_iterations: int = 5
    effort: str = "medium"
    max_tokens: int = 16000
    simulated_latency_ms: int = 0
    evidence_dir: Path = REPO_ROOT / "docs" / "evidence"
    transactions_path: Path = DATA_DIR / "transactions.json"
    policies_path: Path = DATA_DIR / "support_policies.json"

    anthropic_model: str = "claude-opus-5-5"
    enable_server_fallbacks: bool = True

    vertex_project_id: str | None = None
    vertex_region: str = "global"
    vertex_model: str = "claude-opus-5-5"

    aws_region: str | None = None
    aws_profile: str | None = None
    bedrock_model: str = "anthropic.claude-opus-5-5"

    @classmethod
    def from_env(cls, env: dict[str, str] | None = None, load_dotenv_file: bool = True) -> "Settings":
        if env is None:
            if load_dotenv_file:
                load_dotenv(REPO_ROOT / ".env", override=False)
            env = dict(os.environ)
        evidence = env.get("CFL_EVIDENCE_DIR")
        evidence_dir = Path(evidence) if evidence else REPO_ROOT / "docs" / "evidence"
        if not evidence_dir.is_absolute():
            evidence_dir = REPO_ROOT / evidence_dir
        return cls(
            default_provider=_str(env.get("CFL_DEFAULT_PROVIDER"), "mock").lower(),
            allow_live_calls=_bool(env.get("CFL_ALLOW_LIVE_CALLS")),
            max_tool_iterations=max(1, _int(env.get("CFL_MAX_TOOL_ITERATIONS"), 5)),
            effort=_str(env.get("CFL_EFFORT"), "medium"),
            max_tokens=_int(env.get("CFL_MAX_TOKENS"), 16000),
            simulated_latency_ms=max(0, _int(env.get("CFL_SIMULATED_LATENCY_MS"), 0)),
            evidence_dir=evidence_dir,
            anthropic_model=_str(env.get("CFL_ANTHROPIC_MODEL"), "claude-opus-5-5"),
            enable_server_fallbacks=_bool(env.get("CFL_ENABLE_SERVER_FALLBACKS"), default=True),
            vertex_project_id=env.get("ANTHROPIC_VERTEX_PROJECT_ID") or None,
            vertex_region=_str(env.get("CLOUD_ML_REGION"), "global"),
            vertex_model=_str(env.get("CFL_VERTEX_MODEL"), "claude-opus-5-5"),
            aws_region=env.get("AWS_REGION") or env.get("AWS_DEFAULT_REGION") or None,
            aws_profile=env.get("AWS_PROFILE") or None,
            bedrock_model=_str(env.get("CFL_BEDROCK_MODEL"), "anthropic.claude-opus-5-5"),
        )
