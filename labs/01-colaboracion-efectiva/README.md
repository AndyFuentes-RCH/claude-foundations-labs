# Proyecto 1 · Colaboración efectiva con Claude

**Cursos relacionados:** AI Fluency: Framework & Foundations · Claude 101
**Estado:** Pendiente de credenciales o intervención — materiales listos; falta la ejecución LIVE y tu revisión humana.

## Objetivo
Convertir notas desordenadas de una reunión sobre una integración fintech (sintética) en una especificación técnica,
comparando un prompt inicial con uno mejorado y aplicando revisión humana.

## Materiales
| Archivo | Contenido |
|---------|-----------|
| [insumos/requisitos-integracion.md](insumos/requisitos-integracion.md) | Notas sintéticas de la reunión (insumo) |
| [prompts/01-prompt-inicial.md](prompts/01-prompt-inicial.md) | Prompt ingenuo de una línea |
| [prompts/02-prompt-mejorado.md](prompts/02-prompt-mejorado.md) | Prompt con rol, audiencia, estructura, reglas y delimitadores |
| [evaluacion/criterios.md](evaluacion/criterios.md) | Rúbrica: criterios automáticos y humanos |
| [revision-humana.md](revision-humana.md) | Plantilla de revisión **para que la completes tú** |
| `outputs/` | Salidas reales de Claude con metadatos (se crean al ejecutar en LIVE) |

## Las 4D de AI Fluency aplicadas
| Competencia | Cómo se aplica en este laboratorio |
|-------------|-----------------------------------|
| **Delegación** | Se delega a Claude la estructuración y detección de huecos (tarea de síntesis donde aporta velocidad); se reservan para la persona las decisiones de alcance, la validación de datos con el socio y la aprobación final. |
| **Descripción** | El prompt mejorado describe el producto (especificación para estimar), el proceso (secciones y orden, trazabilidad RF→nota) y el comportamiento esperado (no inventar, señalar contradicciones, preguntar lo que falta). |
| **Discernimiento** | La rúbrica separa lo verificable por script (estructura, numeración, palabras clave) de lo que exige juicio (C6: ¿inventó datos?, C8: ¿sirve para estimar?). La revisión humana contrasta línea a línea con las notas. |
| **Diligencia** | Datos sintéticos; las salidas se guardan con fecha, modelo, request-id y tokens; nada se comparte como especificación final sin la revisión y correcciones registradas en `revision-humana.md`. |

## Cómo ejecutarlo
Requiere `ANTHROPIC_API_KEY` y autorizar el consumo (2 llamadas al modelo configurado).
```bash
export ANTHROPIC_API_KEY=...            # o en .env
export CFL_ALLOW_LIVE_CALLS=true
.venv/bin/python -m cfl.labs.prompt_lab ejecutar 01 --provider anthropic
.venv/bin/python -m cfl.labs.prompt_lab evaluar 01   # genera evaluacion/resultados-automaticos.md
```
Sin credenciales el comando termina en **PENDIENTE** y no genera contenido. Después, completa
[revision-humana.md](revision-humana.md).

## Pendiente
- [ ] Ejecutar en LIVE (requiere tu API key y autorización de consumo).
- [ ] Revisión humana de ambas salidas por Andy Fuentes.
- [ ] Capturas indicadas en [docs/evidence/capturas-pendientes.md](../../docs/evidence/capturas-pendientes.md).
