# Proyecto 5 · Claude en Google Cloud (Vertex AI)

**Curso relacionado:** Claude on Google Cloud
**Estado:** Pendiente de credenciales o intervención — el adaptador está implementado y probado **sin red**;
la validación en vivo no se ha ejecutado. No se aprovisionó ningún recurso ni se generó consumo.

## Qué se implementó
- `build_live_provider("vertex")` en [src/cfl/providers/factory.py](../../src/cfl/providers/factory.py) crea
  `anthropic.AnthropicVertex(project_id, region)` y lo envuelve en el mismo `MessagesAPIProvider` del Proyecto 2.
  El caso de soporte (herramientas, streaming, límites, errores) se reutiliza sin cambios.
- Diferencias de plataforma aplicadas: sin parámetro `fallbacks` (no existe en Vertex); IDs de modelo sin prefijo.
- Errores de credenciales de Google (`DefaultCredentialsError`, `RefreshError`) se clasifican como `credentials`.
- Interruptor de consumo: sin `CFL_ALLOW_LIVE_CALLS=true` el proveedor queda en **PENDIENTE**.

## Configuración (variables de entorno)
| Variable | Valor | Notas |
|----------|-------|-------|
| `ANTHROPIC_VERTEX_PROJECT_ID` | ID de tu proyecto GCP | Obligatorio |
| `CLOUD_ML_REGION` | `global` (recomendado), `us` o `eu` | Los endpoints regionales solo sirven Sonnet 4.6 y anteriores; para Opus 5.5 usa `global` o multi-región |
| `CFL_VERTEX_MODEL` | `claude-opus-5-5` | Sin prefijo ni sufijo de fecha en modelos actuales |
| `GOOGLE_APPLICATION_CREDENTIALS` | ruta a JSON de cuenta de servicio | Opcional; si no, se usa ADC de `gcloud` |
| `CFL_ALLOW_LIVE_CALLS` | `true` | Solo cuando autorices el consumo |

## Requisitos previos (los realiza el titular de la cuenta)
1. Proyecto de Google Cloud con facturación activa y acceso a Agent Platform / Vertex AI.
2. Habilitar el modelo Claude deseado en **Model Garden** (busca "Claude") para tu proyecto.
3. Rol con permiso `aiplatform.endpoints.predict`, por ejemplo **Agent Platform User** (`roles/aiplatform.user`).
4. `gcloud` instalado y credenciales locales: `gcloud auth application-default login`.

## Prueba real (cuando autorices el consumo)
```bash
export ANTHROPIC_VERTEX_PROJECT_ID=tu-proyecto CLOUD_ML_REGION=global CFL_ALLOW_LIVE_CALLS=true
.venv/bin/python -m cfl.assistant "¿Cuál es el estado de RMX-2026-000104?" --provider vertex
```
Una consulta típica consume 2–3 llamadas al modelo (por las herramientas). El resultado, el request-id y los tokens
quedan en `docs/evidence/runs/runs.jsonl` con `project = 05-claude-google-cloud`. También puedes usar la interfaz web
(Proyecto 05, proveedor Vertex).

## Qué se validó sin red
`tests/test_providers.py::test_vertex_client_is_built_without_network` construye el cliente real del SDK y verifica el
host `aiplatform.googleapis.com` y la ausencia de `fallbacks`; `test_vertex_status_reads_env` verifica la lectura de
configuración. Ninguna prueba contacta a Google Cloud.

## Pendiente
- [ ] Proyecto GCP, habilitación del modelo y credenciales ADC (tu intervención).
- [ ] Autorizar el consumo y ejecutar la prueba real.

Referencia: documentación oficial "Claude Models on Google Cloud" en platform.claude.com (consultada el 2026-10-23).
