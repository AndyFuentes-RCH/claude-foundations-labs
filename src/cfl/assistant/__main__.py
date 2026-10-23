"""CLI del asistente: python -m cfl.assistant "¿Estado de RMX-2026-000104?" --provider mock"""

from __future__ import annotations

import argparse
import json
import sys

from cfl.assistant.agent import SupportAssistant
from cfl.config import Settings
from cfl.evidence import EvidenceRecorder, record_assistant_result
from cfl.providers import PROVIDERS, ProviderUnavailable, build_provider, provider_status
from cfl.tools import build_default_toolbox

PROJECT_BY_PROVIDER = {"mock": "02-asistente-claude-api", "anthropic": "02-asistente-claude-api",
                       "vertex": "05-claude-google-cloud", "bedrock": "06-claude-amazon-bedrock"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Asistente de soporte de remesas sintéticas")
    parser.add_argument("query", help="Pregunta del agente de soporte")
    parser.add_argument("--provider", choices=PROVIDERS, default=None)
    parser.add_argument("--no-record", action="store_true", help="No registrar la ejecución en docs/evidence")
    args = parser.parse_args(argv)

    settings = Settings.from_env()
    name = args.provider or settings.default_provider
    status = provider_status(name, settings)
    print(f"Proveedor: {status.label} | Modelo: {status.model} | Modo: {status.mode}", file=sys.stderr)
    try:
        provider = build_provider(name, settings)
    except ProviderUnavailable as exc:
        print(f"PENDIENTE — falta: {', '.join(exc.missing)}", file=sys.stderr)
        return 2

    assistant = SupportAssistant(provider, build_default_toolbox(settings), max_iterations=settings.max_tool_iterations)
    result = None
    for event in assistant.stream(args.query):
        kind = event["type"]
        if kind == "text":
            print(event["text"], end="", flush=True)
        elif kind == "tool_call":
            print(f"\n  → herramienta {event['name']}({json.dumps(event['input'], ensure_ascii=False)})", file=sys.stderr)
        elif kind == "tool_result":
            flag = "error " + str(event["error_code"]) if event["is_error"] else f"found={event['found']}"
            print(f"  ← {event['name']}: {flag}", file=sys.stderr)
        elif kind in ("warning", "error"):
            print(f"\n[{kind.upper()}] {event.get('message')}", file=sys.stderr)
        elif kind == "done":
            result = event["result"]
    print()
    if result and not args.no_record:
        entry = record_assistant_result(EvidenceRecorder(settings.evidence_dir), PROJECT_BY_PROVIDER[name], result, notes="CLI")
        print(f"Registrado en evidencia: run_id={entry['run_id']}", file=sys.stderr)
    return 0 if result and result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
