# Criterios de evaluación — Proyecto 1

Cada respuesta (prompt inicial y prompt mejorado) se evalúa con los mismos criterios. Los **automáticos** los calcula
`python -m cfl.labs.prompt_lab evaluar 01` sobre las salidas guardadas; los **humanos** los completa Andy Fuentes en
[revision-humana.md](../revision-humana.md). Ninguna puntuación humana se rellena automáticamente.

| # | Criterio | Tipo | Cómo se verifica | Peso |
|---|----------|------|------------------|------|
| C1 | Contiene las 9 secciones pedidas, en orden | Automático | Búsqueda de encabezados | 10 |
| C2 | Requisitos numerados (RF-xx / RNF-xx) | Automático | Expresión regular | 10 |
| C3 | Incluye sección de supuestos marcados como SUPUESTO | Automático | Búsqueda de texto | 5 |
| C4 | Incluye preguntas abiertas (cancelación, decimales COP, IPs) | Automático (parcial) + humano | Palabras clave + lectura | 15 |
| C5 | Cubre idempotencia y duplicados de webhooks | Automático (palabras clave) + humano | Palabras clave + lectura | 15 |
| C6 | No inventa datos ausentes en las notas (endpoints, límites, plazos) | **Humano** | Contraste línea a línea con las notas | 20 |
| C7 | Criterios de aceptación verificables (Dado/Cuando/Entonces) | Automático (formato) + humano (calidad) | Regex + lectura | 10 |
| C8 | Utilidad para estimar: un ingeniero podría planificar con este documento | **Humano** | Juicio experto | 15 |

Escala humana por criterio: 0 = no cumple, 1 = parcial, 2 = cumple. Puntuación ponderada = Σ(peso × nota/2).

## Hipótesis que se quiere contrastar
El prompt mejorado (rol, audiencia, estructura, reglas anti-invención y delimitadores XML) debería mejorar C1–C7 frente al
prompt inicial. El resultado **no se da por supuesto**: se registra lo que efectivamente produzca el modelo.
