# Documento de requisitos (PRD) — Notificaciones proactivas de estado de remesas

> Documento **sintético** para la práctica del Proyecto 3. Empresa, personas, fechas y cifras son ficticias.

| Campo | Valor |
|-------|-------|
| Producto | App de envíos "RemesaFácil" (ficticia) |
| Versión | 0.3 — borrador |
| Responsable de producto | Persona A (Producto) |
| Fecha | 2026-10-20 |

## 1. Problema
El 38% de los contactos a soporte del último trimestre (dato sintético) fueron preguntas "¿dónde está mi envío?".
Los clientes no reciben avisos cuando una remesa cambia de estado, en especial cuando queda **retenida** (ON_HOLD) o
**fallida** (FAILED), y se enteran días después al llamar.

## 2. Objetivo
Reducir en 25% los contactos "¿dónde está mi envío?" en los 90 días posteriores al lanzamiento, enviando
notificaciones proactivas y claras en cada cambio de estado relevante.

## 3. Alcance
**Incluido**
- Notificaciones push y correo electrónico para: fondeo confirmado, en tránsito, disponible para retiro, pagado,
  retenido, fallido y reembolsado.
- Mensajes con acción sugerida cuando el cliente debe hacer algo (p. ej., corregir el nombre del beneficiario).
- Preferencias del cliente para activar o desactivar cada canal.

**Fuera de alcance**
- SMS (se evaluará en una fase posterior por costo).
- Notificaciones al beneficiario.
- Cambios en el flujo de cumplimiento.

## 4. Requisitos funcionales
- RF-1: Enviar notificación en menos de 2 minutos tras el cambio de estado.
- RF-2: No enviar duplicados si el socio pagador reporta el mismo estado dos veces.
- RF-3: Para ON_HOLD por cumplimiento, el texto **no** debe revelar el motivo interno; solo indicar que está en revisión.
- RF-4: Para ON_HOLD por nombre no coincidente, incluir enlace directo a "Corregir beneficiario".
- RF-5: Plantillas en español e inglés.
- RF-6: Registrar cada notificación enviada para auditoría (12 meses).

## 5. Requisitos no funcionales
- Disponibilidad del servicio de notificaciones: 99.9% mensual.
- No incluir montos completos ni datos del beneficiario en notificaciones push (pantalla bloqueada).
- Cumplir preferencias de privacidad y baja de correo.

## 6. Dependencias y riesgos
- Depende del nuevo webhook del socio pagador (equipo de Integraciones, fecha comprometida 2026-11-15).
- Riesgo: el proveedor de correo actual tiene límite de 10.000 envíos/hora; el pico estimado es 14.000/hora en quincena.
- Riesgo: Legal no ha aprobado los textos de ON_HOLD.
- Dependencia: equipo de App debe exponer el centro de preferencias (sin fecha).

## 7. Hitos propuestos
| Hito | Fecha objetivo | Responsable |
|------|----------------|-------------|
| Textos aprobados por Legal | 2026-11-08 | Persona B (Legal) |
| Webhook del socio disponible | 2026-11-15 | Persona C (Integraciones) |
| Piloto con 5% de clientes | 2026-12-01 | Persona D (Ingeniería) |
| Lanzamiento general | 2026-12-15 | Persona A (Producto) |

## 8. Preguntas abiertas
- ¿Quién paga el aumento de plan del proveedor de correo?
- ¿Se notifica el estado "en tránsito" o solo genera ruido?
- ¿Cómo medimos la reducción de contactos si soporte no etiqueta los motivos de forma consistente?
