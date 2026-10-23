"""Catálogo de laboratorios: fuente única de títulos, cursos, estado y modos para la interfaz y la documentación.

Estados permitidos (definidos en el README):
- "Preparado"
- "Validado localmente"
- "Validado con Claude"
- "Pendiente de credenciales o intervención"
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

STATUSES = ("Preparado", "Validado localmente", "Validado con Claude", "Pendiente de credenciales o intervención")


@dataclass(frozen=True)
class Lab:
    key: str
    folder: str
    title: str
    courses: tuple[str, ...]
    kind: str  # prompt | assistant | manual | cache | mcp
    status: str
    status_note: str
    providers: tuple[str, ...] = ()
    examples: tuple[str, ...] = ()
    materials: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict:
        data = asdict(self)
        data["readme"] = f"labs/{self.folder}/README.md"
        return data


ASSISTANT_EXAMPLES = (
    "¿Cuál es el estado de RMX-2026-000104 y qué le digo al cliente?",
    "El cliente pregunta por RMX-2026-000111, dice que no le llega el dinero.",
    "Dame el historial de RMX-2026-000108.",
    "¿Qué pasó con RMX-2026-999999?",
    "Revisa la remesa RMX-12",
)

LABS: tuple[Lab, ...] = (
    Lab(
        key="01", folder="01-colaboracion-efectiva",
        title="Colaboración efectiva con Claude: de requisitos a especificación técnica",
        courses=("AI Fluency: Framework & Foundations", "Claude 101"),
        kind="prompt", status="Pendiente de credenciales o intervención",
        status_note="Prompts, insumos y criterios listos. Falta ejecutar en LIVE (API key) y la revisión humana de Andy.",
        providers=("anthropic",),
        materials=("insumos/requisitos-integracion.md", "prompts/01-prompt-inicial.md", "prompts/02-prompt-mejorado.md",
                   "evaluacion/criterios.md", "revision-humana.md"),
    ),
    Lab(
        key="02", folder="02-asistente-claude-api",
        title="Asistente de estado de remesas con Claude API (tool use + streaming)",
        courses=("Building with the Claude API",),
        kind="assistant", status="Validado localmente",
        status_note="Bucle, herramientas y validaciones probados con pytest y en modo MOCK. Ejecución LIVE pendiente de API key.",
        providers=("mock", "anthropic"), examples=ASSISTANT_EXAMPLES,
    ),
    Lab(
        key="03", folder="03-flujo-productividad",
        title="Flujo de productividad: resumen ejecutivo, tabla de acciones y correo",
        courses=("Claude 101", "AI Fluency: Framework & Foundations"),
        kind="manual", status="Pendiente de credenciales o intervención",
        status_note="Documento sintético, prompts y guía de capturas listos. Requiere práctica manual en Claude.ai.",
        providers=("anthropic",),
        materials=("insumos/documento-requisitos.md", "prompts/claude-ai-listos-para-pegar.md", "guia-capturas.md"),
    ),
    Lab(
        key="04", folder="04-claude-code",
        title="Desarrollo con Claude Code: caché con TTL para consultas de transacciones",
        courses=("Claude Code in Action",),
        kind="cache", status="Preparado",
        status_note="Problema y comportamiento esperado registrados antes de modificar el código.",
        providers=("mock", "anthropic"), examples=ASSISTANT_EXAMPLES[:3],
        materials=("ISSUE.md",),
    ),
    Lab(
        key="05", folder="05-claude-google-cloud",
        title="Claude en Google Cloud (Vertex AI)",
        courses=("Claude on Google Cloud",),
        kind="assistant", status="Pendiente de credenciales o intervención",
        status_note="Adaptador AnthropicVertex implementado y probado sin red. Validación en vivo pendiente de proyecto GCP y autorización.",
        providers=("vertex",), examples=ASSISTANT_EXAMPLES,
    ),
    Lab(
        key="06", folder="06-claude-amazon-bedrock",
        title="Claude en Amazon Bedrock",
        courses=("Claude with Amazon Bedrock",),
        kind="assistant", status="Pendiente de credenciales o intervención",
        status_note="Adaptador AnthropicBedrockMantle implementado y probado sin red. No hay despliegue en AWS; validación en vivo pendiente.",
        providers=("bedrock",), examples=ASSISTANT_EXAMPLES,
        materials=("iam-policy-minima.json",),
    ),
    Lab(
        key="07", folder="07-model-context-protocol",
        title="Servidor MCP de remesas sintéticas",
        courses=("Introduction to Model Context Protocol",),
        kind="mcp", status="Validado localmente",
        status_note="Servidor y cliente local probados (memoria y stdio). Conexión real con Claude pendiente de ejecutar.",
        examples=("RMX-2026-000104", "RMX-2026-999999", "RMX-12"),
    ),
)

LABS_BY_KEY = {lab.key: lab for lab in LABS}
assert all(lab.status in STATUSES for lab in LABS)
