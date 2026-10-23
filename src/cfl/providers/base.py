"""Contrato común de los proveedores de modelo."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterator, Literal, Protocol, Union

Mode = Literal["LIVE", "MOCK", "PENDIENTE"]


@dataclass
class ToolCall:
    id: str
    name: str
    input: Any


@dataclass
class TurnResult:
    """Un turno completo del modelo, ya acumulado tras el streaming."""

    assistant_content: list[Any]  # se reenvía tal cual en el historial (incluye bloques de thinking)
    text: str
    tool_calls: list[ToolCall]
    stop_reason: str | None
    model: str
    request_id: str | None = None
    usage: dict[str, Any] | None = None
    stop_details: dict[str, Any] | None = None


@dataclass
class TextDelta:
    text: str


@dataclass
class TurnComplete:
    result: TurnResult


StreamEvent = Union[TextDelta, TurnComplete]


@dataclass
class ProviderError(Exception):
    """Error normalizado de proveedor; `kind` permite decidir si reintentar o escalar."""

    kind: str  # authentication | permission | not_found | rate_limit | overloaded | bad_request | connection | timeout | invalid_tool_json | credentials | server | unknown
    message: str
    retryable: bool = False
    status_code: int | None = None
    request_id: str | None = None
    provider: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:  # pragma: no cover - representación
        return f"[{self.provider}:{self.kind}] {self.message}"


class ProviderUnavailable(Exception):
    """El proveedor no puede ejecutarse (faltan credenciales o autorización): modo PENDIENTE."""

    def __init__(self, provider: str, missing: list[str]) -> None:
        self.provider = provider
        self.missing = missing
        super().__init__(f"{provider}: pendiente — falta {', '.join(missing)}")


class ModelProvider(Protocol):
    name: str  # anthropic | vertex | bedrock | mock
    model: str
    mode: Mode

    def stream_turn(
        self, *, system: str, messages: list[dict[str, Any]], tools: list[dict[str, Any]]
    ) -> Iterator[StreamEvent]:
        """Emite TextDelta durante la generación y termina con exactamente un TurnComplete."""
        ...

    def complete(self, *, system: str, prompt: str) -> TurnResult:
        """Una sola respuesta sin herramientas (Labs 1 y 3)."""
        ...
