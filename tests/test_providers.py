"""Pruebas de proveedores sin red: estado PENDIENTE, construcción de clientes reales y mapeo de errores."""

from __future__ import annotations

from types import SimpleNamespace

import anthropic
import httpx2
import pytest

from cfl.config import Settings
from cfl.providers import ProviderUnavailable, TextDelta, TurnComplete, build_provider, provider_status
from cfl.providers.factory import build_live_provider
from cfl.providers.messages_api import SERVER_FALLBACK_BETA, MessagesAPIProvider, map_exception

CLEAN_ENV = ["ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "GOOGLE_APPLICATION_CREDENTIALS", "AWS_ACCESS_KEY_ID",
             "AWS_SECRET_ACCESS_KEY", "AWS_BEARER_TOKEN_BEDROCK", "ANTHROPIC_AWS_API_KEY", "AWS_PROFILE",
             "AWS_WEB_IDENTITY_TOKEN_FILE", "AWS_CONTAINER_CREDENTIALS_RELATIVE_URI"]


@pytest.fixture(autouse=True)
def isolated_home(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    for name in CLEAN_ENV:
        monkeypatch.delenv(name, raising=False)


def test_mock_is_always_available(settings):
    status = provider_status("mock", settings)
    assert status.mode == "MOCK"
    assert build_provider("mock", settings).mode == "MOCK"


@pytest.mark.parametrize("name", ["anthropic", "vertex", "bedrock"])
def test_real_providers_pending_without_credentials(settings, name):
    status = provider_status(name, settings)
    assert status.mode == "PENDIENTE" and not status.credentials_configured
    with pytest.raises(ProviderUnavailable):
        build_provider(name, settings)


def test_credentials_without_authorization_stay_pending(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-not-real")
    s = Settings.from_env(env={"CFL_ALLOW_LIVE_CALLS": "false"})
    status = provider_status("anthropic", s)
    assert status.credentials_configured and status.mode == "PENDIENTE"
    assert any("CFL_ALLOW_LIVE_CALLS" in m for m in status.missing)


def test_live_when_credentials_and_authorization(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-not-real")
    s = Settings.from_env(env={"CFL_ALLOW_LIVE_CALLS": "true"})
    assert provider_status("anthropic", s).mode == "LIVE"
    provider = build_provider("anthropic", s)
    assert provider.name == "anthropic" and provider.model == "claude-opus-5-5" and provider.server_fallbacks


def test_vertex_status_reads_env(monkeypatch, tmp_path):
    adc = tmp_path / "adc.json"
    adc.write_text("{}")
    monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", str(adc))
    s = Settings.from_env(env={"ANTHROPIC_VERTEX_PROJECT_ID": "demo-proyecto", "CLOUD_ML_REGION": "us",
                               "CFL_ALLOW_LIVE_CALLS": "true"})
    status = provider_status("vertex", s)
    assert status.mode == "LIVE" and status.details == {"project_id": "demo-proyecto", "region": "us"}


def test_vertex_client_is_built_without_network():
    s = Settings.from_env(env={"ANTHROPIC_VERTEX_PROJECT_ID": "demo-proyecto", "CLOUD_ML_REGION": "global"})
    provider = build_live_provider("vertex", s)
    assert isinstance(provider.client, anthropic.AnthropicVertex)
    assert provider.server_fallbacks is False  # `fallbacks` no existe en Vertex
    assert "aiplatform.googleapis.com" in str(provider.client.base_url)


def test_bedrock_mantle_client_is_built_without_network(monkeypatch):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "AKIAEXAMPLENOTREAL")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "not-a-real-secret")
    s = Settings.from_env(env={"AWS_REGION": "us-east-1", "CFL_BEDROCK_MODEL": "anthropic.claude-opus-5-5"})
    provider = build_live_provider("bedrock", s)
    assert isinstance(provider.client, anthropic.AnthropicBedrockMantle)
    assert "bedrock-mantle.us-east-1" in str(provider.client.base_url)
    assert provider.model == "anthropic.claude-opus-5-5" and provider.server_fallbacks is False


# --- Parámetros y streaming con un cliente falso ---------------------------------------

class _FakeStream:
    def __init__(self, final, events):
        self._final, self._events = final, events
        self.request_id = "req_fake_123"

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def __iter__(self):
        return iter(self._events)

    def get_final_message(self):
        return self._final


class _FakeMessages:
    def __init__(self, stream):
        self._stream, self.params = stream, None

    def stream(self, **params):
        self.params = params
        return self._stream


def _final_message():
    return SimpleNamespace(
        content=[SimpleNamespace(type="text", text="Hola"),
                 SimpleNamespace(type="tool_use", id="toolu_1", name="get_transaction_status", input={"transaction_id": "RMX-2026-000101"})],
        stop_reason="tool_use", model="claude-opus-5-5", stop_details=None,
        usage=SimpleNamespace(model_dump=lambda exclude_none: {"input_tokens": 100, "output_tokens": 20}),
    )


def test_stream_turn_normalizes_result():
    messages = _FakeMessages(_FakeStream(_final_message(), [SimpleNamespace(type="text", text="Hola")]))
    client = SimpleNamespace(messages=messages, beta=SimpleNamespace(messages=None))
    provider = MessagesAPIProvider(name="vertex", client=client, model="claude-opus-5-5", effort="low")
    events = list(provider.stream_turn(system="s", messages=[{"role": "user", "content": "q"}],
                                       tools=[{"name": "t", "description": "d", "input_schema": {"type": "object"}}]))
    assert isinstance(events[0], TextDelta) and isinstance(events[-1], TurnComplete)
    result = events[-1].result
    assert result.request_id == "req_fake_123" and result.usage == {"input_tokens": 100, "output_tokens": 20}
    assert result.tool_calls[0].name == "get_transaction_status"
    assert messages.params["output_config"] == {"effort": "low"}
    assert messages.params["tools"][0]["eager_input_streaming"] is True
    assert "fallbacks" not in messages.params and "temperature" not in messages.params


def test_server_fallbacks_use_beta_namespace():
    beta_messages = _FakeMessages(_FakeStream(_final_message(), []))
    client = SimpleNamespace(messages=None, beta=SimpleNamespace(messages=beta_messages))
    provider = MessagesAPIProvider(name="anthropic", client=client, model="claude-opus-5-5", server_fallbacks=True)
    list(provider.stream_turn(system="s", messages=[{"role": "user", "content": "q"}], tools=[]))
    assert beta_messages.params["betas"] == [SERVER_FALLBACK_BETA]
    assert beta_messages.params["fallbacks"] == "default"


def test_unparseable_tool_json_maps_to_retryable_error():
    class _Bad(_FakeStream):
        def __iter__(self):
            raise ValueError("Unable to parse tool parameter JSON")

    client = SimpleNamespace(messages=_FakeMessages(_Bad(None, [])), beta=None)
    provider = MessagesAPIProvider(name="bedrock", client=client, model="m")
    with pytest.raises(Exception) as info:
        list(provider.stream_turn(system="s", messages=[], tools=[]))
    assert info.value.kind == "invalid_tool_json" and info.value.retryable


# --- Mapeo de errores del SDK ---------------------------------------------------------

def _status_error(cls, code):
    request = httpx2.Request("POST", "https://example.invalid/v1/messages")
    response = httpx2.Response(code, request=request, headers={"request-id": "req_err_1"})
    return cls("mensaje", response=response, body=None)


@pytest.mark.parametrize(
    "cls,code,kind,retryable",
    [
        (anthropic.AuthenticationError, 401, "authentication", False),
        (anthropic.PermissionDeniedError, 403, "permission", False),
        (anthropic.NotFoundError, 404, "not_found", False),
        (anthropic.RateLimitError, 429, "rate_limit", True),
        (anthropic.BadRequestError, 400, "bad_request", False),
        (anthropic.InternalServerError, 500, "server", True),
    ],
)
def test_map_status_errors(cls, code, kind, retryable):
    err = map_exception(_status_error(cls, code), "anthropic")
    assert (err.kind, err.retryable, err.status_code) == (kind, retryable, code)
    assert err.request_id == "req_err_1"


def test_map_connection_and_cloud_credential_errors():
    request = httpx2.Request("POST", "https://example.invalid")
    assert map_exception(anthropic.APIConnectionError(request=request), "vertex").kind == "connection"
    from botocore.exceptions import NoCredentialsError
    from google.auth.exceptions import DefaultCredentialsError

    assert map_exception(DefaultCredentialsError("sin ADC"), "vertex").kind == "credentials"
    assert map_exception(NoCredentialsError(), "bedrock").kind == "credentials"
