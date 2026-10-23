from __future__ import annotations

from typing import Any, Iterator

import pytest

from cfl.config import DATA_DIR, Settings
from cfl.domain import JsonTransactionRepository, PolicyBook
from cfl.providers.base import Mode, StreamEvent, TextDelta, ToolCall, TurnComplete, TurnResult
from cfl.tools import Toolbox


@pytest.fixture
def settings(tmp_path) -> Settings:
    """Settings aislados: sin credenciales, sin consumo y con evidencia en un directorio temporal."""
    return Settings.from_env(env={"CFL_EVIDENCE_DIR": str(tmp_path / "evidence")})


@pytest.fixture
def repository() -> JsonTransactionRepository:
    return JsonTransactionRepository(DATA_DIR / "transactions.json")


@pytest.fixture
def policies() -> PolicyBook:
    return PolicyBook(DATA_DIR / "support_policies.json")


@pytest.fixture
def toolbox(repository, policies) -> Toolbox:
    return Toolbox(repository, policies)


def text_turn(text: str, stop_reason: str = "end_turn", **extra: Any) -> TurnResult:
    return TurnResult(assistant_content=[{"type": "text", "text": text}], text=text, tool_calls=[],
                      stop_reason=stop_reason, model="fake-model", **extra)


def tool_turn(*calls: tuple[str, str, Any], stop_reason: str = "tool_use", text: str = "") -> TurnResult:
    tool_calls = [ToolCall(id=i, name=n, input=inp) for i, n, inp in calls]
    content: list[dict[str, Any]] = [{"type": "text", "text": text}] if text else []
    content += [{"type": "tool_use", "id": c.id, "name": c.name, "input": c.input} for c in tool_calls]
    return TurnResult(assistant_content=content, text=text, tool_calls=tool_calls, stop_reason=stop_reason,
                      model="fake-model", request_id=f"req_{tool_calls[0].id}", usage={"input_tokens": 10, "output_tokens": 5})


class ScriptedProvider:
    """Proveedor de prueba: devuelve turnos predefinidos y guarda lo que recibió."""

    name = "fake"
    model = "fake-model"
    mode: Mode = "MOCK"

    def __init__(self, turns: list[TurnResult | Exception]) -> None:
        self.turns = list(turns)
        self.calls: list[list[dict[str, Any]]] = []

    def stream_turn(self, *, system: str, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> Iterator[StreamEvent]:
        self.calls.append([dict(m) for m in messages])
        turn = self.turns.pop(0)
        if isinstance(turn, Exception):
            raise turn
        if turn.text:
            yield TextDelta(turn.text)
        yield TurnComplete(turn)

    def complete(self, *, system: str, prompt: str) -> TurnResult:  # pragma: no cover
        return text_turn("ok")
