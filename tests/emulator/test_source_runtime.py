"""Actual loopback Firestore transactions; controlled source data, no authority/model calls."""

from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

import pytest

from batchbeacon.guest_service import GuestDenied
from batchbeacon.source_fetch import SourceFetchPolicy
from batchbeacon.source_refresh import RefreshDenied, TrustedRefresh, TrustedRefreshPolicy
from batchbeacon.source_service import SourceCommand, SourceService, StartSourceReview
from batchbeacon.source_state import SourceRuntimeAdmission
from tests.emulator.test_firestore_emulator import pytestmark as pytestmark
from tests.emulator.test_firestore_emulator import runtime as runtime  # noqa: F401
from tests.unit.test_source_runtime import registry_for_environment


def activate(runtime):
    stores = runtime[0][0]
    base = stores.run(
        lambda tx: tx.read({stores.name("environment"): "environment"})[stores.name("environment")]
    )
    registry = registry_for_environment(base)
    admission = SourceRuntimeAdmission(catalog_hash=registry.catalog.digest(), replay_enabled=True)
    for instance in runtime:
        instance[0].source_runtime = admission

    def create(tx):
        name = stores.name("source_registry")
        tx.read({name: "source_registry"})
        tx.write(name, "source_registry", registry, create=True)

    stores.run(create)
    return registry, tuple(SourceService(i[3], i[0]) for i in runtime)


def test_two_clients_forward_only_logical_dedup_and_immediate_expiry(runtime):
    registry, services = activate(runtime)
    guest = runtime[0][2]
    token, session = guest.issue()
    ctx = services[0].context(token)
    start = StartSourceReview(
        catalog_hash=ctx["catalog_hash"], session_reference=ctx["session_reference"]
    )
    value = services[0].start(token, "source-start", start)
    command = SourceCommand(
        catalog_hash=ctx["catalog_hash"], choice="uk-update", expected_revision=1
    )
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [
            pool.submit(service.select, token, value["incident_id"], f"forward{n}", command)
            for n, service in enumerate(services)
        ]
        results = [f.result() for f in futures]
    assert [r["selection_revision"] for r in results] == [2, 2]
    assert services[1].reconcile_start(token, "source-start")["selected_choice"] == "uk-update"
    current = runtime[0][3].read_evidence(token, value["incident_id"])
    assert len(current.state.source_selection.receipts) == 3
    assert not current.current and not current.state.results
    other, _ = guest.issue()
    with pytest.raises(GuestDenied) as denied:
        services[1].read(other, value["incident_id"])
    assert denied.value.status == 404
    runtime[0][5][0] = session.scope.expires_at
    with pytest.raises(GuestDenied) as denied:
        services[1].select(token, value["incident_id"], "expired", command)
    assert denied.value.status == 401


def test_real_transaction_refresh_cas_baseline_unchanged_changed_failure_expiry(runtime):
    registry, _ = activate(runtime)
    stores, _, _, _, _, now = runtime[0]
    notice = registry.catalog.environment(None).notices[0]
    from urllib.parse import urlsplit

    policy = TrustedRefreshPolicy(
        family=notice.dependency.family,
        version=notice.dependency.version,
        expected_hash=notice.dependency.content_hash,
        catalog_hash=registry.catalog.digest(),
        fetch=SourceFetchPolicy(
            url=notice.final_url,
            allowed_hosts=(urlsplit(notice.final_url).hostname,),
            public_addresses=("8.8.8.8",),
        ),
        not_before=now[0] - timedelta(seconds=1),
        expires_at=now[0] + timedelta(hours=1),
        freshness_seconds=30,
    )
    first = TrustedRefresh(stores, policy, clock=lambda: now[0])
    second = TrustedRefresh(runtime[1][0], policy, clock=lambda: now[0])
    pending, _ = first.begin("first")
    with pytest.raises(RefreshDenied, match="pending"):
        second.begin("overlap")
    epochs = []
    for n, digest in enumerate((policy.expected_hash, "c" * 64, None, "c" * 64, "d" * 64)):
        key = "first" if n == 0 else f"next{n}"
        if n:
            first.begin(key)
        result = first.publish(key, digest)
        assert second.publish(key, digest) == result
        epochs.append(result.result.epoch)
    assert epochs == [1, 2, 2, 2, 3]
    intent, _ = first.begin("expired-pending")
    now[0] = intent.deadline
    second.begin("recovery")
    with pytest.raises(RefreshDenied):
        first.publish("expired-pending", "e" * 64)
    assert second.publish("recovery", "d" * 64).result.epoch == 3
    now[0] += timedelta(seconds=30)
    effective = stores.run(lambda tx: stores.source_registry(tx)).resolve(None, now[0])
    assert effective.source_refresh_outcome == "EXPIRED"
