Actúas como arquitecto de software en una empresa de remesas (ficticia). Necesito convertir las notas de una reunión
en una especificación técnica que el equipo de ingeniería usará para estimar y diseñar la integración con un nuevo
socio pagador. Todo el material es sintético.

<notas_reunion>
{{DOCUMENTO}}
</notas_reunion>

Audiencia: ingenieros backend y QA que no estuvieron en la reunión. Deben poder estimar a partir del documento.

Produce la especificación en Markdown con exactamente estas secciones, en este orden:
1. Resumen y alcance (incluye qué queda fuera de alcance).
2. Requisitos funcionales numerados (RF-01, RF-02...), cada uno trazable a una línea de las notas.
3. Requisitos no funcionales numerados (RNF-01...): seguridad, privacidad, rendimiento, disponibilidad, observabilidad.
4. Flujo de integración: creación de pago, idempotencia, webhooks (firma, duplicados, desorden), consulta de estado y reintentos.
5. Mapeo de estados y códigos de rechazo del socio a nuestros estados internos (tabla).
6. Manejo de errores y límites (429/Retry-After, timeouts, expiración de token y de cotización).
7. Supuestos: todo lo que asumas debe ir aquí, marcado como SUPUESTO.
8. Preguntas abiertas para el socio y para negocio, con responsable sugerido.
9. Criterios de aceptación verificables (formato Dado/Cuando/Entonces).

Reglas:
- No inventes valores que no estén en las notas (límites, plazos, endpoints, códigos). Si falta un dato, va a Preguntas abiertas.
- Señala explícitamente contradicciones o riesgos (por ejemplo, IPs dinámicas frente a lista blanca).
- No incluyas datos personales reales ni ejemplos con números de documento completos.
- Sé concreto y conciso: prefiere tablas y listas a párrafos largos.
