"""Bucle de tool use del asistente de soporte de remesas (Proyecto 2).

- Streaming: el texto se emite a medida que llega.
- Tool use manual: cada `tool_use` se valida y ejecuta en el Toolbox; todos los resultados de un turno
  vuelven en un único mensaje `user`.
- Límite de iteraciones: evita bucles infinitos o costosos.
- Manejo de errores: errores de proveedor, stop_reason `refusal` y `max_tokens` con herramientas truncadas.
- Fundamentación: tras responder, se comprueba que cada ID mencionado haya pasado por una herramienta.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from typing import Any, Iterator

from cfl.assistant.prompts import SUPPORT_SYSTEM_PROMPT
from cfl.domain.errors import InvalidTransactionIdError
from cfl.domain.models import normalize_transaction_id
from cfl.providers.base import ModelProvider, ProviderError, TextDelta, TurnComplete, TurnResult
from cfl.tools.toolbox import Toolbox

_STRICT_ID = re.compile(r"RMX-\d{4}-\d{6}")
MAX_INVALID_JSON_RETRIES = 2


@dataclass
class AssistantResult:
    query: str
    answer: str
    provider: str
    model: str
    mode: str
    stop_reason: str | None
    iterations: int
    tools_used: list[dict[str, Any]] = field(default_factory=list)
    request_ids: list[str] = field(default_factory=list)
    usage: dict[str, int] = field(default_factory=dict)
    records_consulted: list[str] = field(default_factory=list)
    ungrounded_ids: list[str] = field(default_factory=list)
    error: dict[str, Any] | None = None
    duration_ms: int = 0

    @property
    def ok(self) -> bool:
        return self.error is None


class SupportAssistant:
    def __init__(self, provider: ModelProvider, toolbox: Toolbox, max_iterations: int = 5, system_prompt: str = SUPPORT_SYSTEM_PROMPT) -> None:
        self.provider = provider
        self.toolbox = toolbox
        self.max_iterations = max_iterations
        self.system_prompt = system_prompt

    def run(self, query: str) -> AssistantResult:
        result: AssistantResult | None = None
        for event in self.stream(query):
            if event["type"] == "done":
                result = event["result"]
        assert result is not None
        return result

    def stream(self, query: str) -> Iterator[dict[str, Any]]:
        """Generador de eventos: text, tool_call, tool_result, warning, error y, al final, done."""
        started = time.monotonic()
        messages: list[dict[str, Any]] = [{"role": "user", "content": query}]
        tools = self.toolbox.definitions()
        result = AssistantResult(
            query=query, answer="", provider=self.provider.name, model=self.provider.model,
            mode=self.provider.mode, stop_reason=None, iterations=0,
        )
        grounded_ids: set[str] = set()
        answer_parts: list[str] = []
        json_retries = 0

        while True:
            if result.iterations >= self.max_iterations:
                result.stop_reason = "iteration_limit"
                result.error = {
                    "kind": "iteration_limit",
                    "message": f"Se alcanzó el límite de {self.max_iterations} iteraciones sin respuesta final.",
                }
                note = "\n[Se detuvo la consulta: límite de iteraciones alcanzado. Escala el caso a un agente.]"
                answer_parts.append(note)
                yield {"type": "error", **result.error}
                break
            result.iterations += 1

            try:
                turn = yield from self._stream_one_turn(messages, tools)
            except ProviderError as exc:
                if exc.kind == "invalid_tool_json" and json_retries < MAX_INVALID_JSON_RETRIES:
                    json_retries += 1
                    yield {"type": "warning", "message": "Input de herramienta no parseable; se reintenta el turno."}
                    continue
                result.error = {"kind": exc.kind, "message": exc.message, "retryable": exc.retryable,
                                "status_code": exc.status_code, "request_id": exc.request_id}
                if exc.request_id:
                    result.request_ids.append(exc.request_id)
                yield {"type": "error", **result.error}
                break
            json_retries = 0

            self._accumulate(result, turn)
            if turn.text:
                answer_parts.append(turn.text)
            result.stop_reason = turn.stop_reason

            if turn.stop_reason == "refusal":
                result.error = {"kind": "refusal", "message": "El modelo declinó la solicitud.", "stop_details": turn.stop_details}
                yield {"type": "error", **result.error}
                break
            if not turn.tool_calls:
                break  # end_turn, stop_sequence o max_tokens con texto: respuesta final
            if turn.stop_reason == "max_tokens":
                # Un input de herramienta truncado puede parsear como objeto parcial: no se ejecuta.
                result.error = {"kind": "max_tokens", "message": "Respuesta truncada durante una llamada a herramienta."}
                yield {"type": "error", **result.error}
                break

            messages.append({"role": "assistant", "content": turn.assistant_content})
            tool_results = []
            for call in turn.tool_calls:
                yield {"type": "tool_call", "id": call.id, "name": call.name, "input": call.input}
                outcome = self.toolbox.execute(call.name, call.input)
                if isinstance(call.input, dict) and isinstance(call.input.get("transaction_id"), str):
                    grounded_ids.add(call.input["transaction_id"].strip().upper())
                grounded_ids.update(_STRICT_ID.findall(outcome.as_text().upper()))
                for tx_id in outcome.transaction_ids:
                    if tx_id not in result.records_consulted:
                        result.records_consulted.append(tx_id)
                record = {
                    "name": call.name,
                    "input": call.input,
                    "is_error": outcome.is_error,
                    "error_code": outcome.error_code,
                    "found": outcome.content.get("found"),
                }
                result.tools_used.append(record)
                yield {"type": "tool_result", **record}
                block: dict[str, Any] = {"type": "tool_result", "tool_use_id": call.id, "content": outcome.as_text()}
                if outcome.is_error:
                    block["is_error"] = True
                tool_results.append(block)
            messages.append({"role": "user", "content": tool_results})
            answer_parts.clear()  # el texto intermedio entre herramientas no forma parte de la respuesta final

        result.answer = "".join(answer_parts).strip()
        result.ungrounded_ids = self._ungrounded_ids(result.answer, grounded_ids)
        if result.ungrounded_ids:
            yield {
                "type": "warning",
                "message": "La respuesta menciona IDs que no se consultaron con herramientas: " + ", ".join(result.ungrounded_ids),
            }
        result.duration_ms = int((time.monotonic() - started) * 1000)
        yield {"type": "done", "result": result}

    def _stream_one_turn(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> Iterator[dict[str, Any]]:
        turn: TurnResult | None = None
        for event in self.provider.stream_turn(system=self.system_prompt, messages=messages, tools=tools):
            if isinstance(event, TextDelta):
                yield {"type": "text", "text": event.text}
            elif isinstance(event, TurnComplete):
                turn = event.result
        if turn is None:
            raise ProviderError(kind="unknown", message="El proveedor terminó sin turno completo.", provider=self.provider.name)
        return turn

    @staticmethod
    def _accumulate(result: AssistantResult, turn: TurnResult) -> None:
        if turn.request_id:
            result.request_ids.append(turn.request_id)
        result.model = turn.model or result.model
        for key, value in (turn.usage or {}).items():
            if isinstance(value, int):
                result.usage[key] = result.usage.get(key, 0) + value

    @staticmethod
    def _ungrounded_ids(answer: str, grounded: set[str]) -> list[str]:
        """IDs bien formados que aparecen en la respuesta pero no salen de la entrada ni de la salida de una herramienta."""
        seen: set[str] = set()
        for raw in grounded:
            try:
                seen.add(normalize_transaction_id(raw))
            except InvalidTransactionIdError:
                continue
        mentioned = dict.fromkeys(_STRICT_ID.findall(answer.upper()))
        return [tx for tx in mentioned if tx not in seen]
