"""Dominio compartido: transacciones sintéticas de remesas y políticas de soporte."""

from cfl.domain.cache import TTLCachedRepository
from cfl.domain.errors import InvalidTransactionIdError
from cfl.domain.models import Transaction, TransactionEvent, normalize_transaction_id
from cfl.domain.policies import PolicyBook
from cfl.domain.repository import JsonTransactionRepository, TransactionRepository

__all__ = [
    "InvalidTransactionIdError",
    "JsonTransactionRepository",
    "PolicyBook",
    "TTLCachedRepository",
    "Transaction",
    "TransactionEvent",
    "TransactionRepository",
    "normalize_transaction_id",
]
