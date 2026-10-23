# Registro del uso real de Claude y sus herramientas

Este registro distingue **cómo se construyó el repositorio** (con Claude Code) de **lo que ejecuta la aplicación**
(llamadas a Claude desde el código, todas registradas en `docs/evidence/runs/runs.jsonl`).

## Sesión 1 — Construcción del repositorio con Claude Code

| Campo | Valor |
|-------|-------|
| Fecha | 2026-10-23 (UTC; primeras ejecuciones registradas 17:46 UTC) |
| Herramienta | **Claude Code**, extensión de VS Code (variable `CLAUDECODE` presente en el entorno) |
| Modelo | Claude Opus 5.5 (`claude-opus-5-5`, contexto 1M) |
| Usuario | Andy Fuentes (encargo inicial en un único mensaje; sin intervenciones intermedias) |
| Consumo de tokens de la sesión | no disponible (Claude Code no lo expone a la sesión) |
| Identificador de sesión | no disponible |

### Qué hizo Claude Code
1. Revisó el directorio (solo existían los certificados en `Evidencias_Claude_Andy_Fuentes/`, que se conservaron).
2. Detectó el entorno: Python 3.12.3, sin `ensurepip`; sin `ANTHROPIC_API_KEY`, sin credenciales de GCP ni AWS.
3. Consultó documentación oficial vigente (WebFetch): Claude en Amazon Bedrock (Mantle y legacy), Claude en Google Cloud,
   IAM de `bedrock-mantle`, guía del SDK de MCP v2; y la referencia de la Claude API incluida en Claude Code (*skill* `claude-api`).
4. Verificó las APIs instaladas por introspección (`AnthropicVertex`, `AnthropicBedrockMantle`, `MCPServer.run`, `ToolError`).
5. Escribió el código, las pruebas y la documentación; ejecutó pytest repetidamente (115 pruebas al final).
6. Ejecutó el asistente en MOCK, el cliente MCP por stdio y Streamable HTTP, y `claude mcp list` (detecta el servidor del
   proyecto como *Pending approval*; la aprobación se dejó a Andy).
7. Proyecto 4: midió la línea base, registró `ISSUE.md` y lo confirmó en git **antes** de implementar la caché.
8. Tomó capturas reales de la interfaz con Chrome headless y las revisó visualmente.
9. Encontró y corrigió un defecto propio del mock (citaba la regla de política equivocada para `RMX-2026-000111`);
   la ejecución defectuosa `ae1f7d6e5f02` se conserva en el registro y la corregida es `37f5ba51dcbc`.

### Commits producidos en la sesión (`Co-Authored-By: Claude Opus 5.5`)
| Commit | Contenido |
|--------|-----------|
| `91dacca` | Dominio sintético, herramientas, asistente, proveedores, evidencia, pruebas |
| `988f96d` | Servidor/cliente MCP, interfaz web, materiales de Labs 1 y 3 |
| `e391b26` | ISSUE P4-001 y línea base (antes del código de la caché) |
| `d8bfb2d` | Caché TTL, pruebas, CLAUDE.md |
| siguiente(s) | Documentación, evidencias, corrección del mock (ver `git log`) |

## Llamadas a Claude desde la aplicación
| Proveedor | Ejecuciones LIVE registradas |
|-----------|------------------------------|
| Claude API | 0 — sin API key en esta sesión |
| Vertex AI | 0 — sin proyecto ni credenciales GCP |
| Amazon Bedrock | 0 — sin cuenta ni credenciales AWS |

Todas las ejecuciones registradas hasta ahora son **MOCK** (sin Claude). Cuando ejecutes en LIVE, el registro capturará
automáticamente modelo, request-id y tokens.

## Prácticas pendientes de Andy (añadir aquí cuando ocurran)
| Fecha | Herramienta | Práctica | Evidencia |
|-------|-------------|----------|-----------|
| _pendiente_ | Claude.ai | Proyecto 3 | guía de capturas del Proyecto 3 |
| _pendiente_ | Claude Code | Proyecto 7, conexión MCP real | entrada manual en `docs/evidence/README.md` |
| _pendiente_ | Claude API | Proyectos 1 y 2 en LIVE | `runs.jsonl` + `labs/01-*/outputs/` |
