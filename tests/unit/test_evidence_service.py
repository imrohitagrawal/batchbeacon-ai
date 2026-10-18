"""OE01–12 local protocol cases. Fake stores/providers, never real service proof."""

import json
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import RLock

import pytest
from pydantic import ValidationError

from batchbeacon.contracts import (
    IdentifierKind,
    LiveStatus,
    ObservedIdentifier,
    ValueType,
    Verdict,
    VerifierPolicy,
)
from batchbeacon.evidence_service import (
    EvidenceEnvironment,
    EvidencePolicy,
    EvidenceService,
    EvidenceSnapshot,
    EvidenceState,
    ExtractedIdentity,
    ExtractedValues,
    ExtractionEnvelope,
    replace,
)
from batchbeacon.guest_service import GuestDenied, GuestPolicy, GuestService
from batchbeacon.shared_admission import IncidentUsage, SessionUsage, VerificationReservation
from batchbeacon.uploads import sanitize_images
from tests.unit.domain_fixtures import NOW, context, known, notice, observation, unknown
from tests.unit.test_guest_boundary import ORIGIN, MemoryObjects, MemoryRepository, picture


class Store:
    """Serialized fake, double callback, shared lock, controllable lost ack/races."""
    def __init__(self, guests, environment):
        self.guests, self.environment = guests, environment
        self.states, self.usage, self.lock = {}, {}, RLock()
        self.after_commit = lambda: None
        self.lost_ack = False

    def provision(self, guest, incident, policy):
        # Test-only provisioning; real adapter must make this atomic with issuance.
        key = (guest.capability_hash, incident.id)
        assert key not in self.states
        self.states[key] = EvidenceState(session_id=guest.scope.session_id,
            incident_id=incident.id, policy_hash=policy.digest()).model_dump_json()
        self.usage[guest.capability_hash] = SessionUsage(session_id=guest.scope.session_id,
            incidents=(IncidentUsage(incident_id=incident.id),))

    def state(self, key, incident):
        value = self.states.get((key, incident))
        return EvidenceState.model_validate_json(value) if value else None

    def transact(self, key, incident, change):
        with self.lock:
            snapshot = EvidenceSnapshot(self.guests.get(key), self.state(key, incident),
                                        self.environment, self.usage.get(key))
            first, second = change(snapshot), change(snapshot)
            assert first == second
            self.states[(key, incident)] = second.model_dump_json()
            self.after_commit()
            if self.lost_ack:
                raise OSError("injected lost acknowledgement")
            return second

    def reserve(self, key, incident, request_key, binding):
        # Explicit fake of SharedAdmission's committed receipt, no paid ledger.
        usage = self.usage[key]
        counter = next(i for i in usage.incidents if i.incident_id == incident)
        if len(counter.verifications) >= 6:
            raise GuestDenied(429, "test_verification_limit")
        updated = replace(counter, verifications=(*counter.verifications,
            VerificationReservation(request_key=request_key, context_state_hash=binding)))
        self.usage[key] = replace(usage, incidents=tuple(
            updated if i.incident_id == incident else i for i in usage.incidents))


@pytest.fixture
def rig():
    now = [NOW]
    repo, objects = MemoryRepository(), MemoryObjects()
    guest = GuestService(GuestPolicy(origin=ORIGIN), repo, objects, clock=lambda: now[0])
    token, session = guest.issue()
    incident = guest.create_incident(token, "incident")
    capture = guest.retain(token, incident.id, "upload",
                           sanitize_images((picture(),), guest.policy.uploads)).captures[0]
    policy = EvidencePolicy()
    store = Store(repo, EvidenceEnvironment(context=context(), notices=(notice(),),
                                             verifier_policy=VerifierPolicy()))
    store.provision(session, incident, policy)
    service = EvidenceService(guest, store, policy)
    obs = observation()
    ref = capture.evidence()
    values = ExtractedValues(identity=ExtractedIdentity(
        name=known(obs.identity.name.value, evidence=ref), pack=known("250 g", evidence=ref)),
        fields=tuple(replace(v, observation=known(v.observation.value,
            v.observation.value_type, evidence=ref)) for v in obs.fields))
    envelope = ExtractionEnvelope(provenance="fake", redacted_output_json='{"fake":true}',
        validation="VALID", values=values, model_id="test-fake", prompt_version="test-1",
        configuration_hash="a" * 64, sources=(notice().dependency,), captures=(ref,),
        started_at=NOW, completed_at=NOW)
    return service, store, token, session, incident, envelope, now


def extract(rig, key="extract", expected=0, envelope=None):
    service, _, token, _, incident, original, _ = rig
    return service.record_extraction(token, incident.id, key, expected, envelope or original)


def view(rig, revision=None):
    service, _, token, _, incident, _, _ = rig
    return service.read_evidence(token, incident.id, revision)


def correct(rig, key="edit", expected=1, field="LOT", value="000aB", replacement=None):
    service, _, token, _, incident, envelope, _ = rig
    return service.correct(token, incident.id, key, expected, field,
                           replacement or known(value, evidence=envelope.captures[0]))


def publish(rig, key="verify"):
    service, store, token, session, incident, _, _ = rig
    binding = service.verification_binding(token, incident.id)
    store.reserve(session.capability_hash, incident.id, key, binding)
    return service.publish_verification(token, incident.id, key, binding), binding


def test_original_extraction_corrections_and_restart_preserve_history(rig):
    extract(rig)
    initial = view(rig).state.model_dump_json()
    publish(rig)
    assert view(rig).hold_eligible
    usage = rig[1].usage.copy()
    correct(rig)
    current = view(rig)
    assert current.observation.fields[0].observation.value == "000aB"
    assert not current.current and not current.hold_eligible
    assert current.state.active_result is None and len(current.state.results) == 1
    assert current.state.observations[0].observation.fields[0].observation.value == "232511"
    correction = current.observation.corrections[0]
    assert correction.previous.value == "232511" and correction.replacement.value == "000aB"
    assert correction.actor_session == rig[3].scope.session_id and correction.recorded_at == NOW
    assert current.observation.model_id == "test-fake" and rig[1].usage == usage
    restored = EvidenceState.model_validate_json(initial)
    assert restored.extractions == current.state.extractions
    assert restored.observations[0] == current.state.observations[0]
    service = EvidenceService(rig[0].guest, rig[1], rig[0].policy)
    assert service.read_evidence(rig[2], rig[4].id).state == current.state
    assert not view(rig, 1).current


@pytest.mark.parametrize("operation", ["read", "extract", "correct", "bind", "publish"])
def test_foreign_incident_and_expiry_deny_every_operation(rig, operation):
    extract(rig)
    service, _, token, _, incident, envelope, now = rig
    foreign, _ = service.guest.issue()
    calls = {
        "read": lambda t: service.read_evidence(t, incident.id),
        "extract": lambda t: service.record_extraction(t, incident.id, "other", 1, envelope),
        "correct": lambda t: service.correct(t, incident.id, "other", 1, "LOT", unknown()),
        "bind": lambda t: service.verification_binding(t, incident.id),
        "publish": lambda t: service.publish_verification(t, incident.id, "other", "a" * 64),
    }
    with pytest.raises(GuestDenied):
        calls[operation](foreign)
    now[0] += timedelta(hours=8)
    with pytest.raises(GuestDenied) as error:
        calls[operation](token)
    assert error.value.status == 401


def test_expiry_after_commit_denies_without_erasing_record(rig):
    service, store, _, session, incident, _, now = rig
    store.after_commit = lambda: now.__setitem__(0, NOW + timedelta(hours=8))
    with pytest.raises(GuestDenied):
        extract(rig)
    state = store.state(session.capability_hash, incident.id)
    assert len(state.observations) == len(state.extractions) == 1


@pytest.mark.parametrize("part", ["root", "nested", "missing_bytes", "corrupt_bytes", "pending"])
def test_unowned_or_unretained_capture_rejected(rig, part):
    service, _, _, session, incident, envelope, _ = rig
    if part == "root":
        envelope = replace(envelope, captures=(replace(envelope.captures[0], sha256="b" * 64),))
    if part == "nested":
        foreign = replace(envelope.captures[0], artifact_id="b" * 32)
        envelope = replace(envelope, values=replace(envelope.values,
            identity=replace(envelope.values.identity, name=known("x", evidence=foreign))))
    if part in {"missing_bytes", "corrupt_bytes"}:
        object_key = next(iter(service.guest.objects.data))
        if part == "missing_bytes":
            del service.guest.objects.data[object_key]
        else:
            service.guest.objects.data[object_key] = b"bad"
    if part == "pending":
        stored = service.guest.repository.get(session.capability_hash)
        old = stored.incidents[0]
        updated = replace(old, batches=tuple(replace(b, ready=False) for b in old.batches))
        service.guest.repository.data[session.capability_hash] = replace(
            stored, incidents=(updated,)).model_dump_json()
    with pytest.raises(GuestDenied):
        extract(rig, envelope=envelope)
    assert not rig[1].state(session.capability_hash, incident.id).extractions


def test_invalid_extraction_is_diagnostic_and_invalidates_old_eligibility(rig):
    extract(rig)
    publish(rig)
    invalid = replace(rig[5], validation="INVALID", validation_codes=("SCHEMA_INVALID",),
                      values=None, redacted_output_json='{"broken":"original"}')
    extract(rig, key="invalid", expected=1, envelope=invalid)
    current = view(rig)
    assert len(current.state.extractions) == 2 and len(current.state.observations) == 1
    assert current.state.extractions[-1].envelope == invalid
    assert not current.current and not current.hold_eligible


@pytest.mark.parametrize("field,value", [("resolved_name", "invented"), ("reviewed", True),
                                        ("session_id", "fake"), ("revision", 99)])
def test_model_schema_cannot_assign_authority(rig, field, value):
    with pytest.raises(ValidationError):
        ExtractedIdentity.model_validate(rig[5].values.identity.model_dump() | {field: value})


@pytest.mark.parametrize("missing", ["absent", "corrupt", "owner", "policy"])
def test_established_state_cannot_silently_reset(rig, missing):
    extract(rig)
    store, session, incident = rig[1], rig[3], rig[4]
    key = (session.capability_hash, incident.id)
    if missing == "absent":
        del store.states[key]
    elif missing == "corrupt":
        store.states[key] = "{broken"
    else:
        state = store.state(*key)
        store.states[key] = json.dumps(state.model_dump(mode="json") | {
            "session_id" if missing == "owner" else "policy_hash":
            "b" * (32 if missing == "owner" else 64)})
    with pytest.raises(GuestDenied):
        extract(rig, key="repeat")


def test_stale_unknown_target_ambiguous_code_and_wrong_type_rejected(rig):
    values = rig[5].values
    code = ObservedIdentifier(kind=IdentifierKind.GTIN,
                              observation=known("0001", evidence=rig[5].captures[0]))
    envelope = replace(rig[5], values=replace(values, identity=replace(values.identity,
                                                                    identifiers=(code, code))))
    extract(rig, envelope=envelope)
    for field in ("reviewed", "GTIN"):
        with pytest.raises(GuestDenied):
            correct(rig, field=field)
    with pytest.raises(GuestDenied):
        correct(rig, expected=2)
    with pytest.raises(GuestDenied):
        correct(rig, replacement=known("2026-10-17", ValueType.DATE,
                                      evidence=rig[5].captures[0]))
    with pytest.raises(TypeError):
        rig[0].correct(rig[2], rig[4].id, "forged", 1, "LOT", unknown(), previous="forged")
    assert len(view(rig).state.observations) == 1


def test_identity_edit_clears_resolution_and_ambiguous_date_preserved(rig):
    extract(rig)
    # Simulate a separately reviewed resolver's persisted identity; no client setter.
    store, session, incident = rig[1], rig[3], rig[4]
    state = store.state(session.capability_hash, incident.id)
    saved = state.observations[0]
    resolved = replace(saved.observation.identity, resolved_name="old",
                       resolution_review_hash="b" * 64)
    saved = replace(saved, observation=replace(saved.observation, identity=resolved))
    store.states[(session.capability_hash, incident.id)] = replace(
        state, observations=(saved,)).model_dump_json()
    correct(rig, field="PRODUCT_NAME", value="new name")
    assert view(rig).observation.identity.resolved_name is None
    correct(rig, key="date", expected=2, field="BEST_BEFORE",
            replacement=unknown(True, ValueType.DATE))
    assert view(rig).observation.fields[1].observation.state.value == "AMBIGUOUS"
    assert view(rig).observation.model_id == "test-fake"


def test_lost_ack_idempotency_conflict_and_no_old_reactivation(rig):
    store = rig[1]
    store.lost_ack = True
    with pytest.raises(GuestDenied):
        extract(rig)
    store.lost_ack = False
    assert extract(rig).revision == 1
    publish(rig)
    store.lost_ack = True
    with pytest.raises(GuestDenied):
        correct(rig)
    store.lost_ack = False
    assert correct(rig).revision == 2
    correct(rig, key="new", expected=2, value="last")
    assert correct(rig).revision == 2
    assert extract(rig).revision == 1
    assert view(rig).observation.revision == 3 and view(rig).state.active_result is None
    with pytest.raises(GuestDenied) as error:
        correct(rig, value="different")
    assert error.value.code == "evidence_request_conflict"


def test_concurrent_corrections_one_wins(rig):
    extract(rig)
    def edit(i):
        try:
            return correct(rig, key=f"edit{i}", value=f"000{i}").revision
        except GuestDenied as error:
            return error.code
    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(edit, (1, 2)))
    assert sorted(map(str, outcomes)) == ["2", "observation_changed"]
    assert len(view(rig).state.observations) == 2


@pytest.mark.parametrize("change", ["correction", "source", "policy", "missing_reservation",
                                   "wrong_reservation", "missing_usage"])
def test_stale_or_unreserved_result_cannot_publish(rig, change):
    extract(rig)
    service, store, token, session, incident, _, _ = rig
    binding = service.verification_binding(token, incident.id)
    if change != "missing_reservation":
        store.reserve(session.capability_hash, incident.id, "verify",
                      "b" * 64 if change == "wrong_reservation" else binding)
    if change == "correction":
        correct(rig)
    if change == "source":
        store.environment = replace(store.environment, context=replace(
            store.environment.context, live_status=LiveStatus.FAILED))
    if change == "policy":
        store.environment = replace(store.environment, verifier_policy=VerifierPolicy(version="v2"))
    if change == "missing_usage":
        del store.usage[session.capability_hash]
    with pytest.raises(GuestDenied):
        service.publish_verification(token, incident.id, "verify", binding)
    assert not store.state(session.capability_hash, incident.id).results
    if change == "missing_usage":
        with pytest.raises(GuestDenied, match="acquisition_state_unavailable"):
            view(rig)
    else:
        assert not view(rig).state.results


@pytest.mark.parametrize("negative", [False, True])
def test_currentness_ignores_allowance_and_invalidates_positive_and_negative(rig, negative):
    extract(rig)
    if negative:
        correct(rig)
        # Explicit test-only reviewed identity resolution, not model input.
        store, session, incident = rig[1], rig[3], rig[4]
        state = store.state(session.capability_hash, incident.id)
        saved = state.observations[-1]
        identity = replace(saved.observation.identity,
            resolved_name=saved.observation.identity.name.value,
            resolution_review_hash=observation().identity.resolution_review_hash)
        saved = replace(saved, observation=replace(saved.observation, identity=identity))
        store.states[(session.capability_hash, incident.id)] = replace(
            state, observations=(*state.observations[:-1], saved)).model_dump_json()
    for i in range(6):
        publish(rig, key=f"verify{i}")
    before = view(rig)
    assert before.current
    assert before.hold_eligible is (not negative)
    assert before.result.verdict == (Verdict.NOT_LISTED_IN_CHECKED_NOTICES if negative
                                     else Verdict.MATCHED_HOLD_FOR_REVIEW)
    rig[1].environment = replace(rig[1].environment, context=replace(
        rig[1].environment.context, live_status=LiveStatus.FAILED))
    current = view(rig)
    assert not current.current and not current.hold_eligible
    correct(rig, key="later", expected=2 if negative else 1, value="new")
    assert view(rig).state.active_result is None
    assert len(rig[1].usage[rig[3].capability_hash].incidents[0].verifications) == 6


def test_current_failure_review_is_not_hold_eligible(rig):
    extract(rig)
    rig[1].environment = replace(rig[1].environment, context=replace(
        rig[1].environment.context, live_status=LiveStatus.FAILED))
    publish(rig)
    current = view(rig)
    assert current.current and not current.hold_eligible
    assert current.result.verdict == Verdict.REVIEW_REQUIRED


def test_reservation_binds_observation_and_duplicate_result_never_reactivates(rig):
    extract(rig)
    service, store, token, _, incident, _, _ = rig
    receipt, old = publish(rig)
    correct(rig)
    new = service.verification_binding(token, incident.id)
    assert old != new
    assert service.publish_verification(token, incident.id, "verify", old) == receipt
    assert view(rig).state.active_result is None
    assert len(store.usage[rig[3].capability_hash].incidents[0].verifications) == 1


def test_read_failure_and_missing_environment_do_not_return_current_result(rig):
    extract(rig)
    publish(rig)
    rig[1].environment = None
    with pytest.raises(GuestDenied):
        view(rig)
    rig[1].environment = EvidenceEnvironment(context=context(), notices=(notice(),),
                                               verifier_policy=VerifierPolicy())
    rig[0].guest.objects.data.clear()
    with pytest.raises(GuestDenied):
        view(rig)


def test_config_types_overrides_utf8_and_history_limits(rig):
    for kwargs in ({"max_raw_bytes": True}, {"max_extractions": 0}, {"max_state_bytes": "1024"},
                   {"max_raw_bytes": 1000, "max_state_bytes": 1000}):
        with pytest.raises(ValidationError):
            EvidencePolicy(**kwargs)
    service, store, token, session, incident, envelope, _ = rig
    raw = '{"x":"é"}'
    limit = len(raw.encode())
    policy = EvidencePolicy(max_raw_bytes=limit, max_extractions=1, max_observations=1)
    store.states[(session.capability_hash, incident.id)] = EvidenceState(
        session_id=session.scope.session_id, incident_id=incident.id,
        policy_hash=policy.digest()).model_dump_json()
    service = EvidenceService(service.guest, store, policy)
    exact = replace(envelope, redacted_output_json=raw)
    service.record_extraction(token, incident.id, "exact", 0, exact)
    with pytest.raises(GuestDenied) as error:
        service.record_extraction(token, incident.id, "over", 1,
                                  replace(exact, redacted_output_json=raw + " "))
    assert error.value.code == "extraction_envelope_invalid"
    with pytest.raises(GuestDenied) as error:
        service.correct(token, incident.id, "edit", 1, "LOT", unknown())
    assert error.value.code == "evidence_history_limit"
    assert len(store.state(session.capability_hash, incident.id).observations) == 1


@pytest.mark.parametrize("revision", [True, "1", -1])
def test_malformed_revision_is_not_coerced(rig, revision):
    with pytest.raises(GuestDenied):
        extract(rig, expected=revision)
    extract(rig)
    with pytest.raises(GuestDenied):
        correct(rig, expected=revision)


def test_freshness_crossing_final_storage_ack_is_not_current(rig):
    from batchbeacon.contracts import SourceMode
    extract(rig)
    store, now = rig[1], rig[6]
    store.environment = replace(store.environment, context=replace(store.environment.context,
        mode=SourceMode.LIVE, live_status=LiveStatus.VALIDATED, live_validated_at=NOW),
        verifier_policy=VerifierPolicy(live_freshness_seconds=10))
    publish(rig)
    assert view(rig).current
    calls = [0]
    def advance():
        calls[0] += 1
        if calls[0] == 2:
            now[0] += timedelta(seconds=10)
    store.after_commit = advance
    assert not view(rig).current


def test_changed_observation_during_retained_read_denies(rig):
    extract(rig)
    objects = rig[0].guest.objects
    original = objects.get
    changed = [False]
    def get(*args):
        data = original(*args)
        if not changed[0]:
            changed[0] = True
            # Unknown value has no object read, so this safely interleaves a new revision.
            correct(rig, replacement=unknown())
        return data
    objects.get = get
    with pytest.raises(GuestDenied) as error:
        view(rig)
    assert error.value.code == "evidence_changed_during_read"


def test_new_capture_and_failed_new_extraction_do_not_mutate_previous_bytes(rig):
    extract(rig)
    before = view(rig).state.observations[0].model_dump_json()
    service, _, token, _, incident, envelope, _ = rig
    capture = service.guest.retain(token, incident.id, "recapture",
        sanitize_images((picture(size=(9, 7)),), service.guest.policy.uploads)).captures[0]
    ref = capture.evidence()
    values = replace(envelope.values, identity=ExtractedIdentity(
        name=known("Recaptured product", evidence=ref), pack=known("250 g", evidence=ref)),
        fields=tuple(replace(v, observation=unknown(value_type=v.observation.value_type))
                     for v in envelope.values.fields))
    extract(rig, key="recapture", expected=1,
            envelope=replace(envelope, captures=(ref,), values=values))
    current = view(rig)
    assert current.observation.revision == 2
    assert current.state.observations[0].model_dump_json() == before
    assert len(current.state.extractions) == 2
    assert current.observation.captures == (ref,)


def test_effective_state_byte_limit_reaches_store_boundary(rig):
    service, store, token, session, incident, envelope, _ = rig
    policy = EvidencePolicy(max_raw_bytes=100, max_state_bytes=500)
    store.states[(session.capability_hash, incident.id)] = EvidenceState(
        session_id=session.scope.session_id, incident_id=incident.id,
        policy_hash=policy.digest()).model_dump_json()
    service = EvidenceService(service.guest, store, policy)
    with pytest.raises(GuestDenied) as error:
        service.record_extraction(token, incident.id, "extract", 0, envelope)
    assert error.value.code == "evidence_history_limit"
    assert not store.state(session.capability_hash, incident.id).extractions


@pytest.mark.parametrize("correct_after_failure", [False, True])
def test_invalid_latest_extraction_cannot_reverify_older_success(rig, correct_after_failure):
    extract(rig)
    publish(rig)
    invalid = replace(rig[5], validation="INVALID", validation_codes=("SCHEMA_INVALID",),
                      values=None, redacted_output_json='{"invalid":true}')
    extract(rig, key="failed-recapture", expected=1, envelope=invalid)
    if correct_after_failure:
        correct(rig)
    with pytest.raises(GuestDenied) as error:
        publish(rig, key="retry-after-failure")
    assert error.value.code == "latest_extraction_invalid"
    assert not view(rig).current and not view(rig).hold_eligible
    assert len(view(rig).state.results) == 1
    # A genuinely new validated extraction, not an old receipt retry, recovers.
    extract(rig, key="valid-recovery", expected=2 if correct_after_failure else 1)
    publish(rig, key="recovery")
    assert view(rig).current and view(rig).hold_eligible


@pytest.mark.parametrize("raw", ["{broken", "[]", "", "not json"])
def test_invalid_raw_response_is_preserved_without_successful_observation(rig, raw):
    invalid = replace(rig[5], validation="INVALID", validation_codes=("SCHEMA_INVALID",),
                      values=None, redacted_output_json=raw)
    extract(rig, envelope=invalid)
    state = view(rig).state
    assert state.extractions[0].envelope.redacted_output_json == raw
    assert not state.observations and not state.results
    with pytest.raises(ValidationError):
        replace(rig[5], redacted_output_json=raw)
