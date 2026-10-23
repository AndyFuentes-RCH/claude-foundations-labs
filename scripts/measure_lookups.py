"""Mide lecturas al origen de datos y latencia del asistente (línea base / comparación del Proyecto 4).

    python scripts/measure_lookups.py --latency-ms 150
Usa el proveedor MOCK: no llama a Claude y no genera consumo.
"""

from __future__ import annotations

import argparse
import time

from cfl.assistant import SupportAssistant
from cfl.config import Settings
from cfl.providers.mock import MockProvider
from cfl.tools import build_default_toolbox

QUERIES = [
    "historial de RMX-2026-000104",          # status + history del mismo ID en una consulta
    "¿Cuál es el estado de RMX-2026-000104?",  # el agente vuelve a preguntar por el mismo ID
    "¿Cuál es el estado de RMX-2026-000104?",
    "Estado de RMX-2026-999999",              # inexistente
    "Estado de RMX-2026-999999",
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--latency-ms", type=int, default=150)
    args = parser.parse_args()
    settings = Settings.from_env(env={"CFL_SIMULATED_LATENCY_MS": str(args.latency_ms)})
    toolbox = build_default_toolbox(settings)
    repo = toolbox.repository
    inner = getattr(repo, "inner", repo)  # repositorio de origen (si hay caché, está envuelto)
    print(f"Repositorio: {type(repo).__name__} | latencia simulada: {args.latency_ms} ms")
    total = 0.0
    for q in QUERIES:
        before = inner.lookups
        t0 = time.perf_counter()
        SupportAssistant(MockProvider(), toolbox).run(q)
        elapsed = (time.perf_counter() - t0) * 1000
        total += elapsed
        print(f"- {q!r}: lecturas al origen={inner.lookups - before}, tiempo={elapsed:.0f} ms")
    print(f"TOTAL lecturas al origen={inner.lookups}, tiempo total={total:.0f} ms")
    stats = getattr(repo, "stats", None)
    if callable(stats):
        print(f"Métricas de caché: {stats()}")


if __name__ == "__main__":
    main()
