# CLAUDE.md — claude-foundations-labs

Guía para Claude Code en este repositorio. Todo el contenido de dominio es **sintético** (remesas ficticias).

## Comandos
```bash
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"   # instalación (ver README si falta ensurepip)
.venv/bin/python -m pytest -q                                   # suite completa (~2 s, sin red)
.venv/bin/python -m pytest -q tests/test_cache.py               # un módulo
.venv/bin/uvicorn cfl.web.app:app --reload --port 8000          # interfaz web
.venv/bin/python -m cfl.assistant "Estado de RMX-2026-000104" --provider mock   # asistente por CLI
.venv/bin/python -m cfl.mcp_server.client                       # cliente MCP de prueba (stdio)
.venv/bin/python -m cfl.labs.prompt_lab ejecutar 01 --provider anthropic        # Lab 1 (requiere LIVE)
.venv/bin/python scripts/measure_lookups.py --latency-ms 150    # métrica del Proyecto 4
```

## Arquitectura (no mezclar capas)
- `src/cfl/domain/` lógica de negocio: modelos, repositorio JSON, caché TTL, políticas. Sin dependencias de proveedores.
- `src/cfl/tools/` herramientas **de solo lectura** + validación (pydantic, `extra="forbid"`). Reutilizadas por el asistente y por MCP.
- `src/cfl/providers/` adaptadores de modelo. Claude API, Vertex y Bedrock comparten `MessagesAPIProvider`; el mock es determinista.
- `src/cfl/assistant/` bucle de tool use (streaming, límite de iteraciones, verificación de fundamentación).
- `src/cfl/mcp_server/` servidor MCP v2 (`MCPServer`) y cliente de prueba.
- `src/cfl/web/` FastAPI + `static/` (HTML/JS sin dependencias externas).
- `src/cfl/labs/catalog.py` es la **fuente única** del estado de cada laboratorio; si cambia un estado, actualiza también la tabla del README.

## Convenciones
- Código y comentarios en español; nombres de identificadores en inglés. Python ≥ 3.10, tipado con `from __future__ import annotations`.
- Modelos por defecto: `claude-opus-5-5` (API y Vertex), `anthropic.claude-opus-5-5` (Bedrock). No enviar `temperature`/`top_p`/`top_k` (la versión de API `2026-10-21` los rechaza) ni `thinking` disabled/`budget_tokens` (400 en Opus 5.5). Controlar profundidad con `output_config.effort`.
- `tool_choice` forzado (`any`/`tool`) da 400 en Opus 5.5: usar `auto` y guiar con el prompt.
- El parámetro `fallbacks` solo existe en la Claude API; no activarlo en Vertex ni Bedrock.
- Las herramientas nunca escriben datos. Una transacción inexistente devuelve `found=false` (no es error); un argumento inválido devuelve `is_error=true` / `ToolError`.
- Las pruebas no usan red ni credenciales. Para clientes reales, construir sin llamar (ver `tests/test_providers.py`).

## Seguridad y evidencia (obligatorio)
- Nunca hacer llamadas facturables sin `CFL_ALLOW_LIVE_CALLS=true` **y** autorización explícita de Andy.
- Nunca imprimir ni registrar claves. `.env` está en `.gitignore`.
- `docs/evidence/runs/runs.jsonl` solo recibe ejecuciones reales vía `EvidenceRecorder`; campos ausentes = `null`. No editar a mano ni inventar entradas.
- No crear salidas de Claude simuladas en `labs/*/outputs*`; esas carpetas solo guardan ejecuciones LIVE reales.
- No marcar un laboratorio como "Validado con Claude" sin evidencia real registrada.
