# Proyecto 7 · Servidor MCP de remesas sintéticas

**Curso relacionado:** Introduction to Model Context Protocol
**Estado:** Validado localmente — servidor probado con el cliente oficial (en memoria y por stdio).
La conexión con Claude está preparada pero **no se ha registrado aún una ejecución conectada a Claude**.

## Capacidades del servidor ([src/cfl/mcp_server/server.py](../../src/cfl/mcp_server/server.py))
| Tipo | Nombre | Descripción |
|------|--------|-------------|
| Herramienta | `get_transaction_status(transaction_id)` | Solo lectura (`readOnlyHint=true`, `destructiveHint=false`). Reutiliza el Toolbox del Proyecto 2 |
| Recurso | `policies://soporte-remesas` | Políticas sintéticas en Markdown |
| Prompt | `investigar_incidente(transaction_id, sintoma)` | Guía de investigación: hechos verificados vs. hipótesis, comunicación y escalamiento |

SDK: `mcp==2.3.0` (API v2: `MCPServer`, `Client`, `ToolError`).

## Validación de entradas y errores
| Caso | Resultado MCP |
|------|---------------|
| ID existente | `structuredContent` con `found=true` y el registro |
| ID inexistente | `found=false` con mensaje; **no** es error y no se inventan datos |
| Formato inválido (`RMX-12`, inyecciones) | `isError=true` con `INVALID_ARGUMENT` y el formato esperado |
| Tipo inválido o argumento faltante | `isError=true` (validación del esquema) |
| Fallo interno | `isError=true` genérico; el detalle queda en el log del servidor, no llega al modelo |

## 1. Pruebas del cliente local (sin Claude)
```bash
.venv/bin/python -m pytest -q tests/test_mcp.py        # 12 pruebas: memoria + subproceso stdio
.venv/bin/python -m cfl.mcp_server.client               # cliente por stdio; registra en runs.jsonl como MOCK
```
Estas ejecuciones se registran con `mode = MOCK` y `provider = cliente MCP local … — sin Claude`.
**No demuestran** una integración con Claude: solo que el servidor cumple el protocolo.

## 2. Conexión real con Claude (transporte stdio)

### Opción A — Claude Code (recomendada)
El repositorio incluye [.mcp.json](../../.mcp.json) (alcance de proyecto). Desde la raíz del repositorio:
```bash
claude                      # Claude Code pedirá aprobar el servidor "remesas-sinteticas" del .mcp.json
# dentro de Claude Code:
/mcp                        # verifica que remesas-sinteticas aparece como conectado
```
Equivalente por CLI: `claude mcp add --scope project remesas-sinteticas -- .venv/bin/python -m cfl.mcp_server.server`.
Prueba sugerida: *"Usa el prompt investigar_incidente para RMX-2026-000111 y lee el recurso de políticas."*
También: *"¿Cuál es el estado de RMX-2026-999999?"* (debe decir que no existe).

### Opción B — Claude Desktop
En `claude_desktop_config.json` (Configuración → Desarrollador → Editar configuración):
```json
{
  "mcpServers": {
    "remesas-sinteticas": {
      "command": "/RUTA/ABSOLUTA/AL/REPO/.venv/bin/python",
      "args": ["-m", "cfl.mcp_server.server"],
      "cwd": "/RUTA/ABSOLUTA/AL/REPO"
    }
  }
}
```
Reinicia Claude Desktop y verifica el icono de herramientas.

### Opción C — Streamable HTTP
```bash
.venv/bin/python -m cfl.mcp_server.server --transport streamable-http --port 8765   # http://127.0.0.1:8765/mcp
```
Útil con clientes que hablan HTTP. Para el conector MCP de la Claude API el servidor tendría que ser accesible
públicamente por HTTPS (con autenticación): **no lo expongas** con datos reales; aquí no se ha hecho.

## Cómo registrar la evidencia conectada a Claude
Cuando hagas la prueba en Claude Code o Claude Desktop, añade una entrada manual en
[docs/evidence/README.md](../../docs/evidence/README.md) con fecha, cliente, modelo y resultado. Solo entonces el estado
puede pasar a "Validado con Claude".

## Pendiente
- [ ] Ejecutar la conexión real con Claude Code o Claude Desktop.
