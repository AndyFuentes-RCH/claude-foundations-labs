# Proyecto 6 · Claude en Amazon Bedrock

**Curso relacionado:** Claude with Amazon Bedrock
**Estado:** Pendiente de credenciales o intervención — el adaptador existe **solo como código local** probado sin red.
**No hay ningún despliegue en AWS** y no se ha realizado ninguna llamada a Bedrock.

## Qué se implementó
- `build_live_provider("bedrock")` crea `anthropic.AnthropicBedrockMantle(aws_region, aws_profile)`: el cliente oficial
  vigente para el endpoint Messages API de Bedrock (`https://bedrock-mantle.{region}.api.aws/anthropic/v1/messages`),
  con firma SigV4 o bearer token. Se reutiliza el `MessagesAPIProvider` del Proyecto 2.
- Diferencias de plataforma: IDs de modelo con prefijo `anthropic.`; sin `fallbacks` de servidor (no disponible en Bedrock).
- Errores de AWS (`NoCredentialsError`, `PartialCredentialsError`, `ProfileNotFound`) → `credentials`; 403 → `permission`
  (típico cuando falta acceso al modelo o el permiso IAM); 429 → `rate_limit` reintentable.

> El cliente `AnthropicBedrock` (sin "Mantle") corresponde a la integración *legacy* InvokeModel/Converse con IDs
> versionados por ARN (Opus 4.6 y anteriores). Este proyecto usa el camino vigente para Opus 4.7 y posteriores.

## Configuración
| Variable | Ejemplo | Notas |
|----------|---------|-------|
| `AWS_REGION` | `us-east-1` | Región con endpoint Mantle (ver tabla de regiones en la documentación) |
| `AWS_PROFILE` | `remesas-labs` | Perfil de `~/.aws/config` (SSO o rol asumido, recomendado) |
| `AWS_BEARER_TOKEN_BEDROCK` | token de corta duración | Alternativa a SigV4; generar con `aws-bedrock-token-generator` |
| `CFL_BEDROCK_MODEL` | `anthropic.claude-opus-5-5` | También acepta un *inference profile* (ID o ARN) para enrutar dentro de una geografía |
| `CFL_ALLOW_LIVE_CALLS` | `true` | Solo cuando autorices el consumo |

**Global vs. regional:** el endpoint global no tiene recargo; el regional cuesta 10 % más y sirve para residencia de datos.
Para enrutar dentro de US/EU/JP/AU usa un inference profile en `CFL_BEDROCK_MODEL`.

## Permisos mínimos
[iam-policy-minima.json](iam-policy-minima.json):
1. `bedrock-mantle:CreateInference` — la única acción necesaria para inferencia en el endpoint Mantle.
   **Recomendación:** sustituye `"Resource": "*"` por los ARN de los modelos permitidos. Consulta el formato exacto del
   recurso en la *Service Authorization Reference* de AWS para `bedrock-mantle` antes de restringirlo; no se incluye un ARN
   aquí porque no se pudo verificar en la documentación consultada.
2. Denegar bearer tokens de larga duración (según la guía de Anthropic: "deny `bedrock:CallWithBearerToken` unless
   `bedrock:BearerTokenType` matches a short-term token"). Verifica el valor exacto de la condición en la referencia de IAM.

Además, la cuenta debe tener habilitado el acceso al modelo en *Bedrock → Model access*.

## Prueba real (cuando autorices el consumo)
```bash
aws sts get-caller-identity --profile remesas-labs        # confirma identidad, sin costo de Bedrock
export AWS_PROFILE=remesas-labs AWS_REGION=us-east-1 CFL_ALLOW_LIVE_CALLS=true
.venv/bin/python -m cfl.assistant "¿Cuál es el estado de RMX-2026-000104?" --provider bedrock
```
La ejecución queda en `docs/evidence/runs/runs.jsonl` con `project = 06-claude-amazon-bedrock`, request-id y tokens.
Para soporte ante fallos, AWS pide el `request-id` que registra este proyecto.

## Qué se validó sin red
`tests/test_providers.py::test_bedrock_mantle_client_is_built_without_network` construye el cliente real con credenciales
falsas y verifica el host `bedrock-mantle.us-east-1`; `test_map_connection_and_cloud_credential_errors` verifica el
mapeo de `NoCredentialsError`. Ninguna prueba contacta a AWS.

## Pendiente
- [ ] Cuenta AWS con acceso al modelo, rol/perfil con la política mínima (tu intervención).
- [ ] Autorizar el consumo y ejecutar la prueba real; capturas de terminal y CloudTrail/CloudWatch.

Referencia: "Claude in Amazon Bedrock" en platform.claude.com y "bedrock-mantle" en docs.aws.amazon.com (consultadas el 2026-10-23).
