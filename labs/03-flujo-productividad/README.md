# Proyecto 3 · Flujo de productividad con Claude

**Cursos relacionados:** Claude 101 · AI Fluency: Framework & Foundations
**Estado:** Pendiente de credenciales o intervención — la práctica se realiza manualmente en Claude.ai.

## Objetivo
A partir de un documento sintético de requisitos, obtener con Claude: (1) un resumen ejecutivo, (2) una tabla de acciones
y (3) un correo borrador, revisando que no se inventen responsables ni fechas.

## Dos formas de ejecución — se registran por separado
| | Claude.ai (práctica principal) | Claude API (opcional) |
|---|---|---|
| Quién ejecuta | **Tú**, en el navegador | Script `cfl.labs.prompt_lab` |
| Contexto | Una conversación; el documento se adjunta una vez | Cada prompt es una llamada independiente con el documento incluido |
| Prompts | [prompts/claude-ai-listos-para-pegar.md](prompts/claude-ai-listos-para-pegar.md) | `prompts/01..03-*.md` |
| Evidencia | Capturas + texto copiado en `outputs-claude-ai/` | `outputs-api/` con request-id y tokens + `runs.jsonl` |
| Etiqueta | "Ejecución en Claude.ai" | "Ejecución por API" |

No mezcles ambas evidencias: una salida de la API no demuestra la práctica en Claude.ai, y viceversa.

## Pasos en Claude.ai
1. Abre una conversación nueva en claude.ai y adjunta [insumos/documento-requisitos.md](insumos/documento-requisitos.md).
2. Pega los prompts 1, 2 y 3 de [prompts/claude-ai-listos-para-pegar.md](prompts/claude-ai-listos-para-pegar.md), en orden.
3. Toma las capturas de la [guía de capturas](guia-capturas.md).
4. Copia cada respuesta tal cual en `outputs-claude-ai/` (`01-resumen.md`, `02-tabla.md`, `03-correo.md`) e indica arriba
   la fecha, el modelo que mostraba la interfaz y el enlace de la conversación si decides compartirla.
5. Revisa con los criterios de revisión de abajo y anota hallazgos en `outputs-claude-ai/revision.md`.

## Criterios de revisión (discernimiento)
- El resumen respeta el máximo de palabras y no añade datos ausentes.
- La tabla usa "Sin definir" donde el documento no da responsable o fecha (p. ej., centro de preferencias).
- El correo marca con [CONFIRMAR] lo que falta y no promete fechas que no existen.
- Los riesgos (límite de correo 10.000/h vs. pico 14.000/h; textos de Legal) aparecen y están bien priorizados.

## Ejecución por API (opcional)
```bash
export ANTHROPIC_API_KEY=... CFL_ALLOW_LIVE_CALLS=true
.venv/bin/python -m cfl.labs.prompt_lab ejecutar 03 --provider anthropic
```

## Alcance de esta entrega
Incluye documento sintético, prompts para Claude.ai y para la API, guía de capturas y criterios de revisión. Las salidas de Claude.ai y de la API no forman parte de esta entrega.
