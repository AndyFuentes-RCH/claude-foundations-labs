# ISSUE P4-001 — Consultas repetidas de transacciones golpean el origen de datos en cada llamada

| Campo | Valor |
|-------|-------|
| Registrado | 2026-10-23, **antes** de modificar el código |
| Registrado por | Claude Code (sesión de esta mejora), a solicitud de Andy Fuentes |
| Estado del código al registrar | commit `988f96d` (sin caché) |
| Componente | `src/cfl/domain/repository.py` · `src/cfl/tools/toolbox.py` (Proyecto 2) |

## Problema
`JsonTransactionRepository.get()` relee el origen de datos en **cada** llamada. En el asistente del Proyecto 2 eso
significa que:

1. Una misma pregunta suele invocar `get_transaction_status` y `get_transaction_history` sobre el **mismo ID**: 2 lecturas.
2. En una conversación, el agente de soporte vuelve a preguntar por la misma remesa varias veces en pocos minutos.
3. Las búsquedas de IDs inexistentes (errores de tipeo frecuentes) también llegan siempre al origen.

En un sistema real el repositorio sería una llamada al "core de remesas" con latencia y límite de tasa, por lo que este
patrón multiplica latencia y carga sin aportar información nueva.

## Evidencia (línea base medida, no estimada)
Medición con `python scripts/measure_lookups.py --latency-ms 150` (proveedor MOCK, sin Claude), guardada en
[docs/evidence/test-runs/p4-linea-base-antes-de-cache.txt](../../docs/evidence/test-runs/p4-linea-base-antes-de-cache.txt):

```
- 'historial de RMX-2026-000104': lecturas al origen=2, tiempo=303 ms
- '¿Cuál es el estado de RMX-2026-000104?': lecturas al origen=1, tiempo=151 ms
- '¿Cuál es el estado de RMX-2026-000104?': lecturas al origen=1, tiempo=151 ms
- 'Estado de RMX-2026-999999': lecturas al origen=1, tiempo=151 ms
- 'Estado de RMX-2026-999999': lecturas al origen=1, tiempo=151 ms
TOTAL lecturas al origen=6, tiempo total=908 ms
```

## Comportamiento esperado
1. **Caché en memoria con TTL** delante del repositorio (patrón decorador), sin cambiar la interfaz `get()`.
2. **Clave normalizada**: `rmx-2026-000104` y `RMX-2026-000104` comparten entrada. IDs con formato inválido siguen
   lanzando `InvalidTransactionIdError` y **no** se cachean ni llegan al origen.
3. **TTL configurable** con `CFL_CACHE_TTL_SECONDS` (por defecto 30 s). `0` desactiva la caché.
4. **Caché negativa** para "no encontrada" con TTL propio y más corto (`CFL_CACHE_NEGATIVE_TTL_SECONDS`, por defecto 10 s),
   para que una transacción recién creada aparezca pronto.
5. Los **errores del origen no se cachean**.
6. **Tamaño máximo** (`CFL_CACHE_MAX_ENTRIES`, por defecto 1000) con expulsión de la entrada más antigua.
7. **Seguro con hilos** (la interfaz web atiende peticiones concurrentes).
8. **Métricas** `hits`, `misses`, `expired`, `size` visibles en la interfaz web del Proyecto 4.
9. **Invalidación** explícita por ID y total.
10. Reloj inyectable para probar la expiración sin `sleep`.

## Criterios de aceptación
- Con TTL > 0, repetir el escenario de la línea base produce **2 lecturas al origen** (una por ID distinto) en lugar de 6.
- Con `CFL_CACHE_TTL_SECONDS=0` el comportamiento es idéntico al actual.
- Tras expirar el TTL, la siguiente consulta vuelve al origen.
- La suite de pruebas existente sigue pasando sin cambios en las pruebas del Proyecto 2.

## Riesgo aceptado
Durante el TTL, un cambio de estado en el origen puede tardar hasta 30 s en verse. Es aceptable para un asistente de
consulta de soporte; no lo sería para decisiones de pago. Documentarlo en el README del laboratorio.
