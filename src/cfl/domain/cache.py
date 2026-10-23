"""Caché en memoria con TTL para el repositorio de transacciones (Proyecto 4, ISSUE P4-001)."""

from __future__ import annotations

import threading
import time
from collections import OrderedDict
from dataclasses import dataclass
from typing import Callable

from cfl.domain.models import Transaction, normalize_transaction_id
from cfl.domain.repository import TransactionRepository


@dataclass
class _Entry:
    value: Transaction | None  # None = caché negativa ("no encontrada")
    expires_at: float


class TTLCachedRepository:
    """Decorador de TransactionRepository con TTL, caché negativa, límite de tamaño y métricas.

    - Los IDs inválidos lanzan InvalidTransactionIdError antes de tocar la caché o el origen.
    - Los errores del origen se propagan y no se cachean.
    """

    def __init__(
        self,
        inner: TransactionRepository,
        ttl_seconds: float = 30.0,
        negative_ttl_seconds: float = 10.0,
        max_entries: int = 1000,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds debe ser > 0; para desactivar la caché no envuelvas el repositorio.")
        if max_entries < 1:
            raise ValueError("max_entries debe ser >= 1")
        self.inner = inner
        self.ttl = ttl_seconds
        self.negative_ttl = max(0.0, negative_ttl_seconds)
        self.max_entries = max_entries
        self._clock = clock
        self._entries: OrderedDict[str, _Entry] = OrderedDict()
        self._lock = threading.Lock()
        self.hits = self.misses = self.expired = self.evicted = 0

    def get(self, transaction_id: str) -> Transaction | None:
        key = normalize_transaction_id(transaction_id)
        now = self._clock()
        with self._lock:
            entry = self._entries.get(key)
            if entry is not None:
                if entry.expires_at > now:
                    self.hits += 1
                    return entry.value
                del self._entries[key]
                self.expired += 1
            self.misses += 1
        # La lectura al origen ocurre fuera del lock para no serializar consultas a IDs distintos.
        value = self.inner.get(key)
        ttl = self.ttl if value is not None else self.negative_ttl
        if ttl > 0:
            with self._lock:
                self._entries[key] = _Entry(value, self._clock() + ttl)
                self._entries.move_to_end(key)
                while len(self._entries) > self.max_entries:
                    self._entries.popitem(last=False)
                    self.evicted += 1
        return value

    def invalidate(self, transaction_id: str | None = None) -> None:
        with self._lock:
            if transaction_id is None:
                self._entries.clear()
            else:
                self._entries.pop(normalize_transaction_id(transaction_id), None)

    def stats(self) -> dict[str, float | int]:
        with self._lock:
            return {
                "hits": self.hits,
                "misses": self.misses,
                "expired": self.expired,
                "evicted": self.evicted,
                "size": len(self._entries),
                "ttl_seconds": self.ttl,
                "negative_ttl_seconds": self.negative_ttl,
            }
