"""Repositorio de transacciones (solo lectura) sobre el archivo JSON sintético."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Protocol

from pydantic import ValidationError

from cfl.domain.errors import DataSourceError
from cfl.domain.models import Transaction, normalize_transaction_id


class TransactionRepository(Protocol):
    def get(self, transaction_id: str) -> Transaction | None:
        """Devuelve la transacción o None si no existe. Lanza InvalidTransactionIdError si el ID es inválido."""
        ...


class JsonTransactionRepository:
    """Simula el "core de remesas": cada consulta relee el origen, como lo haría una llamada remota.

    `latency_ms` permite simular la latencia de red de un backend real.
    """

    def __init__(self, path: Path, latency_ms: int = 0) -> None:
        self._path = Path(path)
        self._latency_s = latency_ms / 1000
        self.lookups = 0  # número de lecturas al origen (útil para pruebas y métricas)

    def _load(self) -> dict[str, Transaction]:
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
            items = [Transaction.model_validate(item) for item in raw["transactions"]]
        except (OSError, KeyError, TypeError, json.JSONDecodeError, ValidationError) as exc:
            raise DataSourceError(f"No se pudo leer el origen de transacciones: {exc}") from exc
        return {item.transaction_id: item for item in items}

    def get(self, transaction_id: str) -> Transaction | None:
        normalized = normalize_transaction_id(transaction_id)
        self.lookups += 1
        if self._latency_s:
            time.sleep(self._latency_s)
        return self._load().get(normalized)

    def all_ids(self) -> list[str]:
        return sorted(self._load())
