"""Proveedor MOCK determinista: imita el protocolo de tool use sin llamar a ningún modelo.

Sirve para demostrar y probar el bucle del asistente sin credenciales ni consumo. Sus respuestas
se construyen con plantillas a partir de los resultados de herramientas y se marcan como MOCK;
no son respuestas de Claude y no deben presentarse como tales.
"""

from __future__ import annotations

import itertools
import json
import re
from typing import Any, Iterator

from cfl.providers.base import Mode, StreamEvent, TextDelta, ToolCall, TurnComplete, TurnResult

MOCK_BANNER = "[MOCK — respuesta de plantilla generada localmente, sin llamar a Claude]"
_ID_CANDIDATE = re.compile(r"\bRMX[-_ ]?[0-9A-Z]{1,6}(?:[-_ ][0-9A-Z]{1,8})?\b", re.IGNORECASE)
_POLICY_FOR_STATUS = {
    "ON_HOLD": "retenciones",
    "IN_TRANSIT": "retrasos",
    "FAILED": "fallidas",
    "CANCELLED": "cancelaciones",
    "REFUNDED": "cancelaciones",
}


class MockProvider:
    name = "mock"
    model = "mock-deterministic-v1"
    mode: Mode = "MOCK"

    def __init__(self, chunk_size: int = 24) -> None:
        self._ids = itertools.count(1)
        self.chunk_size = chunk_size

    # -- API pública -----------------------------------------------------------------
    def stream_turn(
        self, *, system: str, messages: list[dict[str, Any]], tools: list[dict[str, Any]]
    ) -> Iterator[StreamEvent]:
        result = self._decide(messages)
        for i in range(0, len(result.text), self.chunk_size):
            yield TextDelta(result.text[i : i + self.chunk_size])
        yield TurnComplete(result)

    def complete(self, *, system: str, prompt: str) -> TurnResult:
        text = f"{MOCK_BANNER}\nEl modo MOCK no genera contenido para este laboratorio; ejecútalo en modo LIVE."
        return self._text_result(text)

    # -- Lógica determinista --------------------------------------------------------
    def _decide(self, messages: list[dict[str, Any]]) -> TurnResult:
        last = messages[-1]
        content = last.get("content")
        if isinstance(content, str):
            return self._first_turn(content)
        results = _collect_tool_results(messages)
        follow_up = self._policy_follow_up(results)
        if follow_up:
            return follow_up
        return self._text_result(self._compose_answer(results))

    def _first_turn(self, query: str) -> TurnResult:
        candidates = list(dict.fromkeys(m.group(0) for m in _ID_CANDIDATE.finditer(query)))
        if not candidates:
            return self._text_result(
                f"{MOCK_BANNER}\nPara consultar una remesa necesito su identificador "
                "con formato RMX-AAAA-NNNNNN (por ejemplo RMX-2026-000101)."
            )
        calls = [ToolCall(self._next_id(), "get_transaction_status", {"transaction_id": c}) for c in candidates[:3]]
        if "historial" in query.lower() or "historia" in query.lower():
            calls += [ToolCall(self._next_id(), "get_transaction_history", {"transaction_id": c}) for c in candidates[:1]]
        return self._tool_result(calls)

    def _policy_follow_up(self, results: list[dict[str, Any]]) -> TurnResult | None:
        if any(r["name"] == "get_support_policy" for r in results):
            return None
        topics: list[str] = []
        for r in results:
            tx = (r["payload"] or {}).get("transaction")
            if r["name"] == "get_transaction_status" and tx and tx.get("status") in _POLICY_FOR_STATUS:
                topic = _POLICY_FOR_STATUS[tx["status"]]
                if topic not in topics:
                    topics.append(topic)
        if not topics:
            return None
        return self._tool_result([ToolCall(self._next_id(), "get_support_policy", {"topic": t}) for t in topics])

    @staticmethod
    def _compose_answer(results: list[dict[str, Any]]) -> str:
        lines = [MOCK_BANNER]
        policies = [r["payload"]["policy"] for r in results if r["name"] == "get_support_policy" and r["payload"] and r["payload"].get("policy")]
        for r in results:
            payload = r["payload"] or {}
            if r["name"] == "get_transaction_status":
                if r["is_error"]:
                    raw = (r["input"] or {}).get("transaction_id", "")
                    lines.append(
                        f"- El identificador «{raw}» no es válido ({payload.get('message', 'formato incorrecto')}). "
                        "No consulté ningún registro con él."
                    )
                elif not payload.get("found"):
                    lines.append(
                        f"- No encontré la transacción {payload.get('transaction_id')} en los registros sintéticos. "
                        "Verifica el ID con el cliente; no puedo dar información de una transacción que no existe."
                    )
                else:
                    tx = payload["transaction"]
                    line = (
                        f"- {tx['transaction_id']}: estado {tx['status']} — {tx['status_detail']} "
                        f"(última actualización registrada: {tx['updated_at']})."
                    )
                    if tx.get("hold_reason"):
                        line += f" Motivo de retención registrado: {tx['hold_reason']}."
                    if tx.get("estimated_availability"):
                        line += f" Disponibilidad estimada registrada: {tx['estimated_availability']}."
                    lines.append(line)
            elif r["name"] == "get_transaction_history" and payload.get("found"):
                events = payload["history"]["events"]
                lines.append(f"- Historial ({len(events)} eventos): " + " → ".join(e["status"] for e in events) + ".")
        hold_reasons = {
            (r["payload"] or {}).get("transaction", {}).get("hold_reason")
            for r in results
            if r["name"] == "get_transaction_status"
        } - {None}
        for policy in policies:
            # Prioriza las reglas que mencionan el motivo registrado; si no hay, usa la primera.
            specific = [rule for rule in policy["rules"] if any(reason in rule for reason in hold_reasons)]
            for rule in specific or policy["rules"][:1]:
                lines.append(f"- Política aplicable «{policy['title']}»: {rule}")
        lines.append("Fuente: herramientas de solo lectura sobre datos sintéticos.")
        return "\n".join(lines)

    # -- Construcción de bloques ----------------------------------------------------
    def _next_id(self) -> str:
        return f"mock_toolu_{next(self._ids):04d}"

    def _text_result(self, text: str) -> TurnResult:
        return TurnResult(
            assistant_content=[{"type": "text", "text": text}],
            text=text,
            tool_calls=[],
            stop_reason="end_turn",
            model=self.model,
        )

    def _tool_result(self, calls: list[ToolCall]) -> TurnResult:
        content = [{"type": "tool_use", "id": c.id, "name": c.name, "input": c.input} for c in calls]
        return TurnResult(assistant_content=content, text="", tool_calls=calls, stop_reason="tool_use", model=self.model)


def _collect_tool_results(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Empareja cada tool_use del historial con su tool_result."""
    uses: dict[str, dict[str, Any]] = {}
    out: list[dict[str, Any]] = []
    for message in messages:
        content = message.get("content")
        if not isinstance(content, list):
            continue
        for block in content:
            block = block if isinstance(block, dict) else block.model_dump()
            if block.get("type") == "tool_use":
                uses[block["id"]] = block
            elif block.get("type") == "tool_result":
                use = uses.get(block["tool_use_id"], {})
                try:
                    payload = json.loads(block.get("content") or "null")
                except (TypeError, json.JSONDecodeError):
                    payload = None
                out.append(
                    {
                        "name": use.get("name"),
                        "input": use.get("input"),
                        "is_error": bool(block.get("is_error")),
                        "payload": payload,
                    }
                )
    return out
