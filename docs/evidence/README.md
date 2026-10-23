# Índice de evidencias

Reglas: solo evidencia real. Los campos no disponibles se registran como `null` o "no disponible". Ninguna entrada
contiene claves ni datos reales de clientes. Todas las ejecuciones de esta tabla son **MOCK (sin Claude)**: no hubo
credenciales para ejecuciones LIVE durante la sesión de construcción.

## 1. Registro automático de ejecuciones
Archivo: [runs/runs.jsonl](runs/runs.jsonl) — una línea JSON por ejecución con los campos `run_id`, `timestamp_utc`,
`project`, `mode`, `provider`, `model`, `input`, `output`, `tools_invoked`, `tests`, `request_ids`, `usage`,
`code_state` (`commit`, `dirty`) y `notes`.

| run_id | Fecha y hora (UTC) | Proyecto | Modo | Proveedor / herramienta | Entrada | Herramientas invocadas | request-id | Tokens | Código | Nota |
|--------|--------------------|----------|------|-------------------------|---------|------------------------|-----------|--------|--------|------|
| `870f8aba33ed` | 2026-10-23 17:46:43 | 02 | MOCK | mock (interfaz web) | ¿Estado de RMX-2026-000104…? | get_transaction_status, get_support_policy | no disponible | no disponible | `d8bfb2d` + cambios | Captura `app-02-mock-on-hold.png` |
| `601c1ebfb9f9` | 2026-10-23 17:46:43 | 02 | MOCK | mock (interfaz web) | ¿Qué pasó con RMX-2026-999999? | get_transaction_status (found=false) | no disponible | no disponible | `d8bfb2d` + cambios | Captura `app-02-mock-no-existe.png` |
| `fc10e4c41738` | 2026-10-23 17:46:44 | 04 | MOCK | mock (interfaz web) | historial de RMX-2026-000104 | status, history, policy | no disponible | no disponible | `d8bfb2d` + cambios | Captura `app-04-cache.png` (métricas de caché) |
| `59d4d8dc367e` | 2026-10-23 17:46:46 | 07 | MOCK | cliente MCP local en memoria, sin Claude | RMX-12 | get_transaction_status (is_error) | no aplica | no aplica | `d8bfb2d` + cambios | Captura `app-07-mcp-invalido.png` |
| `ae1f7d6e5f02` | 2026-10-23 17:47:12 | 02 | MOCK | mock (CLI) | RMX-2026-000111 | status, policy | no disponible | no disponible | `d8bfb2d` + cambios | **Defecto detectado**: el mock citó la regla de cumplimiento en vez de la de nombre no coincidente |
| `3bce0c0c0037` | 2026-10-23 17:47:13 | 02 | MOCK | mock (CLI) | ¿Qué pasó con RMX-2026-999999? | get_transaction_status | no disponible | no disponible | `d8bfb2d` + cambios | — |
| `2322e8669ce7` | 2026-10-23 17:47:15 | 07 | MOCK | cliente MCP local por stdio, sin Claude | 5 casos (válido, inexistente, inválidos) | get_transaction_status ×5 | no aplica | no aplica | `d8bfb2d` + cambios | Lista tool/resource/prompt |
| `37f5ba51dcbc` | 2026-10-23 17:47:37 | 02 | MOCK | mock (CLI) | RMX-2026-000111 | status, policy | no disponible | no disponible | `d8bfb2d` + cambios | Repetición tras corregir el defecto (cita la regla correcta) |

Intentos sin llamada (no generan entrada en `runs.jsonl`): `--provider anthropic` y `prompt_lab ejecutar 01` terminaron
en **PENDIENTE** por falta de `ANTHROPIC_API_KEY` y de `CFL_ALLOW_LIVE_CALLS=true`.

## 2. Pruebas ejecutadas
| Archivo | Contenido |
|---------|-----------|
| [test-runs/pytest-20261023T174743Z.txt](test-runs/pytest-20261023T174743Z.txt) | `pytest -v` completo: **115 passed**, con fecha, commit y versión de Python en la cabecera |
| [test-runs/p4-linea-base-antes-de-cache.txt](test-runs/p4-linea-base-antes-de-cache.txt) | Proyecto 4, línea base: 6 lecturas al origen, ~908 ms |
| [test-runs/p4-despues-de-cache.txt](test-runs/p4-despues-de-cache.txt) | Proyecto 4, con caché: 2 lecturas al origen, ~305 ms |
| [test-runs/p4-pytest-despues-de-cache.txt](test-runs/p4-pytest-despues-de-cache.txt) | Resumen de pytest tras implementar la caché (115 passed) |

Otras verificaciones ejecutadas en la sesión (salida en el registro de la conversación, no en archivo):
servidor MCP por Streamable HTTP (`RMX-2026-000102` → IN_TRANSIT; `RMX-2026-424242` → found=false) y
`claude mcp list` (servidor `remesas-sinteticas` detectado, *Pending approval*).

## 3. Capturas reales de la aplicación
Tomadas con Chrome headless el 2026-10-23 contra el servidor local (`docs/evidence/screenshots/app/`):

| Archivo | Muestra |
|---------|---------|
| `app-01-prompts.png` | Proyecto 01: materiales y modo PENDIENTE |
| `app-02-mock-on-hold.png` | Proyecto 02 en MOCK: ON_HOLD, política aplicada, herramientas |
| `app-02-mock-no-existe.png` | Proyecto 02 en MOCK: transacción inexistente sin inventar datos |
| `app-02-anthropic-pendiente.png` | Claude API en PENDIENTE: no se hizo llamada |
| `app-04-cache.png` | Proyecto 04: métricas de caché al pie |
| `app-05-vertex-pendiente.png` | Vertex AI en PENDIENTE con requisitos faltantes |
| `app-06-bedrock-pendiente.png` | Bedrock en PENDIENTE con requisitos faltantes |
| `app-07-mcp-invalido.png` | MCP local: entrada inválida → `is_error=true` |

## 4. Estado del código
Historial en `git log` (commits locales, sin push). Hitos: `91dacca` → `988f96d` → `e391b26` (ISSUE P4) → `d8bfb2d` (caché) →
commits posteriores de documentación y evidencia.

## 5. Evidencia manual (completar por Andy)
| Fecha y hora reales | Proyecto | Herramienta / proveedor | Modelo mostrado | Qué se hizo | Archivos |
|---------------------|----------|-------------------------|-----------------|-------------|----------|
| | | | | | |
