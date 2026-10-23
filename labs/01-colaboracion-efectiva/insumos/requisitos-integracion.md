# Notas de requisitos — Integración con "Pagador Sintético Andino"

> Documento **sintético** para fines educativos. La empresa, el socio pagador, las personas y los sistemas son ficticios.
> Está redactado a propósito como notas desordenadas de una reunión, igual que suelen llegar en la vida real.

**Reunión de arranque — 14/10/2026.** Asistentes: Producto (P), Operaciones (O), Cumplimiento (C), Ingeniería (I).

- P: queremos habilitar depósito bancario a Colombia y Perú con el Pagador Sintético Andino (PSA) antes de fin de trimestre. Hoy solo tenemos efectivo con otro socio.
- I: PSA expone una API REST con OAuth2 client credentials. El token dura 3600 s. Tienen sandbox, pero los datos del sandbox se reinician cada noche.
- I: para crear un pago hay que enviar: referencia nuestra, monto en moneda destino, banco, tipo y número de cuenta, nombre del beneficiario y tipo/número de documento.
- O: el año pasado tuvimos pagos duplicados con otro socio porque reintentamos tras un timeout. **No puede volver a pasar.** PSA dice que acepta un header `Idempotency-Key` válido por 24 h.
- I: PSA notifica cambios de estado por webhook (firmado con HMAC-SHA256) y también tiene un endpoint para consultar estado. Los webhooks a veces llegan desordenados o repetidos.
- C: antes de enviar a PSA, toda orden debe haber pasado screening de listas restrictivas en nuestro sistema. Si PSA devuelve "COMPLIANCE_HOLD" tenemos que reflejarlo como ON_HOLD y no reintentar.
- P: la cotización de tipo de cambio que mostramos al cliente vale 30 minutos. Si se vence antes de fondear, hay que recotizar.
- O: necesitamos saber cuándo un pago lleva más de 24 h en tránsito para avisar a soporte. Hoy nos enteramos cuando el cliente llama.
- I: límite de PSA: 50 solicitudes por segundo; responden 429 con `Retry-After`.
- C: no podemos guardar el número de documento del beneficiario en logs. Retención de datos: 5 años en la base transaccional, cifrado en reposo.
- P: ¿podemos cancelar un pago ya enviado? PSA dijo "depende del banco"; nadie lo confirmó.
- O: los rechazos de PSA traen códigos propios (R01 cuenta inexistente, R02 nombre no coincide, R03 banco no disponible...). Queremos mostrarlos en español a soporte.
- I: ambiente productivo de PSA requiere IPs en lista blanca. Nuestra salida actual usa IPs dinámicas.
- P: métrica de éxito: 95% de pagos acreditados en menos de 2 horas hábiles.
- Pendiente: nadie sabe si PSA soporta montos con decimales para COP.
