"""Trusted refresh at actual publication/activation boundaries; all providers controlled."""

from datetime import timedelta

import pytest

from batchbeacon.action_service import ActionConfirmation
from batchbeacon.contracts import ActionType
from batchbeacon.evidence_service import replace
from batchbeacon.guest_service import GuestDenied
from batchbeacon.learning_service import ActivationConfirmation
from batchbeacon.source_refresh import TrustedRefresh
from tests.unit.test_firestore_store import env as env
from tests.unit.test_firestore_store import extract, owned, publish, saved, shared
from tests.unit.test_firestore_store import no_network_or_credentials as no_network_or_credentials
from tests.unit.test_firestore_store import setup as setup
from tests.unit.test_learning_service import candidate
from tests.unit.test_learning_service import learning as learning
from tests.unit.test_reviewed_extraction import acquire
from tests.unit.test_reviewed_extraction import reviewed as reviewed
from tests.unit.test_source_runtime import refresher, source_service


@pytest.mark.parametrize("phase", ["extraction", "verification", "completion"])
def test_actual_refresh_during_inflight_acquisition_prevents_current_completion(reviewed, phase):
    c = reviewed
    stores, server, *_ = c[3]
    source_service(c[3])
    refresh = refresher(c[3])
    calls = []

    def race(request):
        for write in request.writes:
            kind = write.update.fields["kind"].string_value
            state = stores._decode(write.update, kind)
            relevant = (
                kind == "completion"
                if phase == "completion"
                else kind == "evidence"
                and bool(state.results if phase == "verification" else state.extractions)
            )
            if relevant:
                server.before_commit = lambda request: None
                calls.append(True)
                refresh.begin("inflight")
                return

    server.before_commit = race
    result = acquire(c)
    assert calls == [True] and server.aborts == 1 and not result.current
    assert not c[7].read_evidence(c[2], c[1].incident_id).current
    assert not any(doc.fields["kind"].string_value == "completion" for doc in server.docs.values())
    assert len(c[4]) == 2  # one controlled fake generation + countTokens, no real model


@pytest.mark.parametrize("phase", ["before", "during"])
def test_actual_source_refresh_invalidates_evaluated_guidance_activation(learning, phase):
    c, service = learning
    source_service(c[3])
    refresh = refresher(c[3])
    _, _, proposal = candidate(learning)
    evaluation = service.evaluate(c[2], "evaluate", proposal.id)
    confirmation = ActivationConfirmation(
        basis=service.prepare_activation(c[2], evaluation.id), explicit_confirmation=True
    )
    stores, server, *_ = c[3]
    if phase == "before":
        refresh.begin("guidance-source")
    else:

        def race(request):
            if any(
                w.update.name == stores.name("learning", c[6].capability_hash)
                for w in request.writes
            ):
                server.before_commit = lambda request: None
                refresh.begin("guidance-source")

        server.before_commit = race
    with pytest.raises(GuestDenied):
        service.activate(c[2], "activate", confirmation)
    state = service.read(c[2])
    assert state.active.activation_revision == 1 and not state.transitions
    assert len(c[4]) == 2


def test_valid_refresh_deadline_reaches_action_commit_consumer(setup, env, monkeypatch):
    stores, server, guest, evidence, actions, now = setup
    original = saved(setup, "environment")
    original = replace(
        original, verifier_policy=replace(original.verifier_policy, live_freshness_seconds=1)
    )
    server.seed(stores._encode(stores.name("environment"), "environment", original))
    source_service(setup)
    token, session, incident = owned(setup)
    extract(setup, token, incident)
    publish(setup, env, token, session, incident)
    refresh = refresher(setup)
    refresh = TrustedRefresh(
        stores, replace(refresh.policy, freshness_seconds=1), clock=lambda: now[0]
    )
    refresh.begin("fresh")
    refresh.publish("fresh", refresh.policy.expected_hash)
    binding = evidence.verification_binding(token, incident.id)
    shared(setup, env).reserve_verification(session.capability_hash, incident.id, "live", binding)
    evidence.publish_verification(token, incident.id, "live", binding)
    target = actions.prepare(token, incident.id, ActionType.SIMULATED_HOLD)
    validate = actions._target

    def after_target(*args):
        value = validate(*args)
        now[0] += timedelta(seconds=1)
        return value

    monkeypatch.setattr(actions, "_target", after_target)
    before = server.versions.copy()
    with pytest.raises(GuestDenied):
        actions.confirm(
            token,
            incident.id,
            "cutoff",
            ActionConfirmation(target=target, explicit_confirmation=True),
        )
    assert server.versions == before and not actions.list_actions(token, incident.id)


def test_unknown_retrieval_is_explicit_and_never_accepted_for_reviewed_or_complete_notice():
    from pydantic import ValidationError

    from tests.unit.domain_fixtures import notice

    original = notice()
    with pytest.raises(ValidationError):
        replace(original, retrieved_at=None)
    unknown = replace(
        original, review=None, interpretation_complete=False, products=(), retrieved_at=None
    )
    assert "retrieved_at" in unknown.model_dump() and unknown.retrieved_at is None
    with pytest.raises(ValidationError):
        replace(unknown, interpretation_complete=True)
    with pytest.raises(ValidationError):
        replace(original, retrieved_at=original.retrieved_at.replace(tzinfo=None))
    raw = unknown.model_dump()
    raw.pop("retrieved_at")
    with pytest.raises(ValidationError):
        type(unknown).model_validate(raw)
