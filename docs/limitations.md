# Limitaciones y pasos pendientes

## Limitaciones conocidas
- **Sin ejecuciones LIVE.** En la sesión de construcción no había credenciales de Claude API, GCP ni AWS. El
  comportamiento con modelos reales (calidad de respuestas, latencia, tokens) no está medido.
- **El mock no es Claude.** Responde con plantillas deterministas para demostrar el flujo de herramientas; no evalúa la
  calidad del razonamiento del modelo. Sus respuestas están marcadas como MOCK.
- **Verificación de fundamentación parcial.** Comprueba que los IDs mencionados provengan de herramientas; no verifica
  semánticamente cada afirmación (p. ej., un estado mal transcrito). Para eso habría que añadir evaluaciones con modelo.
- **Política IAM de Bedrock.** Usa `"Resource": "*"` porque el formato de ARN de `bedrock-mantle` no se pudo confirmar en
  la documentación consultada; debe restringirse antes de un uso real. El valor exacto de la condición de bearer tokens
  también debe verificarse.
- **Datos estáticos.** El repositorio JSON simula un backend; no hay concurrencia de escrituras ni cambios de estado en vivo.
- **Caché local por proceso.** La caché TTL no se comparte entre réplicas; en producción se usaría una caché distribuida.
- **Interfaz sin autenticación.** Pensada para demostración local (`127.0.0.1`). No exponerla públicamente.
- **MCP por HTTP sin autenticación.** El transporte Streamable HTTP es solo para pruebas locales.

## Pendientes por laboratorio
| Proyecto | Pendiente | Quién | Requiere |
|----------|-----------|-------|----------|
| 1 | Ejecutar ambos prompts en LIVE y completar `revision-humana.md` | Andy | API key + autorizar ~2 llamadas |
| 2 | Ejecución LIVE con los casos de demostración | Andy (o Claude con tu autorización) | API key + autorizar consumo |
| 3 | Práctica en Claude.ai y capturas | Andy | Cuenta de Claude.ai |
| 5 | Proyecto GCP, Model Garden, ADC y prueba real | Andy | Credenciales GCP + autorizar gasto |
| 6 | Cuenta AWS, acceso al modelo, perfil con política mínima y prueba real | Andy | Credenciales AWS + autorizar gasto |
| 7 | Aprobar `remesas-sinteticas` en Claude Code (o configurar Claude Desktop) y probarlo | Andy | Aprobación del servidor |

## Mejoras posibles
- Evaluación automática con Claude como juez (con rúbrica) para el Proyecto 1, siempre complementada por revisión humana.
- Prompt caching del prompt de sistema y herramientas en ejecuciones LIVE (verificar `cache_read_input_tokens`).
- Trazas con OpenTelemetry.
- Despliegue en contenedor con autenticación, solo si se autoriza.
