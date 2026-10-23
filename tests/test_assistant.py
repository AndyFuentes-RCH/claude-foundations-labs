import json

from cfl.assistant import SupportAssistant
from cfl.providers.base import ProviderError
from cfl.providers.mock import MOCK_BANNER, MockProvider
from tests.conftest import ScriptedProvider, text_turn, tool_turn


def _events(assistant, query):
    events = list(assistant.stream(query))
    return events, events[-1]["result"]


def test_tool_loop_and_grounded_answer(toolbox):
    provider = ScriptedProvider([
        tool_turn(("t1", "get_transaction_status", {"transaction_id": "RMX-2026-000102"})),
        text_turn("RMX-2026-000102 está IN_TRANSIT. Fuentes: get_transaction_status RMX-2026-000102"),
    ])
    events, result = _events(SupportAssistant(provider, toolbox), "¿Estado de RMX-2026-000102?")
    assert result.ok and result.iterations == 2
    assert result.records_consulted == ["RMX-2026-000102"]
    assert result.ungrounded_ids == []
    assert result.request_ids == ["req_t1"]
    assert result.usage == {"input_tokens": 10, "output_tokens": 5}
    assert [e["type"] for e in events].count("tool_result") == 1
    # el tool_result vuelve en un mensaje user con el tool_use_id correcto
    tool_msg = provider.calls[1][-1]
    assert tool_msg["role"] == "user" and tool_msg["content"][0]["tool_use_id"] == "t1"
    assert json.loads(tool_msg["content"][0]["content"])["found"] is True


def test_parallel_tool_calls_return_in_single_message(toolbox):
    provider = ScriptedProvider([
        tool_turn(("a", "get_transaction_status", {"transaction_id": "RMX-2026-000101"}),
                  ("b", "get_transaction_history", {"transaction_id": "RMX-2026-000101"})),
        text_turn("listo"),
    ])
    SupportAssistant(provider, toolbox).run("q")
    last = provider.calls[1][-1]
    assert [b["tool_use_id"] for b in last["content"]] == ["a", "b"]


def test_invalid_argument_marks_is_error(toolbox):
    provider = ScriptedProvider([
        tool_turn(("t1", "get_transaction_status", {"transaction_id": "RMX-1"})),
        text_turn("El ID no es válido."),
    ])
    result = SupportAssistant(provider, toolbox).run("RMX-1")
    block = provider.calls[1][-1]["content"][0]
    assert block["is_error"] is True
    assert result.tools_used[0]["error_code"] == "INVALID_ARGUMENT"


def test_iteration_limit(toolbox):
    turns = [tool_turn((f"t{i}", "get_transaction_status", {"transaction_id": "RMX-2026-000101"})) for i in range(5)]
    result = SupportAssistant(ScriptedProvider(turns), toolbox, max_iterations=3).run("q")
    assert result.stop_reason == "iteration_limit"
    assert result.error["kind"] == "iteration_limit"
    assert result.iterations == 3
    assert "límite de iteraciones" in result.answer


def test_provider_error_is_reported(toolbox):
    err = ProviderError(kind="rate_limit", message="429", retryable=True, status_code=429, request_id="req_x", provider="fake")
    result = SupportAssistant(ScriptedProvider([err]), toolbox).run("q")
    assert not result.ok and result.error["kind"] == "rate_limit" and result.error["retryable"]
    assert result.request_ids == ["req_x"]


def test_invalid_tool_json_is_retried(toolbox):
    provider = ScriptedProvider([
        ProviderError(kind="invalid_tool_json", message="bad", retryable=True, provider="fake"),
        text_turn("respuesta"),
    ])
    events, result = _events(SupportAssistant(provider, toolbox), "q")
    assert result.ok and result.answer == "respuesta"
    assert any(e["type"] == "warning" for e in events)


def test_refusal_stops(toolbox):
    turn = text_turn("", stop_reason="refusal", stop_details={"category": "cyber"})
    result = SupportAssistant(ScriptedProvider([turn]), toolbox).run("q")
    assert result.error["kind"] == "refusal"


def test_truncated_tool_call_is_not_executed(toolbox):
    turn = tool_turn(("t1", "get_transaction_status", {"transaction_id": "RMX-2026-0001"}), stop_reason="max_tokens")
    result = SupportAssistant(ScriptedProvider([turn]), toolbox).run("q")
    assert result.error["kind"] == "max_tokens" and result.tools_used == []


def test_ungrounded_ids_are_flagged(toolbox):
    provider = ScriptedProvider([text_turn("La transacción RMX-2026-000105 fue pagada.")])
    events, result = _events(SupportAssistant(provider, toolbox), "¿Y la RMX-2026-000105?")
    assert result.ungrounded_ids == ["RMX-2026-000105"]
    assert any(e["type"] == "warning" for e in events)


def test_intermediate_text_is_not_part_of_final_answer(toolbox):
    provider = ScriptedProvider([
        tool_turn(("t1", "get_transaction_status", {"transaction_id": "RMX-2026-000101"}), text="Voy a consultar."),
        text_turn("Pagada."),
    ])
    assert SupportAssistant(provider, toolbox).run("q").answer == "Pagada."


# --- Mock determinista de extremo a extremo -------------------------------------------

def test_mock_on_hold_consults_policy(toolbox):
    result = SupportAssistant(MockProvider(), toolbox).run("¿Qué pasa con RMX-2026-000111?")
    names = [t["name"] for t in result.tools_used]
    assert names == ["get_transaction_status", "get_support_policy"]
    assert result.answer.startswith(MOCK_BANNER)
    assert "BENEFICIARY_NAME_MISMATCH" in result.answer
    assert result.mode == "MOCK" and result.ungrounded_ids == []


def test_mock_not_found_does_not_invent(toolbox):
    result = SupportAssistant(MockProvider(), toolbox).run("Estado de RMX-2026-424242")
    assert "No encontré la transacción RMX-2026-424242" in result.answer
    for word in ("PAID", "IN_TRANSIT", "ON_HOLD", "USD"):
        assert word not in result.answer


def test_mock_without_id_asks_for_it(toolbox):
    result = SupportAssistant(MockProvider(), toolbox).run("¿Dónde está mi dinero?")
    assert result.tools_used == [] and "RMX-AAAA-NNNNNN" in result.answer


def test_mock_history_request(toolbox):
    result = SupportAssistant(MockProvider(), toolbox).run("historial de RMX-2026-000108")
    assert [t["name"] for t in result.tools_used][:2] == ["get_transaction_status", "get_transaction_history"]
    assert "CREATED → FUNDED → FAILED → REFUNDED" in result.answer
