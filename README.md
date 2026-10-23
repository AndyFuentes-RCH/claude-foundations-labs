# claude-foundations-labs

Portafolio práctico de **Andy Fuentes** con siete laboratorios que aplican lo aprendido en los cursos de
Anthropic Academy, sobre un caso común de **soporte de remesas** con datos **100 % sintéticos**.

> **Alcance honesto.** Son aplicaciones educativas propias inspiradas en los temas de los cursos. No son ejercicios
> oficiales de Anthropic ni evidencia de haber aprobado el examen *Claude Certified Architect*. Los certificados de
> finalización de los cursos están en [Evidencias_Claude_Andy_Fuentes/certificates/](Evidencias_Claude_Andy_Fuentes/certificates/).
> Ningún dato corresponde a clientes, operaciones financieras, socios ni empresas reales.

## Estado de los laboratorios
| # | Proyecto | Curso(s) | Estado | Qué falta |
|---|----------|----------|--------|-----------|
| 1 | [Colaboración efectiva: requisitos → especificación](labs/01-colaboracion-efectiva/) | AI Fluency · Claude 101 | Pendiente de credenciales o intervención | Ejecución LIVE + tu revisión humana |
| 2 | [Asistente de remesas con Claude API](labs/02-asistente-claude-api/) | Building with the Claude API | Validado localmente | Ejecución LIVE con API key |
| 3 | [Flujo de productividad](labs/03-flujo-productividad/) | Claude 101 · AI Fluency | Pendiente de credenciales o intervención | Tu práctica en Claude.ai + capturas |
| 4 | [Desarrollo con Claude Code: caché TTL](labs/04-claude-code/) | Claude Code in Action | Validado con Claude | — |
| 5 | [Claude en Google Cloud (Vertex AI)](labs/05-claude-google-cloud/) | Claude on Google Cloud | Pendiente de credenciales o intervención | Proyecto GCP, ADC y autorización de gasto |
| 6 | [Claude en Amazon Bedrock](labs/06-claude-amazon-bedrock/) | Claude with Amazon Bedrock | Pendiente de credenciales o intervención | Cuenta AWS, acceso al modelo y autorización de gasto |
| 7 | [Servidor MCP](labs/07-model-context-protocol/) | Introduction to Model Context Protocol | Validado localmente | Aprobar el servidor en Claude Code y probarlo |

Definición de estados: **Preparado** (código/materiales listos, sin ejecutar) · **Validado localmente** (pruebas y
ejecuciones locales sin Claude) · **Validado con Claude** (ejecución real con Claude registrada) · **Pendiente de
credenciales o intervención** (requiere algo que solo tú puedes aportar).

Más detalle: [mapa de cursos y evidencias](docs/course-map.md) · [limitaciones y pendientes](docs/limitations.md).

## Modos de ejecución
| Modo | Significado |
|------|-------------|
| **LIVE** | Llamada real a Claude (API, Vertex o Bedrock). Requiere credenciales **y** `CFL_ALLOW_LIVE_CALLS=true`. |
| **MOCK** | Ejecución local sin Claude: proveedor determinista de plantillas o cliente MCP local. Sus respuestas llevan la marca `[MOCK …]`. |
| **PENDIENTE** | Falta una credencial o autorización: no se hace ninguna llamada y no se genera contenido sustituto. |

## Instalación
Requisitos: Python 3.10+ (probado con 3.12.3), git.
```bash
git clone <url-del-repositorio> claude-foundations-labs && cd claude-foundations-labs
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"          # versiones fijadas en pyproject.toml
cp .env.example .env                        # opcional: credenciales y ajustes
```
Si `python3 -m venv` falla por falta de `ensurepip` (Debian/Ubuntu), instala `python3-venv`
(`sudo apt install python3.12-venv`) o crea el entorno con `python3 -m venv --without-pip .venv` y ejecuta
`get-pip.py` dentro de él. `requirements.lock.txt` contiene el entorno exacto usado en las pruebas.

## Uso rápido
```bash
.venv/bin/python -m pytest -q                                   # 115 pruebas, sin red ni credenciales
.venv/bin/uvicorn cfl.web.app:app --port 8000                   # interfaz: http://127.0.0.1:8000
.venv/bin/python -m cfl.assistant "¿Estado de RMX-2026-000104?" --provider mock
.venv/bin/python -m cfl.mcp_server.client                       # prueba del servidor MCP por stdio
```
Enlace de demostración: `http://127.0.0.1:8000/?lab=02&provider=mock&q=Estado%20de%20RMX-2026-000104&run=1`.

Para ejecutar con Claude (consumo facturable): define `ANTHROPIC_API_KEY` y `CFL_ALLOW_LIVE_CALLS=true` en `.env`
y usa `--provider anthropic` o elige "Claude API" en la interfaz.

## Estructura
```
src/cfl/
  domain/       Lógica de negocio: modelos, repositorio, caché TTL, políticas
  tools/        Herramientas de solo lectura y validación de argumentos
  providers/    Claude API · Vertex AI · Bedrock (Mantle) · Mock
  assistant/    Bucle de tool use con streaming (Proyecto 2)
  mcp_server/   Servidor y cliente MCP (Proyecto 7)
  evidence/     Registro de ejecuciones
  labs/         Catálogo de laboratorios y ejecutor de prompts (Proyectos 1 y 3)
  web/          FastAPI + interfaz
data/synthetic/ Transacciones y políticas sintéticas compartidas
labs/           Un directorio y README por proyecto
docs/           Arquitectura, mapa de cursos, demo, registro de uso, limitaciones, evidencias
tests/          Pruebas (pytest)
```
Arquitectura detallada: [docs/architecture.md](docs/architecture.md). Instrucciones para Claude Code: [CLAUDE.md](CLAUDE.md).

## Evidencia
- [docs/evidence/README.md](docs/evidence/README.md): índice de evidencias y registro de cada ejecución.
- [docs/claude-usage-log.md](docs/claude-usage-log.md): uso real de Claude y sus herramientas para construir este repositorio.
- [docs/demo-script.md](docs/demo-script.md): guion de demostración de 5 a 8 minutos.

## Seguridad
- `.env` y credenciales están en `.gitignore`; el registro de evidencia nunca guarda claves.
- Las herramientas son de solo lectura; el asistente no puede cancelar, reembolsar ni modificar datos.
- Ninguna llamada facturable ocurre sin credenciales **y** `CFL_ALLOW_LIVE_CALLS=true`.
