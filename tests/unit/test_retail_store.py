"""Owned durable queue through installed Firestore SDK/fake RPC; no cloud proof."""

from datetime import timedelta

import pytest
from google.api_core import exceptions

from batchbeacon.action_service import ActionConfirmation, ActionService
from batchbeacon.contracts import ActionType
from batchbeacon.evidence_service import EvidenceService, replace
from batchbeacon.firestore_store import FirestoreStores
from batchbeacon.guest_service import GuestDenied, GuestService
from batchbeacon.retail_contracts import QueueCategory
from batchbeacon.retail_projection import QueueFilter, RetailProjector, RetailReadPolicy
from tests.unit.firestore_rpc_fake import client
from tests.unit.test_firestore_store import env as env  # noqa: F401
from tests.unit.test_firestore_store import (
    extract,
    owned,
    publish,
    saved,
)
from tests.unit.test_firestore_store import (
    no_network_or_credentials as no_network_or_credentials,  # noqa: F401
)
from tests.unit.test_firestore_store import setup as setup  # noqa: F401
from tests.unit.test_reviewed_extraction import acquire, build_reviewed, view


@pytest.fixture
def enabled(setup, env):
    stores, server, guest, evidence, actions, now = setup
    server.clock = lambda: now[0]
    projector = RetailProjector(actions, env[0].policy, RetailReadPolicy())
    stores.enable_retail(projector)
    return setup


def cold(setup, env, *, enabled=True):
    stores, server, guest, _, _, now = setup
    other = FirestoreStores(client(server), stores.policy, stores.guest_policy,
        stores.evidence_policy, stores.action_policy, clock=lambda: now[0])
    other_guest = GuestService(guest.policy, other.guests, guest.objects, clock=lambda: now[0])
    evidence = EvidenceService(other_guest, other.evidence, stores.evidence_policy)
    actions = ActionService(evidence, other.actions, stores.action_policy)
    if enabled:
        other.enable_retail(RetailProjector(actions, env[0].policy, RetailReadPolicy()))
    return other, other_guest


def summary(setup, session, incident):
    return saved(setup, "retail", session.capability_hash, incident.id)


@pytest.fixture
def connected(setup, env):
    def configure(stores, actions, shared):
        stores.enable_retail(RetailProjector(actions, shared.policy, RetailReadPolicy()))
    return build_reviewed(setup, env, (0,), configure=configure)


def test_adk_completion_action_correction_and_cold_queue(connected):
    c = connected
    stores, server, guest, _, _, now = c[3]
    assert acquire(c).state == "COMPLETE"
    incident = guest.incident(c[2], c[1].incident_id)
    stored = summary(c[3], c[6], incident)
    assert stored.completion is not None
    assert stored.projection.acquisition.completion is None
    assert stores.retail.read(c[2]).snapshot.rows[0].current
    target = c[8].prepare(c[2], incident.id, ActionType.SIMULATED_HOLD)
    c[8].confirm(c[2], incident.id, "hold", ActionConfirmation(
        target=target, explicit_confirmation=True))
    assert stores.retail.read(c[2]).snapshot.rows[0].category == QueueCategory.ACTION_RECORDED
    original = view(c).observation
    from tests.unit.domain_fixtures import known
    now[0] += timedelta(seconds=1)
    c[7].correct(c[2], incident.id, "fix", original.revision, "LOT",
                 known("232511", evidence=original.captures[0]))
    changed = summary(c[3], c[6], incident)
    assert changed.completion == stored.completion
    assert changed.projection.acquisition.original_observation == \
        stored.projection.acquisition.original_observation
    assert not stores.retail.read(c[2]).snapshot.rows[0].current
    binding = c[7].verification_binding(c[2], incident.id)
    c[0].shared.reserve_verification(c[6].capability_hash, incident.id, "again", binding)
    c[7].publish_verification(c[2], incident.id, "again", binding)
    other = FirestoreStores(client(server), stores.policy, stores.guest_policy,
        stores.evidence_policy, stores.action_policy, clock=lambda: now[0])
    other_guest = GuestService(guest.policy, other.guests, guest.objects, clock=lambda: now[0])
    evidence = EvidenceService(other_guest, other.evidence, stores.evidence_policy,
                               identities=c[7].identities)
    actions = ActionService(evidence, other.actions, stores.action_policy)
    other.enable_retail(RetailProjector(actions, c[0].shared.policy, RetailReadPolicy()))
    server.calls.clear()
    result = other.retail.read(c[2])
    assert result.snapshot.rows[0].current
    assert result.snapshot.rows[0].category == QueueCategory.HUMAN_REVIEW
    assert result.contexts[0].action_historical
    reads = [r for m, r, _ in server.calls if m == "batch_get_documents"]
    assert len(reads) == 3 and sum(len(r.documents) for r in reads) == 5
    assert all(not r.writes for m, r, _ in server.calls if m == "commit")


@pytest.mark.parametrize("mutation", ["missing", "late", "edited"])
def test_actual_completion_metadata_controls_currentness(connected, mutation):
    c = connected
    acquire(c)
    stores, server, *_ = c[3]
    usage = saved(c[3], "usage", c[6].capability_hash)
    run = usage.runs[-1]
    name = stores.name("completion", run.id)
    if mutation == "missing":
        del server.docs[name]
        with pytest.raises(GuestDenied):
            stores.retail.read(c[2])
    else:
        if mutation == "late":
            server.docs[name].create_time = run.deadline
            server.docs[name].update_time = run.deadline
        else:
            server.docs[name].update_time += timedelta(seconds=1)
        row = stores.retail.read(c[2]).snapshot.rows[0]
        assert not row.current and row.category == QueueCategory.RENEWED_REVIEW


def test_new_shop_and_incident_are_atomic_and_cold_readable(enabled, env):
    stores, server, guest, *_ = enabled
    token, session = guest.issue()
    assert stores.retail.read(token).snapshot.rows == ()
    incident = guest.create_incident(token, "first")
    commits = [r for method, r, _ in server.calls if method == "commit" and r.writes]
    assert len(commits[-1].writes) == 5  # guest, usage, evidence, actions, summary
    other, _ = cold(enabled, env)
    server.calls.clear()
    view = other.retail.read(token)
    assert [r.incident_id for r in view.snapshot.rows] == [incident.id]
    assert view.new_verification.state == "UNKNOWN"
    assert view.saved_evidence.state == "AVAILABLE"
    assert view.snapshot.rows[0].category == "IN_PROGRESS"
    assert all(not r.writes for method, r, _ in server.calls if method == "commit")
    names = [name for method, r, _ in server.calls if method == "batch_get_documents"
             for name in r.documents]
    assert len(names) == 4
    assert not any("/sdk_tests/evidence-" in n or "/sdk_tests/actions-" in n for n in names)
    assert summary(enabled, session, incident).projection.material.sequence == 1


def test_all_basic_writers_update_summary_and_reads_do_not(enabled, env):
    stores, server, guest, evidence, actions, now = enabled
    token, session, incident = owned(enabled)
    now[0] += timedelta(seconds=1)
    extract(enabled, token, incident)
    extracted = summary(enabled, session, incident)
    assert extracted.projection.observation_count == 1
    now[0] += timedelta(seconds=1)
    publish(enabled, env, token, session, incident)
    verified = summary(enabled, session, incident)
    assert verified.projection.result_count == 1
    assert verified.projection.material.sequence > extracted.projection.material.sequence
    confirmation = ActionConfirmation(target=actions.prepare(token, incident.id,
        ActionType.SIMULATED_HOLD), explicit_confirmation=True)
    action = actions.confirm(token, incident.id, "confirm", confirmation)
    recorded = summary(enabled, session, incident)
    assert recorded.projection.latest_action == action.action
    assert stores.retail.read(token).snapshot.rows[0].category == QueueCategory.ACTION_RECORDED
    before = {n: type(d).serialize(d) for n, d in server.docs.items()}
    actions.confirm(token, incident.id, "confirm", confirmation)
    stores.retail.read(token, selected_filter=QueueFilter.SIMULATED_HOLDS)
    assert before == {n: type(d).serialize(d) for n, d in server.docs.items()}


def test_unconfigured_writer_and_legacy_guest_cannot_bypass_enrollment(enabled, env):
    token, _, _ = owned(enabled)
    _, legacy_guest = cold(enabled, env, enabled=False)
    with pytest.raises(GuestDenied):
        legacy_guest.create_incident(token, "bypass")


def test_missing_summary_is_unavailable_never_repaired(enabled):
    stores, server, *_ = enabled
    token, session, incident = owned(enabled)
    del server.docs[stores.name("retail", session.capability_hash, incident.id)]
    server.calls.clear()
    with pytest.raises(GuestDenied):
        stores.retail.read(token)
    assert all(not r.writes for m, r, _ in server.calls if m == "commit")


def test_summary_bound_failure_aborts_domain_creation(enabled):
    stores, server, guest, *_ = enabled
    stores.retail.projector.policy = replace(stores.retail.projector.policy, projection_bytes=1)
    token, _ = guest.issue()
    before = {n: type(d).serialize(d) for n, d in server.docs.items()}
    with pytest.raises(GuestDenied):
        guest.create_incident(token, "oversized")
    assert before == {n: type(d).serialize(d) for n, d in server.docs.items()}


@pytest.mark.parametrize("when", ["before", "stream", "ack"])
def test_expiry_never_returns_queue(enabled, when):
    stores, server, _, _, _, now = enabled
    token, session, _ = owned(enabled)
    def expire(value):
        now[0] = session.scope.expires_at
        return value
    if when == "before":
        expire(None)
    elif when == "stream":
        server.read_transform = expire
    else:
        server.after_commit = expire
    with pytest.raises(GuestDenied):
        stores.retail.read(token)


def test_foreign_summary_and_unknown_commit_deny(enabled):
    stores, server, guest, *_ = enabled
    token, session, incident = owned(enabled)
    other_token, other_session = guest.issue()
    other_incident = guest.create_incident(other_token, "second")
    foreign = summary(enabled, other_session, other_incident)
    server.seed(stores._encode(stores.name("retail", session.capability_hash, incident.id),
                              "retail", foreign))
    with pytest.raises(GuestDenied):
        stores.retail.read(token)
    def lost(_):
        raise exceptions.DeadlineExceeded("unknown acknowledgement")
    server.after_commit = lost
    with pytest.raises(GuestDenied):
        stores.retail.read(other_token)


def test_source_semantic_change_is_read_without_summary_write(enabled, env):
    stores, server, _, _, _, now = enabled
    token, session, incident = owned(enabled)
    extract(enabled, token, incident)
    publish(enabled, env, token, session, incident)
    assert stores.retail.read(token).snapshot.rows[0].current
    before = summary(enabled, session, incident)
    environment = saved(enabled, "environment")
    changed = replace(environment, notices=tuple(replace(n, review=None)
                                                for n in environment.notices))
    server.seed(stores._encode(stores.name("environment"), "environment", changed))
    result = stores.retail.read(token)
    assert not result.snapshot.rows[0].current
    assert result.snapshot.rows[0].category == QueueCategory.RENEWED_REVIEW
    assert summary(enabled, session, incident) == before
