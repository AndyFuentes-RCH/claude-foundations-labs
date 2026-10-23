import pytest

from cfl.domain.errors import DataSourceError
from cfl.tools.toolbox import POLICY_TOPICS, TOOL_DEFINITIONS, Toolbox


def test_tool_definitions_are_read_only_and_strict():
    names = {t["name"] for t in TOOL_DEFINITIONS}
    assert names == {"get_transaction_status", "get_transaction_history", "get_support_policy"}
    for tool in TOOL_DEFINITIONS:
        assert tool["input_schema"]["additionalProperties"] is False
        assert "solo lectura" in tool["description"]


def test_status_found(toolbox):
    out = toolbox.execute("get_transaction_status", {"transaction_id": "rmx-2026-000102"})
    assert not out.is_error
    assert out.content["found"] is True
    assert out.content["transaction"]["status"] == "IN_TRANSIT"
    assert "events" not in out.content["transaction"]
    assert out.transaction_ids == ["RMX-2026-000102"]


def test_status_not_found_is_not_an_error(toolbox):
    out = toolbox.execute("get_transaction_status", {"transaction_id": "RMX-2026-999999"})
    assert out.is_error is False
    assert out.content["found"] is False
    assert out.transaction_ids == []


def test_history(toolbox):
    out = toolbox.execute("get_transaction_history", {"transaction_id": "RMX-2026-000106"})
    statuses = [e["status"] for e in out.content["history"]["events"]]
    assert statuses == ["CREATED", "FUNDED", "IN_TRANSIT", "FAILED"]


@pytest.mark.parametrize(
    "arguments",
    [
        {"transaction_id": "RMX-12"},
        {"transaction_id": 101},
        {},
        {"transaction_id": "RMX-2026-000101", "extra": "x"},
        "RMX-2026-000101",
        None,
    ],
)
def test_invalid_arguments(toolbox, arguments):
    out = toolbox.execute("get_transaction_status", arguments)
    assert out.is_error and out.error_code == "INVALID_ARGUMENT"


def test_unknown_tool(toolbox):
    out = toolbox.execute("cancel_transaction", {"transaction_id": "RMX-2026-000101"})
    assert out.is_error and out.error_code == "UNKNOWN_TOOL"


@pytest.mark.parametrize("topic", POLICY_TOPICS)
def test_policy_topics(toolbox, topic):
    out = toolbox.execute("get_support_policy", {"topic": topic.upper()})
    assert not out.is_error and out.content["policy"]["topic"] == topic


def test_policy_unknown_topic(toolbox):
    out = toolbox.execute("get_support_policy", {"topic": "descuentos"})
    assert out.is_error and out.error_code == "INVALID_ARGUMENT"


class _BrokenRepo:
    def __init__(self, exc):
        self.exc = exc

    def get(self, transaction_id):
        raise self.exc


def test_data_source_error_is_contained(policies):
    out = Toolbox(_BrokenRepo(DataSourceError("caído")), policies).execute(
        "get_transaction_status", {"transaction_id": "RMX-2026-000101"})
    assert out.is_error and out.error_code == "DATA_SOURCE_ERROR"


def test_unexpected_error_is_contained(policies):
    out = Toolbox(_BrokenRepo(RuntimeError("boom")), policies).execute(
        "get_transaction_status", {"transaction_id": "RMX-2026-000101"})
    assert out.is_error and out.error_code == "INTERNAL_ERROR"
    assert "boom" not in out.as_text()  # no se filtran detalles internos al modelo
