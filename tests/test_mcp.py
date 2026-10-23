"""Pruebas del servidor MCP con el cliente oficial (en memoria y por stdio). No interviene Claude."""

from __future__ import annotations

import pytest
from mcp import Client

from cfl.mcp_server.client import exercise, stdio_params
from cfl.mcp_server.server import POLICIES_URI, create_server


@pytest.fixture
def server(toolbox):
    return create_server(toolbox)


async def test_capabilities_are_listed(server):
    async with Client(server) as client:
        tools = (await client.list_tools()).tools
        assert [t.name for t in tools] == ["get_transaction_status"]
        assert tools[0].annotations.read_only_hint is True
        assert tools[0].annotations.destructive_hint is False
        assert [str(r.uri) for r in (await client.list_resources()).resources] == [POLICIES_URI]
        assert [p.name for p in (await client.list_prompts()).prompts] == ["investigar_incidente"]


async def test_existing_transaction(server):
    async with Client(server) as client:
        result = await client.call_tool("get_transaction_status", {"transaction_id": "rmx-2026-000103"})
    assert not result.is_error
    assert result.structured_content["transaction"]["status"] == "AVAILABLE_FOR_PICKUP"


async def test_missing_transaction_is_reported_not_invented(server):
    async with Client(server) as client:
        result = await client.call_tool("get_transaction_status", {"transaction_id": "RMX-2026-999999"})
    assert not result.is_error
    assert result.structured_content == {
        "found": False,
        "transaction_id": "RMX-2026-999999",
        "message": "No existe ninguna transacción con ese ID en los registros sintéticos.",
    }


@pytest.mark.parametrize("args", [{"transaction_id": "RMX-12"}, {"transaction_id": "' OR 1=1 --"}, {}, {"transaction_id": 7}])
async def test_invalid_inputs_return_tool_errors(server, args):
    async with Client(server) as client:
        result = await client.call_tool("get_transaction_status", args)
    assert result.is_error and result.structured_content is None


async def test_invalid_format_message_reaches_model(server):
    async with Client(server) as client:
        result = await client.call_tool("get_transaction_status", {"transaction_id": "RMX-12"})
    assert "INVALID_ARGUMENT" in result.content[0].text and "RMX-AAAA-NNNNNN" in result.content[0].text


async def test_unknown_tool(server):
    async with Client(server) as client:
        result = await client.call_tool("cancel_transaction", {"transaction_id": "RMX-2026-000101"})
    assert result.is_error


async def test_internal_errors_do_not_leak(policies):
    from cfl.tools import Toolbox

    class Broken:
        def get(self, _):
            raise RuntimeError("secreto interno")

    async with Client(create_server(Toolbox(Broken(), policies))) as client:
        result = await client.call_tool("get_transaction_status", {"transaction_id": "RMX-2026-000101"})
    assert result.is_error and "secreto interno" not in result.content[0].text


async def test_resource_and_prompt(server):
    async with Client(server) as client:
        resource = await client.read_resource(POLICIES_URI)
        assert "Políticas sintéticas" in resource.contents[0].text
        prompt = await client.get_prompt("investigar_incidente", {"transaction_id": "RMX-2026-000111", "sintoma": "retraso"})
    text = prompt.messages[0].content.text
    assert prompt.messages[0].role == "user"
    assert "RMX-2026-000111" in text and "retraso" in text and POLICIES_URI in text


async def test_stdio_subprocess_end_to_end():
    report = await exercise(stdio_params())
    cases = {c["case"]: c["is_error"] for c in report["calls"]}
    assert cases == {"existente": False, "inexistente": False, "formato inválido": True,
                     "tipo inválido": True, "argumento faltante": True}
