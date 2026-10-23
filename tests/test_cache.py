"""Pruebas del Proyecto 4: caché TTL (ISSUE P4-001)."""

from __future__ import annotations

import threading

import pytest

from cfl.assistant import SupportAssistant
from cfl.config import DATA_DIR, Settings
from cfl.domain import InvalidTransactionIdError, JsonTransactionRepository
from cfl.domain.cache import TTLCachedRepository
from cfl.domain.errors import DataSourceError
from cfl.providers.mock import MockProvider
from cfl.tools import build_default_toolbox


class FakeClock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


@pytest.fixture
def clock():
    return FakeClock()


@pytest.fixture
def source():
    return JsonTransactionRepository(DATA_DIR / "transactions.json")


def test_hit_after_first_lookup_with_normalized_key(source, clock):
    repo = TTLCachedRepository(source, ttl_seconds=30, clock=clock)
    first = repo.get("rmx-2026-000104")
    second = repo.get(" RMX-2026-000104 ")
    assert first == second and source.lookups == 1
    assert repo.stats()["hits"] == 1 and repo.stats()["misses"] == 1


def test_expiration_goes_back_to_source(source, clock):
    repo = TTLCachedRepository(source, ttl_seconds=30, clock=clock)
    repo.get("RMX-2026-000101")
    clock.advance(29.9)
    repo.get("RMX-2026-000101")
    assert source.lookups == 1
    clock.advance(0.2)
    repo.get("RMX-2026-000101")
    assert source.lookups == 2 and repo.stats()["expired"] == 1


def test_negative_cache_has_shorter_ttl(source, clock):
    repo = TTLCachedRepository(source, ttl_seconds=30, negative_ttl_seconds=10, clock=clock)
    assert repo.get("RMX-2026-999999") is None
    assert repo.get("RMX-2026-999999") is None
    assert source.lookups == 1
    clock.advance(10.1)
    repo.get("RMX-2026-999999")
    assert source.lookups == 2


def test_negative_cache_can_be_disabled(source, clock):
    repo = TTLCachedRepository(source, ttl_seconds=30, negative_ttl_seconds=0, clock=clock)
    repo.get("RMX-2026-999999")
    repo.get("RMX-2026-999999")
    assert source.lookups == 2


def test_invalid_ids_never_reach_cache_or_source(source, clock):
    repo = TTLCachedRepository(source, ttl_seconds=30, clock=clock)
    with pytest.raises(InvalidTransactionIdError):
        repo.get("RMX-12")
    assert source.lookups == 0 and repo.stats()["size"] == 0


def test_source_errors_are_not_cached(clock):
    class Flaky:
        def __init__(self):
            self.calls = 0

        def get(self, transaction_id):
            self.calls += 1
            if self.calls == 1:
                raise DataSourceError("caído")
            return None

    flaky = Flaky()
    repo = TTLCachedRepository(flaky, ttl_seconds=30, clock=clock)
    with pytest.raises(DataSourceError):
        repo.get("RMX-2026-000101")
    assert repo.get("RMX-2026-000101") is None and flaky.calls == 2


def test_max_entries_evicts_oldest(source, clock):
    repo = TTLCachedRepository(source, ttl_seconds=30, max_entries=2, clock=clock)
    for tx in ("RMX-2026-000101", "RMX-2026-000102", "RMX-2026-000103"):
        repo.get(tx)
    assert repo.stats()["size"] == 2 and repo.stats()["evicted"] == 1
    repo.get("RMX-2026-000101")  # fue expulsada: vuelve al origen
    assert source.lookups == 4


def test_invalidate(source, clock):
    repo = TTLCachedRepository(source, ttl_seconds=30, clock=clock)
    repo.get("RMX-2026-000101")
    repo.get("RMX-2026-000102")
    repo.invalidate("rmx-2026-000101")
    assert repo.stats()["size"] == 1
    repo.invalidate()
    assert repo.stats()["size"] == 0


@pytest.mark.parametrize("kwargs", [{"ttl_seconds": 0}, {"ttl_seconds": -1}, {"ttl_seconds": 5, "max_entries": 0}])
def test_invalid_configuration(source, kwargs):
    with pytest.raises(ValueError):
        TTLCachedRepository(source, **kwargs)


def test_thread_safety_under_concurrency(source):
    repo = TTLCachedRepository(source, ttl_seconds=30)
    ids = [f"RMX-2026-0001{n:02d}" for n in range(1, 13)]
    errors: list[Exception] = []

    def worker():
        try:
            for _ in range(20):
                for tx in ids:
                    assert repo.get(tx).transaction_id == tx
        except Exception as exc:  # pragma: no cover - solo si falla
            errors.append(exc)

    threads = [threading.Thread(target=worker) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    stats = repo.stats()
    assert not errors
    assert stats["hits"] + stats["misses"] == 8 * 20 * 12
    assert stats["size"] == 12


# --- Integración con la configuración y el asistente -----------------------------------

def test_default_toolbox_uses_cache_and_ttl_zero_disables_it():
    cached = build_default_toolbox(Settings.from_env(env={}))
    assert isinstance(cached.repository, TTLCachedRepository) and cached.repository.ttl == 30
    plain = build_default_toolbox(Settings.from_env(env={"CFL_CACHE_TTL_SECONDS": "0"}))
    assert isinstance(plain.repository, JsonTransactionRepository)


def test_acceptance_baseline_scenario_goes_from_6_to_2_lookups():
    """Criterio de aceptación del ISSUE: mismo escenario que la línea base."""
    queries = ["historial de RMX-2026-000104", "¿Cuál es el estado de RMX-2026-000104?",
               "¿Cuál es el estado de RMX-2026-000104?", "Estado de RMX-2026-999999", "Estado de RMX-2026-999999"]

    def lookups(env):
        toolbox = build_default_toolbox(Settings.from_env(env=env))
        for q in queries:
            SupportAssistant(MockProvider(), toolbox).run(q)
        return getattr(toolbox.repository, "inner", toolbox.repository).lookups

    assert lookups({"CFL_CACHE_TTL_SECONDS": "0"}) == 6
    assert lookups({"CFL_CACHE_TTL_SECONDS": "30"}) == 2
