# Proyecto 4 · Desarrollo con Claude Code — caché con TTL

**Curso relacionado:** Claude Code in Action
**Estado:** Validado con Claude — la mejora se realizó en una sesión real de **Claude Code** (extensión de VS Code,
modelo Claude Opus 5.5) y se validó con pruebas locales. Ver [registro de uso](../../docs/claude-usage-log.md).

## Flujo seguido (verificable en `git log`)
| Paso | Qué se hizo | Evidencia |
|------|-------------|-----------|
| 1. Estado inicial | Asistente del Proyecto 2 sin caché | commit `988f96d` |
| 2. Medir | Línea base con latencia simulada de 150 ms | [p4-linea-base-antes-de-cache.txt](../../docs/evidence/test-runs/p4-linea-base-antes-de-cache.txt) |
| 3. Registrar el problema **antes** de tocar código | [ISSUE.md](ISSUE.md): problema, comportamiento esperado, criterios de aceptación | commit `e391b26` |
| 4. Implementar | `TTLCachedRepository` (decorador), configuración por entorno, integración en el Toolbox | commit de la mejora (ver `git log`) |
| 5. Probar | 14 pruebas nuevas en `tests/test_cache.py`; las pruebas del Proyecto 2 no se modificaron | [docs/evidence/test-runs/](../../docs/evidence/test-runs/) |
| 6. Medir de nuevo | Mismo escenario con caché | [p4-despues-de-cache.txt](../../docs/evidence/test-runs/p4-despues-de-cache.txt) |

## Resultado medido
| Métrica (5 consultas, 2 IDs distintos, latencia simulada 150 ms) | Antes | Después |
|---|---|---|
| Lecturas al origen de datos | 6 | 2 |
| Tiempo total (proveedor MOCK) | ~908 ms | ~305 ms |
| Aciertos de caché | — | 4 de 6 consultas |

Los tiempos dependen de la máquina; las lecturas al origen son deterministas y están cubiertas por
`test_acceptance_baseline_scenario_goes_from_6_to_2_lookups`.

## Cambios
- **Nuevo** `src/cfl/domain/cache.py`: `TTLCachedRepository` con TTL, caché negativa con TTL propio, límite de tamaño
  (expulsa la entrada más antigua), lock para concurrencia, invalidación y métricas (`hits`, `misses`, `expired`, `evicted`, `size`).
- `src/cfl/config.py`: `CFL_CACHE_TTL_SECONDS` (30), `CFL_CACHE_NEGATIVE_TTL_SECONDS` (10), `CFL_CACHE_MAX_ENTRIES` (1000).
- `src/cfl/tools/toolbox.py`: `build_default_toolbox` envuelve el repositorio cuando el TTL es > 0.
- La interfaz web muestra las métricas de caché al pie de cada ejecución del Proyecto 4.
- `CLAUDE.md` en la raíz con comandos reales, arquitectura, convenciones y reglas de seguridad/evidencia.

## Decisiones
- **Decorador** en vez de modificar el repositorio: el origen sigue siendo simple y la caché es opcional y probable por separado.
- **IDs inválidos** se validan antes de la caché: no ocupan memoria ni llegan al origen.
- **Errores del origen no se cachean**: un fallo transitorio no se "congela" durante el TTL.
- **Riesgo aceptado**: un cambio de estado puede tardar hasta el TTL en verse. Adecuado para consulta de soporte; no para decisiones de pago.

## Cómo reproducir
```bash
.venv/bin/python -m pytest -q tests/test_cache.py
CFL_CACHE_TTL_SECONDS=0 .venv/bin/python scripts/measure_lookups.py --latency-ms 150   # sin caché
.venv/bin/python scripts/measure_lookups.py --latency-ms 150                           # con caché
```
En la interfaz web, elige "Proyecto 04", ejecuta dos veces la misma consulta y observa `caché {...}` al pie del resultado.

## Cómo repetir el ejercicio en tu propia sesión de Claude Code
1. Haz checkout del commit anterior a la mejora: `git switch -c practica-p4 e391b26`.
2. Abre Claude Code en la raíz (`claude`) y pide: *"Lee labs/04-claude-code/ISSUE.md e implementa la caché siguiendo
   CLAUDE.md. Primero propón el plan; luego implementa, ejecuta pytest y la medición."*
3. Toma las capturas indicadas en [docs/evidence/capturas-pendientes.md](../../docs/evidence/capturas-pendientes.md) (sección P4).
