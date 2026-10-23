import json

import pytest
from fastapi.testclient import TestClient

from cfl.web.app import create_app


@pytest.fixture
def client(settings, toolbox, monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    for name in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "GOOGLE_APPLICATION_CREDENTIALS", "AWS_ACCESS_KEY_ID",
                 "AWS_BEARER_TOKEN_BEDROCK", "AWS_PROFILE"):
        monkeypatch.delenv(name, raising=False)
    return TestClient(create_app(settings, toolbox))


def _sse_events(response):
    return [json.loads(line[6:]) for line in response.text.split("\n\n") if line.startswith("data: ")]


def test_index_and_static(client):
    assert "Claude Foundations Labs" in client.get("/").text
    assert client.get("/static/app.js").status_code == 200


def test_labs_listing(client):
    data = client.get("/api/labs").json()
    assert [lab["key"] for lab in data["labs"]] == ["01", "02", "03", "04", "05", "06", "07"]
    modes = {p["provider"]: p["mode"] for p in data["providers"]}
    assert modes == {"mock": "MOCK", "anthropic": "PENDIENTE", "vertex": "PENDIENTE", "bedrock": "PENDIENTE"}


def test_assistant_stream_mock(client, settings):
    r = client.post("/api/assistant/stream", json={"lab": "02", "provider": "mock", "query": "Estado de RMX-2026-000102"})
    events = _sse_events(r)
    assert events[0] == {"type": "meta", "provider": "Mock local (sin modelo)", "provider_key": "mock",
                         "model": "mock-deterministic-v1", "mode": "MOCK", "query": "Estado de RMX-2026-000102"}
    done = events[-1]
    assert done["type"] == "done" and done["mode"] == "MOCK"
    assert [t["name"] for t in done["tools_used"]] == ["get_transaction_status", "get_support_policy"]
    assert done["request_ids"] == [] and done["usage"] == {}
    log = (settings.evidence_dir / "runs" / "runs.jsonl").read_text(encoding="utf-8")
    assert done["run_id"] in log


@pytest.mark.parametrize("lab,provider", [("05", "vertex"), ("06", "bedrock"), ("02", "anthropic")])
def test_pending_providers_make_no_call(client, lab, provider):
    events = _sse_events(client.post("/api/assistant/stream", json={"lab": lab, "provider": provider, "query": "RMX-2026-000101"}))
    assert events[0]["mode"] == "PENDIENTE"
    assert events[1]["type"] == "pending" and events[1]["missing"]
    assert len(events) == 2


def test_provider_must_belong_to_lab(client):
    r = client.post("/api/assistant/stream", json={"lab": "05", "provider": "bedrock", "query": "x"})
    assert r.status_code == 400


def test_query_validation(client):
    assert client.post("/api/assistant/stream", json={"lab": "02", "provider": "mock", "query": ""}).status_code == 422


@pytest.mark.parametrize(
    "tx,is_error,found",
    [("RMX-2026-000104", False, True), ("RMX-2026-999999", False, False), ("RMX-12", True, None), (None, True, None)],
)
def test_mcp_endpoint(client, tx, is_error, found):
    data = client.post("/api/mcp/call", json={"transaction_id": tx}).json()
    assert data["mode"] == "MOCK" and data["is_error"] is is_error
    if found is not None:
        assert data["structured"]["found"] is found


def test_prompt_lab_pending_without_credentials(client):
    data = client.post("/api/prompt-labs/01/run", json={"provider": "anthropic"}).json()
    assert data["mode"] == "PENDIENTE" and data["outputs"] == []


def test_lab_detail_materials(client):
    data = client.get("/api/labs/01").json()
    paths = [m["path"] for m in data["materials"]]
    assert "labs/01-colaboracion-efectiva/prompts/02-prompt-mejorado.md" in paths
