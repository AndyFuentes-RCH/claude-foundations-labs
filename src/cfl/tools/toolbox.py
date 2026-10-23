"""Definición, validación y ejecución de herramientas de solo lectura.

Ninguna herramienta modifica datos: el asistente consulta, no opera.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any, Callable

from pydantic import BaseModel, ConfigDict, ValidationError, field_validator

from cfl.config import Settings
from cfl.domain.errors import DataSourceError, InvalidTransactionIdError
from cfl.domain.models import normalize_transaction_id
from cfl.domain.policies import PolicyBook
from cfl.domain.repository import JsonTransactionRepository, TransactionRepository

logger = logging.getLogger(__name__)

POLICY_TOPICS = ("privacidad", "retenciones", "retrasos", "cancelaciones", "fallidas", "escalamiento")


class _TransactionArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")
    transaction_id: str

    @field_validator("transaction_id", mode="before")
    @classmethod
    def _normalize(cls, value: object) -> str:
        try:
            return normalize_transaction_id(value)
        except InvalidTransactionIdError as exc:
            raise ValueError(str(exc)) from exc


class _PolicyArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")
    topic: str

    @field_validator("topic", mode="before")
    @classmethod
    def _known_topic(cls, value: object) -> str:
        if not isinstance(value, str) or value.strip().lower() not in POLICY_TOPICS:
            raise ValueError(f"topic debe ser uno de: {', '.join(POLICY_TOPICS)}")
        return value.strip().lower()


_TRANSACTION_ID_SCHEMA = {
    "type": "string",
    "description": "Identificador con formato RMX-AAAA-NNNNNN, por ejemplo RMX-2026-000101.",
}

TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "name": "get_transaction_status",
        "description": (
            "Consulta (solo lectura) el estado actual de una remesa sintética por su ID. "
            "Devuelve estado, detalle, montos, método de pago, motivo de retención y disponibilidad estimada. "
            "Si la transacción no existe devuelve found=false: en ese caso no inventes datos."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"transaction_id": _TRANSACTION_ID_SCHEMA},
            "required": ["transaction_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "get_transaction_history",
        "description": (
            "Consulta (solo lectura) el historial cronológico de eventos de una remesa sintética. "
            "Úsala cuando necesites explicar cómo llegó la transacción a su estado actual."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"transaction_id": _TRANSACTION_ID_SCHEMA},
            "required": ["transaction_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "get_support_policy",
        "description": (
            "Consulta (solo lectura) la política sintética de soporte aplicable a un tema. "
            "Úsala antes de indicar al agente qué comunicar o cuándo escalar."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"topic": {"type": "string", "enum": list(POLICY_TOPICS)}},
            "required": ["topic"],
            "additionalProperties": False,
        },
    },
]


@dataclass
class ToolOutcome:
    """Resultado normalizado de una ejecución de herramienta."""

    name: str
    arguments: Any
    is_error: bool
    content: dict[str, Any]
    error_code: str | None = None
    transaction_ids: list[str] = field(default_factory=list)  # registros efectivamente consultados

    def as_text(self) -> str:
        return json.dumps(self.content, ensure_ascii=False)


class Toolbox:
    def __init__(self, repository: TransactionRepository, policies: PolicyBook) -> None:
        self.repository = repository
        self.policies = policies
        self._handlers: dict[str, tuple[type[BaseModel], Callable[[Any], ToolOutcome]]] = {
            "get_transaction_status": (_TransactionArgs, self._status),
            "get_transaction_history": (_TransactionArgs, self._history),
            "get_support_policy": (_PolicyArgs, self._policy),
        }

    def definitions(self) -> list[dict[str, Any]]:
        return [dict(tool) for tool in TOOL_DEFINITIONS]

    def execute(self, name: str, arguments: Any) -> ToolOutcome:
        handler = self._handlers.get(name)
        if handler is None:
            return self._error(name, arguments, "UNKNOWN_TOOL", f"La herramienta '{name}' no existe.")
        model, func = handler
        if not isinstance(arguments, dict):
            return self._error(name, arguments, "INVALID_ARGUMENT", "Los argumentos deben ser un objeto JSON.")
        try:
            args = model.model_validate(arguments)
        except ValidationError as exc:
            details = "; ".join(f"{'.'.join(map(str, e['loc'])) or 'input'}: {e['msg']}" for e in exc.errors())
            return self._error(name, arguments, "INVALID_ARGUMENT", details)
        try:
            return func(args)
        except DataSourceError as exc:
            logger.exception("Fallo del origen de datos en %s", name)
            return self._error(name, arguments, "DATA_SOURCE_ERROR", str(exc))
        except Exception:  # noqa: BLE001 - nunca propagamos un fallo de herramienta al bucle
            logger.exception("Error inesperado en la herramienta %s", name)
            return self._error(name, arguments, "INTERNAL_ERROR", "Error interno al ejecutar la herramienta.")

    @staticmethod
    def _error(name: str, arguments: Any, code: str, message: str) -> ToolOutcome:
        return ToolOutcome(
            name=name,
            arguments=arguments,
            is_error=True,
            content={"error": code, "message": message},
            error_code=code,
        )

    def _status(self, args: _TransactionArgs) -> ToolOutcome:
        tx = self.repository.get(args.transaction_id)
        if tx is None:
            return self._not_found("get_transaction_status", args.transaction_id)
        return ToolOutcome(
            name="get_transaction_status",
            arguments=args.model_dump(),
            is_error=False,
            content={"found": True, "transaction": tx.status_view()},
            transaction_ids=[tx.transaction_id],
        )

    def _history(self, args: _TransactionArgs) -> ToolOutcome:
        tx = self.repository.get(args.transaction_id)
        if tx is None:
            return self._not_found("get_transaction_history", args.transaction_id)
        return ToolOutcome(
            name="get_transaction_history",
            arguments=args.model_dump(),
            is_error=False,
            content={"found": True, "history": tx.history_view()},
            transaction_ids=[tx.transaction_id],
        )

    def _policy(self, args: _PolicyArgs) -> ToolOutcome:
        policy = self.policies.get(args.topic)
        if policy is None:  # el validador ya filtra temas; protección adicional
            return self._error("get_support_policy", args.model_dump(), "NOT_FOUND", "Tema sin política.")
        return ToolOutcome(
            name="get_support_policy",
            arguments=args.model_dump(),
            is_error=False,
            content={"found": True, "policy": policy},
        )

    @staticmethod
    def _not_found(name: str, transaction_id: str) -> ToolOutcome:
        # No es un error de la herramienta: la consulta fue válida y la respuesta es "no existe".
        return ToolOutcome(
            name=name,
            arguments={"transaction_id": transaction_id},
            is_error=False,
            content={
                "found": False,
                "transaction_id": transaction_id,
                "message": "No existe ninguna transacción con ese ID en los registros sintéticos.",
            },
        )


def build_default_toolbox(settings: Settings | None = None) -> Toolbox:
    settings = settings or Settings.from_env()
    repository = JsonTransactionRepository(settings.transactions_path, latency_ms=settings.simulated_latency_ms)
    return Toolbox(repository, PolicyBook(settings.policies_path))
