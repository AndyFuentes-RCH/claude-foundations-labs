# Prompts listos para Claude.ai (Proyecto 3)

Úsalos en **una sola conversación nueva** en [claude.ai](https://claude.ai). Antes del primer mensaje, adjunta el archivo
`labs/03-flujo-productividad/insumos/documento-requisitos.md` con el botón de adjuntar (clip).
Sigue la [guía de capturas](../guia-capturas.md) para documentar cada paso.

---

## Paso 1 — Resumen ejecutivo
```
Te adjunto un documento de requisitos (PRD) sintético de un producto ficticio de remesas.

Escribe un resumen ejecutivo para la dirección (máximo 180 palabras) con:
- El problema y el objetivo medible.
- Qué se entrega y qué queda fuera.
- Los 3 riesgos principales y su impacto en la fecha de lanzamiento.
- Una decisión que la dirección necesita tomar.

Usa solo información del documento adjunto. Si algo no está en el documento, no lo supongas; dilo como pregunta abierta.
```

## Paso 2 — Tabla de acciones
```
Con base en el mismo documento, crea una tabla de acciones en Markdown con las columnas:
| # | Acción | Responsable (según el documento) | Fecha límite | Dependencia o bloqueo | Prioridad (Alta/Media/Baja) |

Reglas:
- Una fila por acción concreta que se desprenda de hitos, riesgos, dependencias o preguntas abiertas.
- Si el documento no indica responsable o fecha, escribe "Sin definir" (no inventes).
- Debajo de la tabla, en una línea, explica el criterio que usaste para asignar prioridad.
```

## Paso 3 — Correo borrador
```
Redacta un correo borrador de Persona A (Producto) para los responsables mencionados en el documento,
con el asunto, un saludo breve, el estado del proyecto en 3 viñetas, las acciones que se le piden a cada persona
con su fecha (según el documento) y una solicitud de confirmación.

Tono: profesional, cordial y directo. Máximo 200 palabras. Marca con [CONFIRMAR] cualquier dato que el documento no
defina. No lo envíes: es un borrador para revisión humana.
```
