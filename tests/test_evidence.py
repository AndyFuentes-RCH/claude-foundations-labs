import pytest

from cfl.assistant import SupportAssistant
from cfl.evidence import EvidenceRecorder, record_assistant_result
from cfl.evidence.recorder import FIELDS
from cfl.providers.mock import MockProvider


def test_missing_fields_are_null(tmp_path):
    entry = EvidenceRecorder(tmp_path).record(project="02", mode="MOCK", provider="mock")
    assert set(entry) == set(FIELDS)
    assert entry["request_ids"] is None and entry["usage"] is None and entry["model"] is None
    assert entry["timestamp_utc"].endswith("+00:00")


def test_unknown_fields_rejected(tmp_path):
    with pytest.raises(ValueError):
        EvidenceRecorder(tmp_path).record(api_key="nunca")


def test_assistant_result_roundtrip(tmp_path, toolbox):
    recorder = EvidenceRecorder(tmp_path)
    result = SupportAssistant(MockProvider(), toolbox).run("RMX-2026-000101")
    record_assistant_result(recorder, "02-asistente-claude-api", result)
    [saved] = recorder.read_all()
    assert saved["mode"] == "MOCK" and saved["provider"] == "mock"
    assert saved["tools_invoked"][0]["name"] == "get_transaction_status"
    assert saved["request_ids"] is None  # el mock no tiene request-id: no se inventa
