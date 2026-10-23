"""Adaptador del Messages API de Claude.

Claude API, Claude en Vertex AI (`AnthropicVertex`) y Claude en Amazon Bedrock (`AnthropicBedrockMantle`)
exponen la misma superficie `messages.stream(...)`. Este adaptador encapsula esa superficie y normaliza
eventos, uso de tokens, request-id y errores; las diferencias por plataforma se declaran en el constructor.
"""

from __future__ import annotations

from typing import Any, Iterator

import anthropic

from cfl.providers.base import Mode, ProviderError, StreamEvent, TextDelta, ToolCall, TurnComplete, TurnResult

SERVER_FALLBACK_BETA = "server-side-fallback-2026-07-01"


def _usage_dict(usage: Any) -> dict[str, Any] | None:
    if usage is None:
        return None
    try:
        data = usage.model_dump(exclude_none=True)
    except AttributeError:
        return dict(usage) if isinstance(usage, dict) else None
    return data or None


def map_exception(exc: Exception, provider: str) -> ProviderError:
    """Convierte excepciones del SDK (y de credenciales de nube) en ProviderError."""
    request_id = getattr(exc, "request_id", None)
    status = getattr(exc, "status_code", None)
    message = getattr(exc, "message", None) or str(exc) or exc.__class__.__name__
    # Orden: de lo más específico a lo más general.
    if isinstance(exc, anthropic.AuthenticationError):
        kind, retry = "authentication", False
    elif isinstance(exc, anthropic.PermissionDeniedError):
        kind, retry = "permission", False
    elif isinstance(exc, anthropic.NotFoundError):
        kind, retry = "not_found", False
    elif isinstance(exc, anthropic.RateLimitError):
        kind, retry = "rate_limit", True
    elif isinstance(exc, anthropic.BadRequestError):
        kind, retry = "bad_request", False
    elif isinstance(exc, anthropic.APIStatusError):
        kind, retry = ("overloaded" if status == 529 else "server" if (status or 0) >= 500 else "api_error"), (status or 0) >= 500
    elif isinstance(exc, anthropic.APITimeoutError):
        kind, retry = "timeout", True
    elif isinstance(exc, anthropic.APIConnectionError):
        kind, retry = "connection", True
    elif _is_credentials_error(exc):
        kind, retry = "credentials", False
    else:
        kind, retry = "unknown", False
    return ProviderError(kind=kind, message=message, retryable=retry, status_code=status, request_id=request_id, provider=provider)


def _is_credentials_error(exc: Exception) -> bool:
    if isinstance(exc, getattr(anthropic, "CredentialsError", ())):
        return True
    try:
        from google.auth import exceptions as gexc

        if isinstance(exc, (gexc.DefaultCredentialsError, gexc.RefreshError)):
            return True
    except ImportError:  # pragma: no cover
        pass
    try:
        from botocore import exceptions as bexc

        if isinstance(exc, (bexc.NoCredentialsError, bexc.PartialCredentialsError, bexc.ProfileNotFound)):
            return True
    except ImportError:  # pragma: no cover
        pass
    return False


class MessagesAPIProvider:
    mode: Mode = "LIVE"

    def __init__(
        self,
        *,
        name: str,
        client: Any,
        model: str,
        max_tokens: int = 16000,
        effort: str = "medium",
        server_fallbacks: bool = False,
        eager_input_streaming: bool = True,
    ) -> None:
        self.name = name
        self.client = client
        self.model = model
        self.max_tokens = max_tokens
        self.effort = effort
        # El parámetro `fallbacks` del servidor solo existe en la Claude API (no en Vertex ni Bedrock).
        self.server_fallbacks = server_fallbacks
        self.eager_input_streaming = eager_input_streaming

    def build_params(self, *, system: str, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> dict[str, Any]:
        params: dict[str, Any] = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "system": system,
            "messages": messages,
            # Claude Opus 5.5 siempre usa pensamiento adaptativo; el esfuerzo es el control de profundidad.
            "output_config": {"effort": self.effort},
        }
        if tools:
            params["tools"] = [
                {**tool, "eager_input_streaming": True} if self.eager_input_streaming else dict(tool) for tool in tools
            ]
        if self.server_fallbacks:
            params["betas"] = [SERVER_FALLBACK_BETA]
            params["fallbacks"] = "default"
        return params

    def _messages_api(self) -> Any:
        return self.client.beta.messages if self.server_fallbacks else self.client.messages

    def stream_turn(
        self, *, system: str, messages: list[dict[str, Any]], tools: list[dict[str, Any]]
    ) -> Iterator[StreamEvent]:
        params = self.build_params(system=system, messages=messages, tools=tools)
        try:
            with self._messages_api().stream(**params) as stream:
                for event in stream:
                    if getattr(event, "type", None) == "text":
                        yield TextDelta(event.text)
                final = stream.get_final_message()
                request_id = getattr(stream, "request_id", None)
        except ValueError as exc:
            # Con eager_input_streaming el SDK puede no poder parsear un input de herramienta.
            raise ProviderError(
                kind="invalid_tool_json", message=f"Input de herramienta no parseable: {exc}", retryable=True, provider=self.name
            ) from exc
        except ProviderError:
            raise
        except Exception as exc:  # noqa: BLE001 - se normaliza
            raise map_exception(exc, self.name) from exc
        yield TurnComplete(self._to_result(final, request_id))

    def complete(self, *, system: str, prompt: str) -> TurnResult:
        result: TurnResult | None = None
        for event in self.stream_turn(system=system, messages=[{"role": "user", "content": prompt}], tools=[]):
            if isinstance(event, TurnComplete):
                result = event.result
        assert result is not None
        return result

    def _to_result(self, final: Any, request_id: str | None) -> TurnResult:
        text_parts: list[str] = []
        calls: list[ToolCall] = []
        for block in final.content:
            if block.type == "text":
                text_parts.append(block.text)
            elif block.type == "tool_use":
                calls.append(ToolCall(id=block.id, name=block.name, input=block.input))
        stop_details = getattr(final, "stop_details", None)
        return TurnResult(
            assistant_content=list(final.content),
            text="".join(text_parts),
            tool_calls=calls,
            stop_reason=final.stop_reason,
            model=getattr(final, "model", self.model),
            request_id=request_id or getattr(final, "_request_id", None),
            usage=_usage_dict(getattr(final, "usage", None)),
            stop_details=stop_details.model_dump() if hasattr(stop_details, "model_dump") else None,
        )
