import json

import pytest

from cfl.domain import InvalidTransactionIdError, JsonTransactionRepository, normalize_transaction_id
from cfl.domain.errors import DataSourceError


def test_dataset_is_marked_synthetic(repository):
    raw = json.loads(repository._path.read_text(encoding="utf-8"))
    assert raw["dataset"]["synthetic"] is True
    assert len(repository.all_ids()) == 12


@pytest.mark.parametrize("raw", ["RMX-2026-000101", " rmx-2026-000101 ", "Rmx-2026-000101"])
def test_normalize_accepts_variants(raw):
    assert normalize_transaction_id(raw) == "RMX-2026-000101"


@pytest.mark.parametrize("raw", ["", "RMX-12", "RMX-2026-00010", "TX-2026-000101", "RMX-2026-000101; DROP", 101, None])
def test_normalize_rejects_invalid(raw):
    with pytest.raises(InvalidTransactionIdError):
        normalize_transaction_id(raw)


def test_get_existing_and_missing(repository):
    tx = repository.get("rmx-2026-000104")
    assert tx is not None and tx.status == "ON_HOLD" and tx.hold_reason == "COMPLIANCE_REVIEW"
    assert repository.get("RMX-2026-999999") is None
    assert repository.lookups == 2


def test_sender_and_beneficiary_are_masked(repository):
    for tx_id in repository.all_ids():
        tx = repository.get(tx_id)
        assert "****" in tx.sender_ref and "****" in tx.beneficiary_ref


def test_corrupt_source_raises_data_source_error(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    with pytest.raises(DataSourceError):
        JsonTransactionRepository(bad).get("RMX-2026-000101")


def test_policies_markdown(policies):
    md = policies.to_markdown()
    assert "Políticas sintéticas" in md and "`retenciones`" in md
    assert policies.get("inexistente") is None
