"""Reader-first regression gates; installed SDK + controlled RPC, never live sources."""
import json
from datetime import timedelta

import pytest
from pydantic import ValidationError

from batchbeacon.action_service import ActionConfirmation
from batchbeacon.contracts import ActionType, LiveStatus, SourceMode
from batchbeacon.evidence_service import EvidenceState, replace
from batchbeacon.guest_service import GuestDenied
from batchbeacon.retail_contracts import QueueCategory
from batchbeacon.retail_projection import RetailProjector, RetailReadPolicy
from batchbeacon.source_state import (
    FamilyRefresh,
    SelectionReceipt,
    SourceCatalog,
    SourceChoice,
    SourceRegistry,
    SourceRuntimeAdmission,
    SourceSelection,
)
from tests.unit.domain_fixtures import NOW, known
from tests.unit.test_firestore_store import (
    env as env,
)
from tests.unit.test_firestore_store import (
    extract,
    owned,
    publish,
    saved,
)
from tests.unit.test_firestore_store import (
    no_network_or_credentials as no_network_or_credentials,
)
from tests.unit.test_firestore_store import (
    setup as setup,
)


def registry_for(setup):
    base = saved(setup, "environment")
    catalog = SourceCatalog(default_choice="original", choices=(
        SourceChoice(key="original", environment=base),))
    return SourceRegistry(catalog=catalog, families=tuple(FamilyRefresh(
        family=n.dependency.family, epoch=n.dependency.epoch, status="NEVER_REQUESTED")
        for n in base.notices))


def enable(setup, registry):
    stores, server, *_ = setup
    stores.source_runtime = SourceRuntimeAdmission(catalog_hash=registry.catalog.digest())
    server.seed(stores._encode(stores.name("source_registry"), "source_registry", registry))


def refresh(setup, status, *, epoch=None):
    registry = saved(setup, "source_registry")
    family = registry.families[0]
    current = registry.catalog.environment(None).notices[0].dependency
    family = replace(family, epoch=epoch or family.epoch, status=status,
        checked_at=setup[5][0], valid_until=setup[5][0] + timedelta(seconds=30),
        observed_hash=(current.content_hash if status == "UNCHANGED" else "c" * 64)
            if status in {"UNCHANGED", "CHANGED"} else None)
    updated = replace(registry, families=(family,))
    setup[1].seed(setup[0]._encode(setup[0].name("source_registry"), "source_registry", updated))
    return updated


def test_legacy_evidence_serializes_identically_and_no_registry_read_without_admission(setup):
    token, session, incident = owned(setup)
    stores, server, _, evidence, *_ = setup
    raw = server.docs[stores.name("evidence", session.capability_hash, incident.id)]
    old = json.loads(raw.fields["payload"].string_value)
    assert "source_selection" not in old
    state = EvidenceState.model_validate_json(json.dumps(old))
    assert state.source_selection is None and json.loads(state.model_dump_json()) == old
    server.calls.clear()
    evidence.read_evidence(token, incident.id)
    assert not any("source_registry" in name for method, request, _ in server.calls
                   if method == "batch_get_documents" for name in request.documents)


def test_required_registry_absence_and_wrong_catalog_deny_instead_of_historical_fallback(setup):
    token, _, incident = owned(setup)
    registry = registry_for(setup)
    setup[0].source_runtime = SourceRuntimeAdmission(catalog_hash=registry.catalog.digest())
    with pytest.raises(GuestDenied):
        setup[3].read_evidence(token, incident.id)
    enable(setup, registry)
    assert setup[3].read_evidence(token, incident.id).state.source_selection is None
    setup[0].source_runtime = SourceRuntimeAdmission(catalog_hash="0" * 64)
    with pytest.raises(GuestDenied):
        setup[3].read_evidence(token, incident.id)


@pytest.mark.parametrize("status", ["UNCHANGED", "CHANGED", "UNAVAILABLE"])
@pytest.mark.parametrize("negative", [False, True])
def test_refresh_invalidates_old_positive_and_negative_and_queue_without_sweep(setup, env,
                                                                             status, negative):
    stores, _, guest, evidence, actions, now = setup
    stores.enable_retail(RetailProjector(actions, env[0].policy, RetailReadPolicy()))
    token, session, incident = owned(setup)
    envelope = extract(setup, token, incident)
    if negative:
        evidence.correct(token, incident.id, "negative", 1, "LOT",
                         known("unlisted-lot", evidence=envelope.captures[0]))
    publish(setup, env, token, session, incident)
    before = evidence.read_evidence(token, incident.id)
    assert before.current
    if not negative:
        target = actions.prepare(token, incident.id, ActionType.SIMULATED_HOLD)
        action = actions.confirm(token, incident.id, "hold", ActionConfirmation(
            target=target, explicit_confirmation=True))
    counters = saved(setup, "usage", session.capability_hash)
    summaries = saved(setup, "retail", session.capability_hash, incident.id)
    enable(setup, registry_for(setup))
    assert evidence.read_evidence(token, incident.id).current
    refresh(setup, status, epoch=2 if status == "CHANGED" else 1)
    view = evidence.read_evidence(token, incident.id)
    assert not view.current and view.result == before.result and not view.hold_eligible
    row = stores.retail.read(token).snapshot.rows[0]
    assert not row.current and row.category == QueueCategory.RENEWED_REVIEW
    assert saved(setup, "retail", session.capability_hash, incident.id) == summaries
    assert saved(setup, "usage", session.capability_hash) == counters
    if not negative:
        assert actions.get_action(token, incident.id, action.action.id).requires_renewed_review
        reconciled = actions.confirm(token, incident.id, "late", ActionConfirmation(
            target=target, explicit_confirmation=True))
        assert reconciled.action.id == action.action.id and not reconciled.current
        assert len(actions.list_actions(token, incident.id)) == 1
    now[0] += timedelta(seconds=30)
    snapshot = []
    stores.evidence.transact(session.capability_hash, incident.id,
        lambda s: snapshot.append(s) or s.state)
    assert snapshot[0].environment.context.mode == SourceMode.LIVE
    assert snapshot[0].environment.context.live_status == LiveStatus.EXPIRED


def test_freshness_crossing_after_snapshot_is_expired_at_consumer_time(setup):
    registry = registry_for(setup)
    enable(setup, registry)
    registry = refresh(setup, "UNCHANGED")
    environment = registry.resolve(None, NOW)
    assert environment.at(NOW, 1).live_status == LiveStatus.VALIDATED
    assert environment.at(NOW + timedelta(seconds=30), 1).live_status == LiveStatus.EXPIRED


def test_unknown_selection_cannot_fallback_with_or_without_registry(setup):
    token, session, incident = owned(setup)
    registry = registry_for(setup)
    selection = SourceSelection(catalog_hash=registry.catalog.digest(), choice="missing",
        environment_hash="b" * 64, revision=1, selected_at=NOW,
        receipts=(SelectionReceipt(key="choose", payload_hash="c" * 64, revision=1),))
    state = saved(setup, "evidence", session.capability_hash, incident.id)
    state = replace(state, source_selection=selection)
    setup[1].seed(setup[0]._encode(setup[0].name("evidence", session.capability_hash,
        incident.id), "evidence", state))
    for enabled in (False, True):
        if enabled:
            enable(setup, registry)
        with pytest.raises(GuestDenied):
            setup[3].read_evidence(token, incident.id)


@pytest.mark.parametrize("values", [
    {"status": "UNCHANGED"}, {"status": "UNAVAILABLE", "observed_hash": "a" * 64},
    {"checked_at": NOW}, {"epoch": 0}, {"epoch": True},
])
def test_invalid_refresh_state_fails_closed(values):
    with pytest.raises(ValidationError):
        FamilyRefresh.model_validate(
            {"family": "family", "epoch": 1, "status": "NEVER_REQUESTED"} | values)



def test_registry_cannot_omit_family_or_roll_epoch_backward(setup):
    registry = registry_for(setup)
    with pytest.raises(ValidationError):
        replace(registry, families=())
    base = registry.catalog.environment(None)
    later = replace(base, notices=(replace(base.notices[0], dependency=replace(
        base.notices[0].dependency, epoch=2)),), context=replace(base.context,
        current_sources=(replace(base.notices[0].dependency, epoch=2),)))
    catalog = replace(registry.catalog, choices=(SourceChoice(key="original", environment=later),))
    with pytest.raises(ValidationError):
        replace(registry, catalog=catalog)


def test_source_deadline_is_bound_before_callback_and_survives_clock_crossing(setup):
    token, session, incident = owned(setup)
    enable(setup, registry_for(setup))
    refresh(setup, "UNCHANGED")
    before = setup[1].versions.copy()
    def slow_callback(snapshot):
        assert snapshot.environment.context.live_status == LiveStatus.VALIDATED
        setup[5][0] += timedelta(seconds=30)
        return snapshot.state
    with pytest.raises(OSError):
        setup[0].evidence.transact(session.capability_hash, incident.id, slow_callback)
    assert setup[1].versions == before
    # Already-expired evidence stays readable for renewed review; no past cutoff.
    assert setup[3].read_evidence(token, incident.id).state.session_id == session.scope.session_id


def test_inline_selection_and_atomic_summary_roundtrip_before_writers(setup, env):
    stores, _, _, _, actions, _ = setup
    stores.enable_retail(RetailProjector(actions, env[0].policy, RetailReadPolicy()))
    registry = registry_for(setup)
    enable(setup, registry)
    token, session, incident = owned(setup)
    selection = SourceSelection(catalog_hash=registry.catalog.digest(), choice="original",
        environment_hash=registry.catalog.environment(None).digest(), revision=1, selected_at=NOW,
        receipts=(SelectionReceipt(key="choose", payload_hash="c" * 64, revision=1),))
    stores.evidence.transact(session.capability_hash, incident.id,
        lambda snapshot: replace(snapshot.state, source_selection=selection))
    assert saved(setup, "evidence", session.capability_hash,
                 incident.id).source_selection == selection
    assert saved(setup, "retail", session.capability_hash,
                 incident.id).projection.source_selection == selection
    assert stores.retail.read(token).snapshot.rows[0].incident_id == incident.id


def test_metadata_only_unreviewed_notice_can_never_authorize_or_clear(setup):
    from batchbeacon.domain.verifier import verify
    from tests.unit.domain_fixtures import observation
    base = saved(setup, "environment")
    metadata = replace(base.notices[0], products=(), review=None, interpretation_complete=False)
    result = verify(observation(), (metadata,), base.at(NOW, 1), base.verifier_policy)
    assert result.verdict.value == "REVIEW_REQUIRED" and not result.hold_eligible
    with pytest.raises(ValidationError):
        replace(metadata, review=base.notices[0].review)
    with pytest.raises(ValidationError):
        replace(metadata, interpretation_complete=True)


def test_refresh_pending_retains_last_known_hash_and_unique_operation_owner():
    state = FamilyRefresh(family="synthetic-family", epoch=2, status="CHANGED",
        observed_hash="a" * 64, last_known_hash="a" * 64, checked_at=NOW,
        valid_until=NOW + timedelta(seconds=60))
    pending = replace(state, status="UNAVAILABLE", observed_hash=None, pending_refresh="b" * 64)
    assert pending.last_known_hash == state.observed_hash and pending.epoch == 2
    assert replace(pending, pending_refresh=None).last_known_hash == state.observed_hash
    with pytest.raises(ValidationError):
        replace(pending, last_known_hash=None)
    with pytest.raises(ValidationError):
        replace(state, pending_refresh="b" * 64)
    with pytest.raises(ValidationError):
        replace(state, last_known_hash="c" * 64)


def test_source_representation_is_explicit_and_does_not_promote_rendered_text(setup):
    original = registry_for(setup).catalog.choices[0]
    assert original.capture_kind == "UNVERIFIED"
    assert replace(original, capture_kind="RETAINED_RENDERED_TEXT").capture_kind != "RAW_HTTP_BODY"
    with pytest.raises(ValidationError):
        replace(original, capture_kind="MODEL_ASSERTED_RAW")
