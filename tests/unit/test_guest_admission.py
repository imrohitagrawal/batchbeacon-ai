"""Guest admission preserves configured limits across clients and cold restarts."""

from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

import pytest
from google.api_core import exceptions
from pydantic import ValidationError

from batchbeacon.firestore_store import FirestoreStores
from batchbeacon.guest_admission import (
    GuestAdmissionPolicy,
    GuestAdmissionState,
    reserve_guest,
)
from batchbeacon.guest_service import GuestDenied, GuestService
from tests.unit.domain_fixtures import NOW
from tests.unit.firestore_rpc_fake import client
from tests.unit.test_firestore_store import (
    no_network_or_credentials as no_network_or_credentials,
)
from tests.unit.test_firestore_store import (
    setup as setup,
)


def policy(**changes):
    return GuestAdmissionPolicy(**(dict(max_issued_sessions=3,
        max_sessions_per_window=2, window_seconds=60,
        not_before=NOW, expires_at=NOW + timedelta(days=1)) | changes))


def configure(setup, p=None, opening=0):
    stores, server, guest, *_ = setup
    p = p or policy()
    stores.guest_admission = p
    state = GuestAdmissionState(policy_hash=p.digest(), issued_sessions=opening,
        window_started_at=NOW, window_issued=0)
    server.seed(stores._encode(stores.name("guest_admission"), "guest_admission", state))
    return stores, server, guest, p


def state(stores, server):
    return stores._decode(server.docs[stores.name("guest_admission")], "guest_admission")


def test_window_then_lifetime_do_not_replenish_on_restart(setup):
    stores, server, guest, p = configure(setup)
    guest.issue()
    guest.issue()
    before = server.docs.copy()
    with pytest.raises(GuestDenied):
        guest.issue()
    assert server.docs == before
    setup[5][0] += timedelta(seconds=p.window_seconds)
    fresh = FirestoreStores(client(server), stores.policy, guest.policy,
        stores.evidence_policy, stores.action_policy, clock=guest.clock,
        guest_admission=p)
    cold = GuestService(guest.policy, fresh.guests, guest.objects, clock=guest.clock)
    cold.issue()
    setup[5][0] += timedelta(seconds=p.window_seconds)
    with pytest.raises(GuestDenied):
        cold.issue()
    assert state(stores, server).issued_sessions == 3


@pytest.mark.parametrize("change", [
    {"max_issued_sessions":0}, {"max_issued_sessions":True},
    {"window_seconds":0}, {"window_seconds":float("inf")},
    {"max_sessions_per_window":4}, {"expires_at":NOW},
    {"not_before":NOW.replace(tzinfo=None)}, {"window_seconds":90000},
])
def test_invalid_configuration(change):
    with pytest.raises(ValidationError):
        policy(**change)


def test_missing_corrupt_expired_and_changed_policy_deny_before_provisioning(setup):
    stores, server, guest, p = configure(setup)
    name = stores.name("guest_admission")
    original = server.docs.pop(name)
    with pytest.raises(GuestDenied):
        guest.issue()
    assert len(server.docs) == 1
    server.docs[name] = original
    stores.guest_admission = policy(max_issued_sessions=4)
    with pytest.raises(GuestDenied):
        guest.issue()
    stores.guest_admission = p
    setup[5][0] = p.expires_at
    with pytest.raises(GuestDenied):
        guest.issue()
    assert len(server.docs) == 2
    setup[5][0] = NOW
    server.docs[name].fields["payload"].string_value = "{}"
    with pytest.raises(GuestDenied) as exc:
        guest.issue()
    assert exc.value.status == 503 and len(server.docs) == 2


def test_two_clients_race_for_last_slot(setup):
    stores, server, guest, p = configure(setup, opening=2)
    other = FirestoreStores(client(server), stores.policy, guest.policy,
        stores.evidence_policy, stores.action_policy, clock=guest.clock,
        guest_admission=p)
    cold = GuestService(guest.policy, other.guests, guest.objects, clock=guest.clock)
    def issue(service):
        try:
            service.issue()
            return True
        except GuestDenied:
            return False
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sum(pool.map(issue, (guest, cold))) == 1
    assert state(stores, server).issued_sessions == 3
    assert len([n for n in server.docs if n.rsplit("/",1)[-1].startswith("guest-")]) == 1


def test_clock_rollback_and_malformed_counter_fail_closed():
    p = policy()
    s = GuestAdmissionState(policy_hash=p.digest(), issued_sessions=1,
        window_started_at=NOW, window_issued=1)
    with pytest.raises(GuestDenied):
        reserve_guest(p, s, NOW - timedelta(seconds=1))
    with pytest.raises(ValidationError):
        GuestAdmissionState(policy_hash=p.digest(), issued_sessions=0,
            window_started_at=NOW, window_issued=1)


def test_aborted_commit_does_not_double_charge(setup, monkeypatch):
    stores, server, guest, _ = configure(setup)
    original = stores._call
    failed = [False]
    def invoke(method, *args, **kwargs):
        if method == "commit" and not failed[0]:
            failed[0] = True
            raise exceptions.Aborted("synthetic conflict")
        return original(method, *args, **kwargs)
    monkeypatch.setattr(stores, "_call", invoke)
    guest.issue()
    assert state(stores, server).issued_sessions == 1


def test_lost_commit_ack_retains_consumed_capacity(setup, monkeypatch):
    stores, server, guest, _ = configure(setup, opening=2)
    original = stores._call
    def invoke(method, *args, **kwargs):
        result = original(method, *args, **kwargs)
        if method == "commit":
            raise exceptions.DeadlineExceeded("synthetic lost acknowledgement")
        return result
    monkeypatch.setattr(stores, "_call", invoke)
    with pytest.raises(GuestDenied):
        guest.issue()
    monkeypatch.setattr(stores, "_call", original)
    with pytest.raises(GuestDenied):
        guest.issue()
    assert state(stores, server).issued_sessions == 3


def test_admission_expiring_during_commit_denies_response_without_refund(setup):
    stores, server, guest, p = configure(setup)
    server.after_commit = lambda request: setup[5].__setitem__(0, p.expires_at)
    with pytest.raises(GuestDenied):
        guest.issue()
    assert state(stores, server).issued_sessions == 1


def test_impossible_window_counter_cannot_be_reset():
    p = policy(max_issued_sessions=10)
    stored = GuestAdmissionState(policy_hash=p.digest(), issued_sessions=3,
        window_started_at=NOW, window_issued=3)
    with pytest.raises(GuestDenied):
        reserve_guest(p, stored, NOW + timedelta(seconds=60))


def test_explicit_no_lifetime_cap_preserves_counts_rate_and_expiry(setup):
    stores, server, guest, p = configure(setup, policy(max_issued_sessions=None), opening=22)
    guest.issue()
    guest.issue()
    with pytest.raises(GuestDenied, match="guest_creation_rate_limited"):
        guest.issue()
    assert state(stores, server).issued_sessions == 24
    setup[5][0] += timedelta(seconds=p.window_seconds)
    fresh = FirestoreStores(client(server), stores.policy, guest.policy,
        stores.evidence_policy, stores.action_policy, clock=guest.clock,
        guest_admission=p)
    cold = GuestService(guest.policy, fresh.guests, guest.objects, clock=guest.clock)
    cold.issue()
    assert state(stores, server).issued_sessions == 25
    setup[5][0] = p.expires_at
    with pytest.raises(GuestDenied):
        cold.issue()
    assert state(stores, server).issued_sessions == 25
    with pytest.raises(GuestDenied, match="demo_guest_capacity_unavailable"):
        reserve_guest(p, state(stores, server), p.expires_at)


def test_no_lifetime_cap_requires_explicit_null_and_valid_other_limits():
    raw = policy().model_dump()
    del raw["max_issued_sessions"]
    with pytest.raises(ValidationError):
        GuestAdmissionPolicy(**raw)
    unlimited = policy(max_issued_sessions=None)
    assert GuestAdmissionPolicy.model_validate_json(unlimited.model_dump_json()) == unlimited
    assert unlimited.digest() != policy().digest()
    for field in ("max_sessions_per_window", "window_seconds"):
        for value in (None, 0, -1, True, "4", float("inf")):
            with pytest.raises(ValidationError):
                policy(max_issued_sessions=None, **{field: value})


def test_uncapped_policy_migration_requires_bound_state_and_preserves_history(setup):
    stores, server, guest, old = configure(setup, opening=22)
    new = policy(max_issued_sessions=None)
    stores.guest_admission = new
    with pytest.raises(GuestDenied):
        guest.issue()

    previous = state(stores, server)
    migrated = GuestAdmissionState(**(previous.model_dump() | {"policy_hash": new.digest()}))
    server.seed(stores._encode(stores.name("guest_admission"), "guest_admission", migrated))
    guest.issue()
    assert state(stores, server).issued_sessions == 23
    stores.guest_admission = old
    with pytest.raises(GuestDenied):
        guest.issue()


def test_uncapped_clients_still_race_for_last_window_slot(setup):
    stores, server, guest, p = configure(setup, policy(max_issued_sessions=None), opening=22)
    guest.issue()
    other = FirestoreStores(client(server), stores.policy, guest.policy,
        stores.evidence_policy, stores.action_policy, clock=guest.clock,
        guest_admission=p)
    cold = GuestService(guest.policy, other.guests, guest.objects, clock=guest.clock)
    def issue(service):
        try:
            service.issue()
            return True
        except GuestDenied:
            return False
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sum(pool.map(issue, (guest, cold))) == 1
    assert state(stores, server).issued_sessions == 24


def test_increased_window_preserves_sessions_counts_and_exact_boundary(setup):
    old = policy(max_issued_sessions=None, max_sessions_per_window=4)
    stores, server, guest, _ = configure(setup, old, opening=22)
    issued = [guest.issue() for _ in range(4)]
    previous = state(stores, server)
    new = policy(max_issued_sessions=None, max_sessions_per_window=30)
    migrated = GuestAdmissionState(**(previous.model_dump() | {"policy_hash": new.digest()}))
    assert migrated.model_dump(exclude={"policy_hash"}) == previous.model_dump(
        exclude={"policy_hash"})
    server.seed(stores._encode(stores.name("guest_admission"), "guest_admission", migrated))
    fresh = FirestoreStores(client(server), stores.policy, guest.policy,
        stores.evidence_policy, stores.action_policy, clock=guest.clock,
        guest_admission=new)
    cold = GuestService(guest.policy, fresh.guests, guest.objects, clock=guest.clock)
    assert cold.resolve(issued[0][0]) == issued[0][1]
    for _ in range(26):
        cold.issue()
    assert state(fresh, server).window_issued == 30
    assert state(fresh, server).issued_sessions == 52
    setup[5][0] = NOW + timedelta(seconds=59, microseconds=999999)
    with pytest.raises(GuestDenied, match="guest_creation_rate_limited"):
        cold.issue()
    setup[5][0] = NOW + timedelta(seconds=60)
    cold.issue()
    assert state(fresh, server).window_issued == 1
    assert state(fresh, server).issued_sessions == 53
    assert cold.resolve(issued[0][0]) == issued[0][1]
