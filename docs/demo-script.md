# Guion de demostración (≈7 minutos)

**Preparación (antes de grabar):** `.venv/bin/uvicorn cfl.web.app:app --port 8000` en una terminal; navegador en
`http://127.0.0.1:8000`; otra terminal en la raíz del repositorio. Si ya tienes API key autorizada, ten `.env` listo;
si no, la demo funciona en MOCK y muestra los PENDIENTES con honestidad.

| Tiempo | Qué mostrar | Qué decir |
|--------|-------------|-----------|
| 0:00–0:40 | README: tabla de estados y aviso de alcance | "Siete laboratorios sobre soporte de remesas con datos sintéticos. Cada uno declara su estado real: lo que está validado con Claude, lo validado localmente y lo pendiente." |
| 0:40–1:30 | `docs/architecture.md` (diagrama) | "Separé dominio, herramientas, proveedores y orquestación. Las mismas herramientas sirven al asistente y al servidor MCP; un solo adaptador cubre Claude API, Vertex y Bedrock." |
| 1:30–3:00 | Interfaz → Proyecto 02, MOCK: `RMX-2026-000104`, luego `RMX-2026-999999`, luego `RMX-12` | "Ved el modo de ejecución, el proveedor y el modelo arriba. El asistente llama herramientas de solo lectura, consulta la política aplicable y, cuando la transacción no existe, lo dice sin inventar. El ID inválido se rechaza con un error de validación." Si hay API key: repetir con *Claude API* (LIVE) y señalar request-id y tokens al pie. |
| 3:00–3:30 | Proveedor *Claude API* sin credenciales | "Sin credenciales o sin autorización de gasto, el modo es PENDIENTE y no se hace ninguna llamada." |
| 3:30–4:45 | Terminal: `git log --oneline`, `labs/04-claude-code/ISSUE.md`, `python scripts/measure_lookups.py --latency-ms 150`; interfaz → Proyecto 04 dos veces | "Con Claude Code registré el problema y la línea base antes de tocar código; después implementé la caché TTL con pruebas. Lecturas al origen: de 6 a 2. Al pie se ven los aciertos de caché." |
| 4:45–5:45 | Interfaz → Proyecto 07 con `RMX-2026-000104` y `RMX-12`; terminal `python -m cfl.mcp_server.client` | "Servidor MCP con una herramienta, un recurso y un prompt. Esto es el cliente local: no interviene Claude." Si ya lo conectaste: mostrar `/mcp` en Claude Code y una consulta real. |
| 5:45–6:30 | Proyectos 05 y 06 en la interfaz; README de Bedrock (política IAM) | "Los adaptadores de Vertex y Bedrock están implementados y probados sin red; no hay despliegue en la nube ni consumo. Documenté permisos mínimos y pasos para la validación en vivo." |
| 6:30–7:00 | `.venv/bin/python -m pytest -q` y `docs/evidence/README.md` | "115 pruebas. Cada ejecución queda registrada con fecha, modelo, herramientas, request-id y tokens; lo que no existe se registra como null." |

**Cierre (una frase):** "El objetivo no es solo que funcione, sino que cada afirmación del portafolio sea verificable."
