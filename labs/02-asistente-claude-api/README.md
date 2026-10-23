# Proyecto 2 · Asistente de remesas con la Claude API

**Curso relacionado:** Building with the Claude API
**Estado:** Validado localmente — probado con pytest y en modo MOCK. La ejecución LIVE contra Claude queda pendiente de API key.

## Qué hace
Un asistente para agentes de soporte que consulta el estado de remesas **sintéticas** con herramientas de solo lectura y
responde únicamente con lo que encontró en los registros.

## Requisitos cubiertos
| Requisito | Implementación | Prueba |
|-----------|----------------|--------|
| Streaming | `MessagesAPIProvider.stream_turn` usa `client.messages.stream(...)` y emite cada delta de texto; la web lo reenvía por SSE | `test_stream_turn_normalizes_result`, `test_assistant_stream_mock` |
| Tool use | Bucle manual en `assistant/agent.py`; todos los `tool_result` de un turno vuelven en **un** mensaje `user` | `test_tool_loop_and_grounded_answer`, `test_parallel_tool_calls_return_in_single_message` |
| Validación de argumentos | pydantic con `extra="forbid"` y formato `RMX-AAAA-NNNNNN`; errores como `tool_result` con `is_error: true` | `test_invalid_arguments`, `test_invalid_argument_marks_is_error` |
| Límite de iteraciones | `CFL_MAX_TOOL_ITERATIONS` (5 por defecto) | `test_iteration_limit` |
| Manejo de errores | Mapeo de excepciones del SDK (401/403/404/429/5xx/conexión), `refusal`, `max_tokens` con herramienta truncada, JSON de herramienta no parseable (reintento acotado), errores internos sin filtrar detalles | `test_map_status_errors`, `test_refusal_stops`, `test_truncated_tool_call_is_not_executed`, `test_invalid_tool_json_is_retried`, `test_unexpected_error_is_contained` |
| Respuestas fundamentadas | Prompt de sistema + verificación posterior: todo ID mencionado debe provenir de una herramienta; si no, se emite advertencia | `test_ungrounded_ids_are_flagged` |
| Transacción inexistente | La herramienta devuelve `found=false` (no es error) y el prompt exige no suponer datos | `test_status_not_found_is_not_an_error`, `test_mock_not_found_does_not_invent` |

## Herramientas (solo lectura)
- `get_transaction_status(transaction_id)` — estado, detalle, montos, motivo de retención, disponibilidad estimada.
- `get_transaction_history(transaction_id)` — eventos cronológicos.
- `get_support_policy(topic)` — política sintética por tema (`privacidad`, `retenciones`, `retrasos`, `cancelaciones`, `fallidas`, `escalamiento`).

## Configuración del modelo (verificada con la documentación oficial vigente)
- Modelo por defecto `claude-opus-5-5` (`CFL_ANTHROPIC_MODEL`). SDK `anthropic==2.2.0`.
- Profundidad con `output_config.effort` (`CFL_EFFORT`, por defecto `medium`). No se envía `temperature` ni `thinking` deshabilitado: ambos se rechazan en este modelo / versión de API.
- `eager_input_streaming: true` en las herramientas; por eso el cliente valida siempre los argumentos.
- **Fallback de servidor** ante rechazos de seguridad: `fallbacks="default"` con la beta `server-side-fallback-2026-07-01` (solo Claude API; desactivable con `CFL_ENABLE_SERVER_FALLBACKS=false`).

## Ejecutar
```bash
# MOCK (sin credenciales, sin consumo; respuestas de plantilla marcadas como MOCK)
.venv/bin/python -m cfl.assistant "¿Cuál es el estado de RMX-2026-000104?" --provider mock

# LIVE (requiere tu API key y autorización de consumo)
export ANTHROPIC_API_KEY=... CFL_ALLOW_LIVE_CALLS=true
.venv/bin/python -m cfl.assistant "¿Cuál es el estado de RMX-2026-000104?" --provider anthropic
```
Cada ejecución se registra en `docs/evidence/runs/runs.jsonl` con request-id y tokens cuando existen (`null` en MOCK).

## Casos de demostración
| Consulta | Comportamiento esperado |
|----------|-------------------------|
| `RMX-2026-000104` | ON_HOLD por cumplimiento → consulta política `retenciones`, no revela criterios internos |
| `RMX-2026-000111` | ON_HOLD por nombre no coincidente → indica corrección del beneficiario |
| `historial de RMX-2026-000108` | Usa la herramienta de historial |
| `RMX-2026-999999` | Dice que no existe y no inventa datos |
| `RMX-12` | Explica el formato válido |

## Pendiente
- [ ] Ejecución LIVE con `ANTHROPIC_API_KEY` (registrará request-id y tokens reales).
