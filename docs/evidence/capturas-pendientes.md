# Capturas que debe tomar Andy

Las capturas de la interfaz web ya existen (tomadas automáticamente con Chrome headless, ver [README](README.md)).
Las siguientes requieren tu sesión, tu cuenta o tus credenciales. Antes de capturar, oculta correos, claves, IDs de
cuenta/proyecto y nombres de otras conversaciones.

| Proyecto | Momento exacto | Qué debe verse | Archivo |
|----------|----------------|----------------|---------|
| P1 | Tras `prompt_lab ejecutar 01` en LIVE | Terminal con "Modo: LIVE" y las rutas guardadas | `screenshots/p1/p1-01-ejecucion-live.png` |
| P1 | Tras completar la revisión | `revision-humana.md` con tus puntuaciones | `screenshots/p1/p1-02-revision-humana.png` |
| P2 | Interfaz, Proyecto 02, proveedor *Claude API* | Badge LIVE, respuesta, herramientas, request-id y tokens al pie | `screenshots/p2/p2-01-live-on-hold.png` |
| P2 | Igual, con `RMX-2026-999999` | Respuesta de Claude diciendo que no existe | `screenshots/p2/p2-02-live-no-existe.png` |
| P3 | Ver [guía de capturas del Proyecto 3](../../labs/03-flujo-productividad/guia-capturas.md) | Documento, prompts y resultados en Claude.ai | `screenshots/p3/…` |
| P4 | (Opcional) Ventana de Claude Code de esta sesión | Conversación con la implementación de la caché y la ejecución de pytest | `screenshots/p4/p4-01-sesion-claude-code.png` |
| P5 | Tras `--provider vertex` en LIVE | Terminal con la respuesta y la consola de GCP (Model Garden / métricas) sin datos sensibles | `screenshots/p5/p5-01-vertex-live.png` |
| P6 | Tras `--provider bedrock` en LIVE | Terminal con la respuesta y CloudWatch/CloudTrail mostrando la invocación | `screenshots/p6/p6-01-bedrock-live.png` |
| P7 | En Claude Code, tras aprobar el servidor | Salida de `/mcp` con `remesas-sinteticas` conectado | `screenshots/p7/p7-01-mcp-conectado.png` |
| P7 | En Claude Code | Claude invocando `get_transaction_status` (permiso de herramienta) y su respuesta | `screenshots/p7/p7-02-tool-call.png` |
| P7 | En Claude Code | Uso del prompt `investigar_incidente` o lectura del recurso de políticas | `screenshots/p7/p7-03-prompt-recurso.png` |

Después de cada captura, añade una fila en la tabla "Evidencia manual" de [README.md](README.md) con la fecha y hora reales.
