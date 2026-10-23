"""Servidor MCP de remesas sintéticas (Proyecto 7).

Expone:
- Herramienta `get_transaction_status` (solo lectura).
- Recurso `policies://soporte-remesas` con las políticas sintéticas en Markdown.
- Prompt `investigar_incidente` para guiar la investigación de un incidente.

Reutiliza el mismo Toolbox del Proyecto 2: una sola fuente de validación y lógica de negocio.

Ejecución:
    python -m cfl.mcp_server.server                      # stdio (Claude Code / Claude Desktop)
    python -m cfl.mcp_server.server --transport streamable-http --port 8765
"""

from __future__ import annotations

import argparse
from typing import Any

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.server.mcpserver.prompts.base import UserMessage
from mcp.types import ToolAnnotations

from cfl.config import Settings
from cfl.tools import Toolbox, build_default_toolbox

POLICIES_URI = "policies://soporte-remesas"


def create_server(toolbox: Toolbox | None = None) -> MCPServer:
    toolbox = toolbox or build_default_toolbox(Settings.from_env())
    mcp = MCPServer(
        "remesas-sinteticas",
        title="Soporte de remesas (datos sintéticos)",
        version="0.1.0",
        instructions=(
            "Servidor educativo con datos 100% sintéticos. Las herramientas son de solo lectura. "
            "Si una transacción no existe (found=false), no inventes datos."
        ),
    )

    @mcp.tool(
        title="Consultar estado de transacción",
        annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False),
    )
    def get_transaction_status(transaction_id: str) -> dict[str, Any]:
        """Consulta (solo lectura) el estado de una remesa sintética por su ID con formato RMX-AAAA-NNNNNN.

        Devuelve found=false si la transacción no existe; en ese caso no hay datos que reportar.
        """
        outcome = toolbox.execute("get_transaction_status", {"transaction_id": transaction_id})
        if outcome.is_error:
            # Solo el mensaje de un ToolError llega al modelo; los detalles internos quedan en el log.
            raise ToolError(f"{outcome.error_code}: {outcome.content['message']}")
        return outcome.content

    @mcp.resource(
        POLICIES_URI,
        name="politicas-soporte",
        title="Políticas sintéticas de soporte",
        description="Políticas ficticias de soporte de remesas (privacidad, retenciones, retrasos, cancelaciones, fallidas, escalamiento).",
        mime_type="text/markdown",
    )
    def support_policies() -> str:
        return toolbox.policies.to_markdown()

    @mcp.prompt(name="investigar_incidente", title="Investigar incidente de remesa")
    def investigar_incidente(transaction_id: str, sintoma: str = "El cliente reporta que el beneficiario no ha recibido el dinero.") -> list[UserMessage]:
        """Guía paso a paso para investigar un incidente de una remesa sintética."""
        return [
            UserMessage(
                f"Investiga el incidente reportado sobre la transacción {transaction_id}.\n"
                f"Síntoma reportado: {sintoma}\n\n"
                "Pasos:\n"
                f"1. Llama a la herramienta get_transaction_status con transaction_id=\"{transaction_id}\".\n"
                "2. Si found=false, informa que la transacción no existe y detente: no supongas datos.\n"
                f"3. Lee el recurso {POLICIES_URI} y aplica la sección que corresponda al estado.\n"
                "4. Entrega: (a) hechos verificados con su fecha de última actualización, (b) hipótesis "
                "marcadas explícitamente como hipótesis, (c) qué comunicar al cliente, (d) si se debe escalar y a qué nivel.\n"
                "Usa solo referencias enmascaradas; los datos son sintéticos."
            )
        ]

    return mcp


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Servidor MCP de remesas sintéticas")
    parser.add_argument("--transport", choices=["stdio", "streamable-http"], default="stdio")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args(argv)
    server = create_server()
    if args.transport == "stdio":
        server.run("stdio")
    else:
        server.run("streamable-http", host=args.host, port=args.port)


if __name__ == "__main__":
    main()
