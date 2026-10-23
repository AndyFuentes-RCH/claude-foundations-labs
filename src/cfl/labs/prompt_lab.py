"""Ejecutor de los laboratorios de prompts (Proyecto 1 y ejecución por API del Proyecto 3).

    python -m cfl.labs.prompt_lab ejecutar 01 --provider anthropic
    python -m cfl.labs.prompt_lab ejecutar 03 --provider anthropic
    python -m cfl.labs.prompt_lab evaluar 01

Las salidas se guardan con sus metadatos reales (fecha, modelo, request-id, tokens). Sin credenciales y sin
CFL_ALLOW_LIVE_CALLS=true el laboratorio queda PENDIENTE: no se genera ningún contenido sustituto.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from cfl.config import REPO_ROOT, Settings
from cfl.evidence import EvidenceRecorder
from cfl.providers import ProviderUnavailable, build_provider, provider_status

LABS_DIR = REPO_ROOT / "labs"


@dataclass(frozen=True)
class PromptLab:
    key: str
    folder: str
    document: str
    prompts: tuple[str, ...]
    output_dir: str
    system: str


PROMPT_LABS = {
    "01": PromptLab(
        key="01",
        folder="01-colaboracion-efectiva",
        document="insumos/requisitos-integracion.md",
        prompts=("prompts/01-prompt-inicial.md", "prompts/02-prompt-mejorado.md"),
        output_dir="outputs",
        system="",
    ),
    "03": PromptLab(
        key="03",
        folder="03-flujo-productividad",
        document="insumos/documento-requisitos.md",
        prompts=("prompts/01-resumen-ejecutivo.md", "prompts/02-tabla-acciones.md", "prompts/03-correo-borrador.md"),
        output_dir="outputs-api",
        system="",
    ),
}


def render_prompt(lab: PromptLab, prompt_file: str) -> str:
    base = LABS_DIR / lab.folder
    document = (base / lab.document).read_text(encoding="utf-8")
    return (base / prompt_file).read_text(encoding="utf-8").replace("{{DOCUMENTO}}", document.strip())


def run_lab(key: str, provider_name: str, settings: Settings) -> list[Path]:
    lab = PROMPT_LABS[key]
    provider = build_provider(provider_name, settings)  # lanza ProviderUnavailable si queda PENDIENTE
    recorder = EvidenceRecorder(settings.evidence_dir)
    out_dir = LABS_DIR / lab.folder / lab.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for prompt_file in lab.prompts:
        prompt = render_prompt(lab, prompt_file)
        result = provider.complete(system=lab.system, prompt=prompt)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        entry = recorder.record(
            project=lab.folder,
            mode=provider.mode,
            provider=provider.name,
            model=result.model,
            input={"prompt_file": f"labs/{lab.folder}/{prompt_file}", "document": f"labs/{lab.folder}/{lab.document}"},
            output=result.text,
            tools_invoked=[],
            request_ids=[result.request_id] if result.request_id else None,
            usage=result.usage,
            notes=f"Ejecución por API (no Claude.ai). stop_reason={result.stop_reason}",
        )
        path = out_dir / f"{stamp}-{Path(prompt_file).stem}.md"
        header = (
            "<!--\n"
            f"run_id: {entry['run_id']}\nfecha_utc: {entry['timestamp_utc']}\nmodo: {provider.mode} (ejecución por API)\n"
            f"proveedor: {provider.name}\nmodelo: {result.model}\nrequest_id: {result.request_id}\n"
            f"uso_tokens: {result.usage}\nstop_reason: {result.stop_reason}\nprompt: labs/{lab.folder}/{prompt_file}\n"
            "-->\n\n"
        )
        path.write_text(header + result.text + "\n", encoding="utf-8")
        written.append(path)
    return written


# --- Evaluación automática del Proyecto 1 ---------------------------------------------

SECTION_PATTERNS = [
    r"resumen", r"requisitos funcionales", r"requisitos no funcionales", r"flujo", r"mapeo",
    r"errores", r"supuestos", r"preguntas abiertas", r"criterios de aceptaci",
]


def auto_evaluate(text: str) -> dict[str, object]:
    lower = text.lower()
    headings = [h.lower() for h in re.findall(r"^#{1,6}\s*(.+)$", text, flags=re.MULTILINE)]
    positions = []
    for pattern in SECTION_PATTERNS:
        idx = next((i for i, h in enumerate(headings) if re.search(pattern, h)), None)
        positions.append(idx)
    present = [p is not None for p in positions]
    found = [p for p in positions if p is not None]
    return {
        "C1_secciones_presentes": f"{sum(present)}/9",
        "C1_en_orden": found == sorted(found) and all(present),
        "C2_rf_numerados": len(set(re.findall(r"RF-\d{2}", text))),
        "C2_rnf_numerados": len(set(re.findall(r"RNF-\d{2}", text))),
        "C3_supuestos_marcados": text.count("SUPUESTO"),
        "C4_preguntas_clave": {k: (k in lower) for k in ("cancel", "decimal", "ip")},
        "C5_idempotencia": "idempoten" in lower,
        "C5_webhooks_duplicados_o_desorden": ("duplicad" in lower) or ("desorden" in lower) or ("fuera de orden" in lower),
        "C7_dado_cuando_entonces": len(re.findall(r"\bdado\b.*?\bcuando\b.*?\bentonces\b", lower, flags=re.DOTALL)),
    }


def evaluate_outputs(key: str = "01") -> Path | None:
    lab = PROMPT_LABS[key]
    out_dir = LABS_DIR / lab.folder / lab.output_dir
    files = sorted(out_dir.glob("*.md")) if out_dir.exists() else []
    files = [f for f in files if f.name != "README.md"]
    if not files:
        return None
    lines = ["# Resultados automáticos (generados por script)", "",
             "Solo cubren los criterios automáticos. La puntuación humana está en ../revision-humana.md.", ""]
    for f in files:
        lines.append(f"## {f.name}")
        for k, v in auto_evaluate(f.read_text(encoding="utf-8")).items():
            lines.append(f"- {k}: {v}")
        lines.append("")
    target = LABS_DIR / lab.folder / "evaluacion" / "resultados-automaticos.md"
    target.write_text("\n".join(lines), encoding="utf-8")
    return target


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Laboratorios de prompts (1 y 3)")
    sub = parser.add_subparsers(dest="cmd", required=True)
    run = sub.add_parser("ejecutar")
    run.add_argument("lab", choices=sorted(PROMPT_LABS))
    run.add_argument("--provider", default="anthropic", choices=["anthropic", "vertex", "bedrock"])
    ev = sub.add_parser("evaluar")
    ev.add_argument("lab", choices=["01"])
    args = parser.parse_args(argv)

    settings = Settings.from_env()
    if args.cmd == "evaluar":
        target = evaluate_outputs(args.lab)
        print(target or "No hay salidas que evaluar todavía (ejecuta primero el laboratorio en modo LIVE).")
        return 0 if target else 1
    status = provider_status(args.provider, settings)
    print(f"Proveedor: {status.label} | Modelo: {status.model} | Modo: {status.mode}", file=sys.stderr)
    try:
        for path in run_lab(args.lab, args.provider, settings):
            print(f"Guardado: {path.relative_to(REPO_ROOT)}")
    except ProviderUnavailable as exc:
        print(f"PENDIENTE — falta: {', '.join(exc.missing)}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
