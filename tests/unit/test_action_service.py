"""A01–18 protocol tests with explicitly injected local stores; no actual actions."""

import json
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

import pytest
from pydantic import ValidationError

from batchbeacon.action_service import (
    ActionConfirmation,
    ActionPolicy,
    ActionService,
    ActionSnapshot,
    ActionState,
)
from batchbeacon.contracts import ActionType, LiveStatus, VerifierPolicy
from batchbeacon.evidence_service import replace
from batchbeacon.guest_service import GuestDenied
from tests.unit.test_evidence_service import correct, extract, publish
from tests.unit.test_evidence_service import rig as rig  # noqa: F401

HOLD = ActionType.SIMULATED_HOLD
REVIEW = ActionType.SIMULATED_REVIEW_REQUEST


class ActionStoreFake:
    def __init__(self, evidence_store):
        self.evidence = evidence_store
        self.states = {}
        self.before_retry = lambda: None
        self.after_commit = lambda: None
        self.fail_before = self.fail_after = False

    def provision(self, session, incident, policy):
        self.states[(session.capability_hash, incident.id)] = ActionState(
            session_id=session.scope.session_id, incident_id=incident.id,
            policy_hash=policy.digest()).model_dump_json()

    def state(self, key, incident):
        value = self.states.get((key, incident))
        return ActionState.model_validate_json(value) if value else None

    def transact(self, key, incident, change):
        with self.evidence.lock:
            def snapshot():
                return ActionSnapshot(self.evidence.guests.get(key),
                    self.evidence.state(key, incident), self.evidence.environment,
                    self.state(key, incident))
            first_snapshot = snapshot()
            first = change(first_snapshot)
            self.before_retry()
            second_snapshot = snapshot()
            second = change(second_snapshot)
            if first_snapshot == second_snapshot:
                assert first == second
            if self.fail_before:
                raise OSError("injected precommit failure")
            self.states[(key, incident)] = second.model_dump_json()
            self.after_commit()
            if self.fail_after:
                raise OSError("injected committed lost acknowledgement")
            return second


@pytest.fixture
def actions(rig):
    extract(rig)
    publish(rig)
    store = ActionStoreFake(rig[1])
    policy = ActionPolicy()
    store.provision(rig[3], rig[4], policy)
    return ActionService(rig[0], store, policy), store, rig


def target(actions, kind=HOLD):
    service, _, rig = actions
    return service.prepare(rig[2], rig[4].id, kind)


def confirm(actions, key="confirm", command=None, kind=HOLD):
    service, _, rig = actions
    command = command or ActionConfirmation(target=target(actions, kind),
                                             explicit_confirmation=True)
    return service.confirm(rig[2], rig[4].id, key, command)


def logical(actions, revision=1, kind=HOLD):
    service, _, rig = actions
    return service.reconcile(rig[2], rig[4].id, revision, kind)


def fail_source(actions):
    store = actions[2][1]
    store.environment = replace(store.environment, context=replace(
        store.environment.context, live_status=LiveStatus.FAILED))


def test_explicit_confirmation_and_server_actor_history(actions):
    service, store, rig = actions
    prepared = target(actions)
    assert not store.state(rig[3].capability_hash, rig[4].id).actions
    for value in (False, None, "true", 1):
        with pytest.raises(ValidationError):
            ActionConfirmation(target=prepared, explicit_confirmation=value)
    with pytest.raises(GuestDenied):
        service.confirm(rig[2], rig[4].id, "no", None)
    result = confirm(actions)
    assert result.current and not result.requires_renewed_review
    assert result.action.simulation is True
    assert result.action.actor_session == rig[3].scope.session_id
    assert result.event.event_type == "ACTION_CREATED" and result.event.sequence == 1
    stored = rig[1].state(rig[3].capability_hash, rig[4].id)
    assert result.action.sources == stored.results[0].checked_sources
    restarted = ActionService(rig[0], store, service.policy)
    assert restarted.get_action(rig[2], rig[4].id, result.action.id) == result


@pytest.mark.parametrize("field,value", [("actor_session", "forged"), ("role", "manager"),
                                        ("session_id", "foreign"), ("result", {})])
def test_client_authority_fields_rejected(actions, field, value):
    command = {"target": target(actions).model_dump(), "explicit_confirmation": True, field: value}
    with pytest.raises(ValidationError):
        ActionConfirmation.model_validate(command)


@pytest.mark.parametrize("field,value", [("result_hash", "b" * 64),
    ("observation_hash", "b" * 64), ("result_revision", 9), ("context_state_hash", "b" * 64),
    ("environment_hash", "b" * 64), ("action_policy_hash", "b" * 64)])
def test_altered_confirmation_creates_nothing(actions, field, value):
    command = ActionConfirmation(target=replace(target(actions), **{field: value}),
                                 explicit_confirmation=True)
    with pytest.raises(GuestDenied):
        confirm(actions, command=command)
    assert logical(actions) is None


def test_cross_session_all_access_and_replay_denied(actions):
    service, _, rig = actions
    command = ActionConfirmation(target=target(actions), explicit_confirmation=True)
    recorded = confirm(actions, command=command)
    foreign, _ = rig[0].guest.issue()
    for call in (
        lambda: service.prepare(foreign, rig[4].id, HOLD),
        lambda: service.confirm(foreign, rig[4].id, "confirm", command),
        lambda: service.get_action(foreign, rig[4].id, recorded.action.id),
        lambda: service.list_actions(foreign, rig[4].id),
        lambda: service.reconcile(foreign, rig[4].id, 1, HOLD),
    ):
        with pytest.raises(GuestDenied):
            call()


def test_expiry_after_commit_retains_record_but_denies_response_and_replay(actions):
    service, store, rig = actions
    command = ActionConfirmation(target=target(actions), explicit_confirmation=True)
    store.after_commit = lambda: rig[6].__setitem__(0, rig[3].scope.expires_at)
    with pytest.raises(GuestDenied) as error:
        confirm(actions, command=command)
    assert error.value.status == 401
    assert len(store.state(rig[3].capability_hash, rig[4].id).actions) == 1
    with pytest.raises(GuestDenied):
        confirm(actions, command=command)
    with pytest.raises(GuestDenied):
        logical(actions)


@pytest.mark.parametrize("when", ["before", "retry", "after"])
def test_source_races_and_historical_replay(actions, when):
    service, store, rig = actions
    command = ActionConfirmation(target=target(actions), explicit_confirmation=True)
    if when == "before":
        fail_source(actions)
    elif when == "retry":
        store.before_retry = lambda: fail_source(actions)
    else:
        store.after_commit = lambda: fail_source(actions)
    if when != "after":
        with pytest.raises(GuestDenied):
            confirm(actions, command=command)
        assert not store.state(rig[3].capability_hash, rig[4].id).actions
    else:
        result = confirm(actions, command=command)
        assert not result.current and result.requires_renewed_review
        assert confirm(actions, command=command) == result
        assert confirm(actions, key="new-key", command=command) == result
        assert len(store.state(rig[3].capability_hash, rig[4].id).events) == 1


def test_corrected_observation_requires_new_result_and_action_links_history(actions):
    first = confirm(actions)
    original = first.action.model_dump_json()
    rig = actions[2]
    correct(rig, value="232511")
    assert not logical(actions).current
    with pytest.raises(GuestDenied):
        target(actions)
    publish(rig, key="new-result")
    second = confirm(actions, key="reconfirmed")
    assert second.current and second.action.prior_action_id == first.action.id
    assert second.action.result_revision == 2 and second.action.observation_revision == 2
    assert logical(actions).action.model_dump_json() == original
    assert not logical(actions).current


def test_current_review_preserves_failure_and_cannot_hold(actions):
    fail_source(actions)
    with pytest.raises(GuestDenied):
        target(actions, REVIEW)  # Old result is stale, not a current review result.
    publish(actions[2], key="failure-result")
    result = confirm(actions, kind=REVIEW)
    assert result.current and "SOURCE_UNAVAILABLE" in result.event.reason
    assert result.action.action_type == REVIEW
    with pytest.raises(GuestDenied):
        target(actions, HOLD)


def test_current_changed_source_review_can_retain_old_checked_dependencies(actions):
    rig = actions[2]
    environment = rig[1].environment
    changed = replace(environment.context.current_sources[0], epoch=2)
    rig[1].environment = replace(environment, context=replace(environment.context,
                                                              current_sources=(changed,)))
    publish(rig, key="changed-result")
    recorded = confirm(actions, kind=REVIEW)
    assert recorded.current and "SOURCE_VERSION_CHANGED" in recorded.event.reason
    assert recorded.action.sources[0].epoch == 1
    assert rig[1].environment.context.current_sources[0].epoch == 2


def test_scope_negative_enables_neither_action(actions):
    rig = actions[2]
    # An explicit test-only reviewed resolver enables a fully scoped negative.
    from tests.unit.domain_fixtures import observation
    correct(rig)
    evidence = rig[1].state(rig[3].capability_hash, rig[4].id)
    saved = evidence.observations[-1]
    identity = replace(saved.observation.identity,
                       resolved_name=saved.observation.identity.name.value,
                       resolution_review_hash=observation().identity.resolution_review_hash)
    saved = replace(saved, observation=replace(saved.observation, identity=identity))
    rig[1].states[(rig[3].capability_hash, rig[4].id)] = replace(evidence,
        observations=(*evidence.observations[:-1], saved)).model_dump_json()
    publish(rig, key="negative")
    for kind in (HOLD, REVIEW):
        with pytest.raises(GuestDenied) as error:
            target(actions, kind)
        assert error.value.code == "action_not_eligible"


def test_concurrent_different_keys_dedupe_one_action_and_protect_each_key(actions):
    command = ActionConfirmation(target=target(actions), explicit_confirmation=True)
    evidence_before = actions[2][1].states.copy()
    usage_before = actions[2][1].usage.copy()
    with ThreadPoolExecutor(max_workers=4) as pool:
        values = list(pool.map(lambda i: confirm(actions, f"key{i}", command), range(4)))
    assert len({v.action.id for v in values}) == 1
    state = actions[1].state(actions[2][3].capability_hash, actions[2][4].id)
    assert len(state.actions) == len(state.events) == 1 and len(state.receipts) == 4
    changed = replace(command, target=replace(command.target, result_hash="b" * 64))
    for i in range(4):
        with pytest.raises(GuestDenied) as error:
            confirm(actions, f"key{i}", changed)
        assert error.value.code == "action_request_conflict"
    assert actions[2][1].states == evidence_before and actions[2][1].usage == usage_before


@pytest.mark.parametrize("committed", [False, True])
def test_unknown_outcome_reconciles_without_duplicate_or_fabricated_absence(actions, committed):
    command = ActionConfirmation(target=target(actions), explicit_confirmation=True)
    store = actions[1]
    store.fail_after, store.fail_before = committed, not committed
    with pytest.raises(GuestDenied):
        confirm(actions, command=command)
    with pytest.raises(GuestDenied):
        logical(actions)  # Infrastructure failure cannot be reported as absence.
    store.fail_after = store.fail_before = False
    recovered = logical(actions)
    assert (recovered is not None) == committed
    final = confirm(actions, command=command)
    assert logical(actions) == final
    state = store.state(actions[2][3].capability_hash, actions[2][4].id)
    assert len(state.actions) == len(state.events) == 1


@pytest.mark.parametrize("problem", ["missing", "corrupt", "environment", "policy"])
def test_missing_state_environment_or_malformed_records_fail_closed(actions, problem):
    service, store, rig = actions
    key = (rig[3].capability_hash, rig[4].id)
    if problem == "missing":
        del store.states[key]
    elif problem == "corrupt":
        store.states[key] = "{broken"
    elif problem == "environment":
        rig[1].environment = None
    else:
        data = json.loads(store.states[key])
        data["policy_hash"] = "b" * 64
        store.states[key] = json.dumps(data)
    with pytest.raises(GuestDenied):
        service.list_actions(rig[2], rig[4].id)


def test_capacity_bounds_do_not_prevent_existing_reconciliation(actions):
    service, store, rig = actions
    policy = ActionPolicy(max_actions=1, max_receipts=1)
    store.provision(rig[3], rig[4], policy)
    limited = (ActionService(rig[0], store, policy), store, rig)
    command = ActionConfirmation(target=target(limited), explicit_confirmation=True)
    first = confirm(limited, command=command)
    assert confirm(limited, command=command) == first and logical(limited) == first
    with pytest.raises(GuestDenied) as error:
        confirm(limited, key="second-key", command=command)
    assert error.value.code == "action_history_limit"
    assert logical(limited) == first
    for values in ({"max_actions": True}, {"max_receipts": 0}, {"max_state_bytes": "1"},
                   {"max_actions": 2, "max_receipts": 1}):
        with pytest.raises(ValidationError):
            ActionPolicy(**values)


def test_time_expiry_currentness_after_final_storage_ack(actions):
    rig = actions[2]
    from batchbeacon.contracts import SourceMode
    environment = rig[1].environment
    rig[1].environment = replace(environment, context=replace(environment.context,
        mode=SourceMode.LIVE, live_status=LiveStatus.VALIDATED, live_validated_at=rig[6][0]),
        verifier_policy=VerifierPolicy(live_freshness_seconds=10))
    publish(rig, key="live")
    result = confirm(actions)
    assert result.current
    actions[1].after_commit = lambda: rig[6].__setitem__(0, rig[6][0] + timedelta(seconds=10))
    current = logical(actions, revision=2)
    assert not current.current and current.requires_renewed_review


@pytest.mark.parametrize("damage", ["receipt_missing", "receipt_payload", "future_result",
                                   "capture_not_ready", "support_withdrawn"])
def test_invalid_history_or_current_support_fails_closed(actions, damage):
    service, store, rig = actions
    result = confirm(actions)
    key = (rig[3].capability_hash, rig[4].id)
    if damage in {"receipt_missing", "receipt_payload"}:
        data = json.loads(store.states[key])
        if damage == "receipt_missing":
            data["receipts"] = []
        else:
            data["receipts"][0]["payload_hash"] = "b" * 64
        store.states[key] = json.dumps(data)
        with pytest.raises(GuestDenied):
            logical(actions)
    else:
        if damage == "future_result":
            state = rig[1].state(*key)
            future = replace(state.results[0], computed_at=rig[6][0] + timedelta(seconds=1))
            rig[1].states[key] = replace(state, results=(future,)).model_dump_json()
        elif damage == "capture_not_ready":
            guest = rig[0].guest.repository.get(key[0])
            incident = guest.incidents[0]
            incident = replace(incident, batches=tuple(replace(b, ready=False)
                                                       for b in incident.batches))
            rig[0].guest.repository.data[key[0]] = replace(guest,
                incidents=(incident,)).model_dump_json()
        else:
            environment = rig[1].environment
            rig[1].environment = replace(environment, notices=(
                replace(environment.notices[0], source_available=False),))
        if damage == "future_result":
            with pytest.raises(GuestDenied) as error:
                service.get_action(rig[2], rig[4].id, result.action.id)
            assert error.value.code == "action_evidence_unavailable"
        else:
            assert not service.get_action(rig[2], rig[4].id, result.action.id).current
        with pytest.raises(GuestDenied):
            target(actions)


def test_failed_live_cannot_restore_hold_by_historical_relabel(actions):
    from batchbeacon.contracts import SourceMode
    rig = actions[2]
    environment = rig[1].environment
    rig[1].environment = replace(environment, context=replace(environment.context,
        mode=SourceMode.LIVE, live_status=LiveStatus.FAILED))
    with pytest.raises(GuestDenied):
        target(actions)
    rig[1].environment = replace(rig[1].environment, context=replace(
        rig[1].environment.context, mode=SourceMode.HISTORICAL_DEMO))
    publish(rig, key="failed-historical")
    with pytest.raises(GuestDenied):
        target(actions)
    assert confirm(actions, kind=REVIEW).current


def test_latest_failed_acquisition_cannot_create_new_action(actions):
    rig = actions[2]
    command = ActionConfirmation(target=target(actions), explicit_confirmation=True)
    invalid = replace(rig[5], validation="INVALID", validation_codes=("SCHEMA_INVALID",),
                      values=None, redacted_output_json="{broken")
    extract(rig, key="invalid", expected=1, envelope=invalid)
    with pytest.raises(GuestDenied):
        confirm(actions, command=command)
    assert logical(actions) is None


def test_effective_action_byte_limit_prevents_partial_commit(actions):
    _, store, rig = actions
    policy = ActionPolicy(max_state_bytes=500)
    store.provision(rig[3], rig[4], policy)
    limited = ActionService(rig[0], store, policy), store, rig
    with pytest.raises(GuestDenied) as error:
        confirm(limited)
    assert error.value.code == "action_history_limit"
    state = store.state(rig[3].capability_hash, rig[4].id)
    assert not state.actions and not state.events and not state.receipts


@pytest.mark.parametrize("damage", ["action_type", "event_mode", "event_reason"])
def test_semantically_corrupt_action_history_denies_read_and_replay(actions, damage):
    fail_source(actions)
    publish(actions[2], key="failure-result")
    command = ActionConfirmation(target=target(actions, REVIEW), explicit_confirmation=True)
    recorded = confirm(actions, command=command)
    service, store, rig = actions
    key = (rig[3].capability_hash, rig[4].id)
    data = json.loads(store.states[key])
    if damage == "action_type":
        data["actions"][0]["action_type"] = HOLD.value
    elif damage == "event_mode":
        data["events"][0]["source_mode"] = "LIVE"
    else:
        data["events"][0]["reason"] = "SUPPORTED_MATCH_CONFIRMED"
    store.states[key] = json.dumps(data)
    with pytest.raises(GuestDenied) as error:
        service.get_action(rig[2], rig[4].id, recorded.action.id)
    assert error.value.code == "action_evidence_unavailable"
    before = store.states[key]
    with pytest.raises(GuestDenied):
        confirm(actions, key="alias-key", command=command)
    assert store.states[key] == before
