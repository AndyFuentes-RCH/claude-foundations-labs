"""Modelos de transacciones sintéticas."""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict

from cfl.domain.errors import InvalidTransactionIdError

TRANSACTION_ID_PATTERN = re.compile(r"^RMX-\d{4}-\d{6}$")

TransactionStatus = Literal[
    "CREATED",
    "PENDING_FUNDING",
    "FUNDED",
    "IN_TRANSIT",
    "AVAILABLE_FOR_PICKUP",
    "PAID",
    "ON_HOLD",
    "CANCELLED",
    "FAILED",
    "REFUNDED",
]


def normalize_transaction_id(raw: object) -> str:
    """Normaliza (mayúsculas, sin espacios) y valida un ID; lanza InvalidTransactionIdError."""
    if not isinstance(raw, str):
        raise InvalidTransactionIdError("transaction_id debe ser texto.")
    candidate = raw.strip().upper()
    if not TRANSACTION_ID_PATTERN.fullmatch(candidate):
        raise InvalidTransactionIdError(
            f"'{raw}' no tiene el formato RMX-AAAA-NNNNNN (por ejemplo RMX-2026-000101)."
        )
    return candidate


class Money(BaseModel):
    model_config = ConfigDict(frozen=True)
    amount: str
    currency: str


class TransactionEvent(BaseModel):
    model_config = ConfigDict(frozen=True)
    timestamp: str
    status: TransactionStatus
    note: str


class Transaction(BaseModel):
    model_config = ConfigDict(frozen=True)

    transaction_id: str
    status: TransactionStatus
    status_detail: str
    created_at: str
    updated_at: str
    origin_country: str
    destination_country: str
    send_amount: Money
    receive_amount: Money
    fx_rate: str
    fee: Money
    payout_method: Literal["BANK_DEPOSIT", "CASH_PICKUP", "MOBILE_WALLET"]
    payer_partner: str
    sender_ref: str
    beneficiary_ref: str
    hold_reason: str | None = None
    estimated_availability: str | None = None
    events: tuple[TransactionEvent, ...] = ()

    def status_view(self) -> dict:
        """Vista resumida que devuelven las herramientas (sin el historial completo)."""
        data = self.model_dump(exclude={"events"})
        data["synthetic"] = True
        return data

    def history_view(self) -> dict:
        return {
            "transaction_id": self.transaction_id,
            "current_status": self.status,
            "events": [event.model_dump() for event in self.events],
            "synthetic": True,
        }
