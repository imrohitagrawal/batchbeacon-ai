"""Pure queue semantics from actual validated SDK/mock workflow snapshots.

Snapshot acquisition in these fixtures is separate; projection performs no I/O.
"""

from dataclasses import replace as dataclass_replace
from datetime import timedelta

import pytest
from pydantic import ValidationError

from batchbeacon.action_service import ActionConfirmation
from batchbeacon.contracts import ActionType, LiveStatus
from batchbeacon.evidence_service import replace
from batchbeacon.guest_service import GuestDenied
from batchbeacon.retail_contracts import QueueCategory
from batchbeacon.retail_projection import (
    CapabilityObservation,
    CapabilityReason,
    CapabilityState,
    MaterialUpdate,
    QueueFilter,
    RetailProjector,
    RetailReadPolicy,
    capability_view,
    material_state_hash,
)
from tests.unit.test_extraction_proposal import unknown
from tests.unit.test_reviewed_extraction import acquire, view
from tests.unit.test_reviewed_extraction import env as env  # noqa
from tests.unit.test_reviewed_extraction import (
    no_network_or_credentials as no_network_or_credentials,  # noqa
)
from tests.unit.test_reviewed_extraction import reviewed as reviewed  # noqa
from tests.unit.test_reviewed_extraction import setup as setup  # noqa


def snapshot(c, incident=None):
    snapshots = []
    c[3][0].actions.transact(
        c[6].capability_hash,
        incident or c[1].incident_id,
        lambda s: snapshots.append(s) or s.actions,
    )
    return snapshots[0]


def projector(c, policy=None, contexts=None):
    return RetailProjector(
        c[8], c[0].shared.policy, policy or RetailReadPolicy(), contexts=contexts
    )


def prepare(p, c, s=None, sequence=1):
    s = s or snapshot(c)
    material = MaterialUpdate(
        changed_at=c[3][5][0],
        sequence=sequence,
        semantic_state_hash=material_state_hash(s),
        reference="synthetic-test-domain-change",
    )
    return p.project(c[6].capability_hash, s, material=material)


def capability(c, **changes):
    now = c[3][5][0]
    return CapabilityObservation(
        session_id=c[6].scope.session_id,
        capability="NEW_VERIFICATION",
        state=CapabilityState.AVAILABLE,
        reason=CapabilityReason.OBSERVED,
        observed_at=now,
        valid_until=now + timedelta(seconds=60),
        **changes,
    )


def queue(p, c, s=None, prepared=None, **kwargs):
    s = s or snapshot(c)
    return p.view(
        c[6].capability_hash,
        s.guest,
        s.usage,
        (prepared or prepare(p, c, s),),
        s.environment,
        **kwargs,
    )


def category(v):
    return v.snapshot.rows[0].category


def reverify(c, key="queue-reverify"):
    binding = c[7].verification_binding(c[2], c[1].incident_id)
    c[0].shared.reserve_verification(c[6].capability_hash, c[1].incident_id, key, binding)
    c[7].publish_verification(c[2], c[1].incident_id, key, binding)


def seed(c, kind, record):
    stores, server = c[3][:2]
    key = c[6].capability_hash if kind == "usage" else None
    server.seed(stores._encode(stores.name(kind, key), kind, record))


def test_untouched_draft_is_not_invented_observation_or_checked_coverage(reviewed):
    c = reviewed
    v = queue(projector(c), c)
    assert category(v) == QueueCategory.IN_PROGRESS
    row = v.snapshot.rows[0]
    assert row.observation_revision == 0 and row.result is None and not row.current
    assert not row.checked_sources and row.jurisdiction == "Not checked"
    assert sum(v.snapshot.category_counts.values()) == 1
    assert v.new_verification.state == CapabilityState.UNKNOWN


@pytest.mark.parametrize("reviewed", [(0,), (1,), (2,)], indirect=True)
def test_current_results_and_actual_actions_obey_category_precedence(reviewed):
    c = reviewed
    acquire(c)
    p = projector(c)
    current = view(c)
    v = queue(p, c)
    assert v.snapshot.rows[0].current == current.current
    if current.hold_eligible:
        assert category(v) == QueueCategory.HUMAN_REVIEW
        target = c[8].prepare(c[2], c[1].incident_id, ActionType.SIMULATED_HOLD)
        c[8].confirm(
            c[2],
            c[1].incident_id,
            "queue-hold",
            ActionConfirmation(target=target, explicit_confirmation=True),
        )
        held = queue(p, c, selected_filter=QueueFilter.SIMULATED_HOLDS)
        assert category(held) == QueueCategory.ACTION_RECORDED
        assert len(held.visible_incident_ids) == 1 and not held.contexts[0].action_historical
        reverify(c)
        historical = queue(p, c, selected_filter=QueueFilter.SIMULATED_HOLDS)
        assert category(historical) == QueueCategory.HUMAN_REVIEW
        assert not historical.visible_incident_ids and historical.contexts[0].action_historical
        assert historical.snapshot.rows[0].latest_action is not None
    else:
        assert category(v) == QueueCategory.NOT_LISTED
        assert queue(p, c, selected_filter=QueueFilter.NEEDS_ATTENTION).visible_incident_ids == ()
        assert sum(v.snapshot.category_counts.values()) == 1
        assert v.contexts[0].notices[0].interpretation == "COMPARED_NOTICE"
        assert v.contexts[0].notices[0].reason.state == "UNKNOWN"


@pytest.mark.parametrize("reviewed", [(0,)], indirect=True)
def test_missing_evidence_requires_observed_capability_and_remaining_own_allowance(reviewed):
    c = reviewed
    c[5][0]["label"]["best_before"] = unknown(kind="DATE")
    acquire(c)
    p = projector(c)
    assert category(queue(p, c)) == QueueCategory.HUMAN_REVIEW
    available = queue(p, c, new_verification=capability(c))
    assert category(available) == QueueCategory.NEEDS_EVIDENCE
    assert tuple(f.value for f in available.snapshot.rows[0].outstanding_fields) == ("BEST_BEFORE",)
    for index in range(c[0].shared.policy.max_recaptures):
        acquire(c, request_key=f"queue-recapture-{index}", expected_observation_revision=index + 1)
    assert category(queue(p, c, new_verification=capability(c))) == QueueCategory.HUMAN_REVIEW
    target = c[8].prepare(c[2], c[1].incident_id, ActionType.SIMULATED_REVIEW_REQUEST)
    c[8].confirm(
        c[2],
        c[1].incident_id,
        "queue-review",
        ActionConfirmation(target=target, explicit_confirmation=True),
    )
    recorded = queue(
        p, c, new_verification=capability(c), selected_filter=QueueFilter.SIMULATED_HOLDS
    )
    assert category(recorded) == QueueCategory.ACTION_RECORDED
    assert recorded.snapshot.rows[0].uncertainty_unresolved
    assert not recorded.visible_incident_ids


@pytest.mark.parametrize("change", ["review", "predicate", "failure", "scope", "source_epoch"])
def test_fresh_environment_semantics_invalidate_existing_projected_evidence(reviewed, change):
    c = reviewed
    acquire(c)
    s = snapshot(c)
    p = projector(c)
    prepared = prepare(p, c, s)
    environment = s.environment
    if change == "review":
        environment = replace(environment, notices=(replace(environment.notices[0], review=None),))
    elif change == "predicate":
        notice = environment.notices[0]
        product = notice.products[0]
        identity = replace(product.identity, canonical_name="Meadow Vale Brie")
        environment = replace(
            environment,
            notices=(
                replace(
                    notice, products=(replace(product, identity=identity), *notice.products[1:])
                ),
            ),
        )
    elif change == "failure":
        environment = replace(
            environment, context=replace(environment.context, live_status=LiveStatus.FAILED)
        )
    elif change == "scope":
        environment = replace(
            environment, context=replace(environment.context, jurisdiction="UK-ENG")
        )
    else:
        dep = environment.context.current_sources[0]
        environment = replace(
            environment,
            context=replace(
                environment.context, current_sources=(replace(dep, epoch=dep.epoch + 1),)
            ),
        )
    altered = dataclass_replace(s, environment=environment)
    assert category(queue(p, c, altered, prepared)) == QueueCategory.RENEWED_REVIEW
    seed(c, "environment", environment)
    assert not view(c).current


def test_failure_bound_review_can_be_current_and_recorded_unresolved(reviewed):
    c = reviewed
    acquire(c)
    environment = snapshot(c).environment
    seed(
        c,
        "environment",
        replace(environment, context=replace(environment.context, live_status=LiveStatus.FAILED)),
    )
    reverify(c)
    p = projector(c)
    v = queue(p, c)
    assert v.snapshot.rows[0].current and category(v) == QueueCategory.HUMAN_REVIEW
    target = c[8].prepare(c[2], c[1].incident_id, ActionType.SIMULATED_REVIEW_REQUEST)
    c[8].confirm(
        c[2],
        c[1].incident_id,
        "failure-review",
        ActionConfirmation(target=target, explicit_confirmation=True),
    )
    recorded = queue(p, c)
    assert category(recorded) == QueueCategory.ACTION_RECORDED
    assert recorded.snapshot.rows[0].uncertainty_unresolved
    seed(c, "environment", environment)
    assert category(queue(p, c)) == QueueCategory.RENEWED_REVIEW


@pytest.mark.parametrize("field", ["PRODUCT_NAME", "LOT"])
def test_original_completion_survives_later_correction_without_hash_substitution(reviewed, field):
    c = reviewed
    acquire(c)
    before = view(c)
    old = (
        before.observation.identity.name
        if field == "PRODUCT_NAME"
        else next(f.observation for f in before.observation.fields if f.field == field)
    )
    c[7].correct(c[2], c[1].incident_id, "queue-correct", 1, field, old)
    p = projector(c)
    s = snapshot(c)
    prepared = prepare(p, c, s)
    assert prepared.record.observation.corrections == ()
    assert (
        prepared.record.original_observation_hash
        == s.evidence.observations[-1].observation.digest()
    )
    assert prepared.record.observation.digest() != prepared.record.original_observation_hash
    assert category(queue(p, c, s, prepared)) == QueueCategory.RENEWED_REVIEW
    reverify(c)
    result = queue(p, c)
    assert result.snapshot.rows[0].current == view(c).current
    assert category(result) == (
        QueueCategory.HUMAN_REVIEW if field == "PRODUCT_NAME" else QueueCategory.NOT_LISTED
    )


@pytest.mark.parametrize("terminal", [None, "failed", "timed_out", "completed"])
def test_completion_proof_outranks_terminal_cleanup_but_not_newer_run(reviewed, terminal):
    c = reviewed
    acquire(c)
    s = snapshot(c)
    run = s.usage.runs[-1]
    seed(c, "usage", replace(s.usage, runs=(replace(run, terminal=terminal),)))
    p = projector(c)
    assert category(queue(p, c)) == QueueCategory.NOT_LISTED
    # A second run has the same input but distinct identity and no completion.
    seed(c, "usage", replace(s.usage, runs=(replace(run, terminal="completed"),)))
    binding = replace(run.binding, expected_observation_revision=1)
    second = c[0].shared.begin_run(c[6].capability_hash, c[1].incident_id, "queue-second", binding)
    s = snapshot(c)
    seed(
        c, "usage", replace(s.usage, runs=(*s.usage.runs[:-1], replace(second, terminal=terminal)))
    )
    assert category(queue(p, c)) == QueueCategory.RENEWED_REVIEW
    assert not view(c).current


def test_projection_is_pure_and_rejects_unprepared_or_changed_derivative(reviewed, monkeypatch):
    c = reviewed
    acquire(c)
    s = snapshot(c)
    p = projector(c)
    before = (s.evidence.model_dump_json(), s.actions.model_dump_json(), s.usage.model_dump_json())

    def forbidden(*args, **kwargs):
        raise AssertionError("projection attempted an I/O boundary")

    for port, name in [
        (c[7].guest, "resolve"),
        (c[7].guest, "image"),
        (c[7].store, "transact"),
        (c[8].store, "transact"),
        (c[7].guest.objects, "get"),
    ]:
        monkeypatch.setattr(port, name, forbidden)
    prepared = prepare(p, c, s)
    a = queue(p, c, s, prepared)
    b = queue(p, c, s, prepared)
    assert a == b and before == (
        s.evidence.model_dump_json(),
        s.actions.model_dump_json(),
        s.usage.model_dump_json(),
    )
    with pytest.raises(GuestDenied, match="retail_projection_not_prepared"):
        queue(p, c, s, prepared.record)
    with pytest.raises(ValueError, match="prepared_projection_changed"):
        dataclass_replace(
            prepared, record=replace(prepared.record, original_observation_hash="f" * 64)
        )
    assert type(prepared.record).model_validate_json(prepared.original) == prepared.record
    forbidden_text = ("redacted_output_json", "reserved_nanos", "project_id", "reviewed_images")
    assert not any(item in prepared.original.decode() for item in forbidden_text)


@pytest.mark.parametrize(
    "state", ["missing", "expired", "future", "foreign", "wrong_capability", "too_long"]
)
def test_unsubstantiated_capability_is_unknown(reviewed, state):
    c = reviewed
    observed = capability(c)
    now = c[3][5][0]
    if state == "missing":
        observed = None
    elif state == "expired":
        observed = replace(observed, observed_at=now - timedelta(seconds=60), valid_until=now)
    elif state == "future":
        observed = replace(observed, observed_at=now + timedelta(seconds=1))
    elif state == "foreign":
        observed = replace(observed, session_id="f" * 32)
    elif state == "wrong_capability":
        observed = replace(observed, capability="SAVED_EVIDENCE")
    else:
        observed = replace(observed, valid_until=now + timedelta(seconds=61))
    result = capability_view(
        observed, now, RetailReadPolicy(), c[6].scope.session_id, "NEW_VERIFICATION"
    )
    assert result.state == CapabilityState.UNKNOWN


@pytest.mark.parametrize(
    "field,value",
    [
        ("projection_bytes", 0),
        ("snapshot_bytes", True),
        ("context_bytes", "128"),
        ("capability_validity_seconds", float("inf")),
    ],
)
def test_invalid_operational_policy_rejected(field, value):
    with pytest.raises(ValidationError):
        RetailReadPolicy(**{field: value})


def test_effective_byte_limits_reach_actual_consumer(reviewed):
    c = reviewed
    acquire(c)
    p = projector(c)
    s = snapshot(c)
    result = prepare(p, c, s)
    assert len(result.original) <= p.policy.projection_bytes
    with pytest.raises(GuestDenied, match="retail_snapshot_unavailable"):
        prepare(projector(c, replace(p.policy, projection_bytes=1)), c, s)
    small = projector(
        c, RetailReadPolicy(projection_bytes=100, context_bytes=100, snapshot_bytes=101)
    )
    with pytest.raises(GuestDenied):
        prepare(small, c, s)


def test_scope_membership_filter_and_material_validation(reviewed):
    c = reviewed
    acquire(c)
    p = projector(c)
    s = snapshot(c)
    prepared = prepare(p, c, s)
    with pytest.raises(GuestDenied):
        p.view(c[6].capability_hash, s.guest, s.usage, (), s.environment)
    with pytest.raises(GuestDenied):
        p.view(c[6].capability_hash, s.guest, s.usage, (prepared, prepared), s.environment)
    with pytest.raises(GuestDenied):
        queue(p, c, s, prepared, selected_filter="ALL")
    with pytest.raises(GuestDenied):
        p.project(
            c[6].capability_hash,
            s,
            material=MaterialUpdate(
                changed_at=c[3][5][0], sequence=1, semantic_state_hash="f" * 64, reference="unbound"
            ),
        )
    c[3][5][0] = s.guest.scope.expires_at
    with pytest.raises(GuestDenied, match="guest_expired_or_invalid"):
        queue(p, c, s, prepared)


def bound_context(c):
    """Explicit synthetic context, never an amendment to reviewed source facts."""
    from batchbeacon.source_context import ContextManifest, RecallContext

    notice = snapshot(c).environment.notices[0]
    fact = dict(state="STATED", text="Synthetic recall context", locator="synthetic test")
    item = RecallContext(
        source_id=notice.dependency.version,
        source_url=notice.original_url,
        capture_sha256=notice.dependency.content_hash,
        citation_label="Synthetic citation",
        human_review="PENDING",
        attribution="Synthetic fixture",
        **{
            name: fact
            for name in (
                "reason",
                "basis",
                "health_risks",
                "affected_products",
                "total_quantity",
                "businesses",
                "company_action",
                "regulatory_action",
                "legal_action",
                "consumer_advice",
                "geography",
            )
        },
        related_documents=dict(
            state="PRESENT",
            locator="Synthetic parent link",
            documents=(
                dict(
                    title="Synthetic company notice",
                    url="https://manufacturer.example/notice.pdf",
                    kind="COMPANY_CUSTOMER_NOTICE",
                    format="PDF",
                    locator="Synthetic link",
                    link_observed_on=notice.published_at,
                    link_basis="OBSERVED_ON_PARENT_PAGE",
                    contents_reviewed=False,
                ),
            ),
        ),
    )
    return ContextManifest(
        version="recall-context-draft-1", status="HUMAN_REVIEW_PENDING", notices=(item,)
    ), notice


def test_exact_context_binding_keeps_links_pending_and_historical_notice(reviewed):
    c = reviewed
    acquire(c)
    contexts, notice = bound_context(c)
    p = RetailProjector(
        c[8], c[0].shared.policy, RetailReadPolicy(), contexts=contexts, context_notices=(notice,)
    )
    s = snapshot(c)
    prepared = prepare(p, c, s)
    v = queue(p, c, s, prepared)
    context = v.contexts[0].notices[0]
    assert context.reason.state == "STATED" and context.human_review == "PENDING"
    assert context.authority == notice.authority and context.jurisdictions == notice.jurisdictions
    assert (context.original_url, context.final_url) == (notice.original_url, notice.final_url)
    assert context.related_documents == contexts.notices[0].related_documents
    assert not context.related_documents.documents[0].contents_reviewed
    assert context.interpretation == "COMPARED_NOTICE"
    new = replace(notice.dependency, epoch=notice.dependency.epoch + 1)
    environment = replace(
        s.environment, notices=(), context=replace(s.environment.context, current_sources=(new,))
    )
    changed = queue(p, c, dataclass_replace(s, environment=environment), prepared)
    assert category(changed) == QueueCategory.RENEWED_REVIEW
    assert changed.snapshot.current_sources == (new,)
    assert changed.contexts[0].notices[0] == context


@pytest.mark.parametrize("mismatch", ["family", "version", "hash", "url", "unbound"])
def test_context_cannot_migrate_between_notice_bindings(reviewed, mismatch):
    c = reviewed
    acquire(c)
    contexts, notice = bound_context(c)
    if mismatch in {"version", "hash"}:
        field = "source_id" if mismatch == "version" else "capture_sha256"
        contexts = replace(
            contexts,
            notices=(
                replace(
                    contexts.notices[0],
                    **{field: "other-version" if mismatch == "version" else "f" * 64},
                ),
            ),
        )
    elif mismatch == "url":
        contexts = replace(
            contexts,
            notices=(replace(contexts.notices[0], source_url="https://other.example/notice"),),
        )
    elif mismatch == "family":
        notice = replace(notice, dependency=replace(notice.dependency, family="other-family"))
    p = RetailProjector(
        c[8],
        c[0].shared.policy,
        RetailReadPolicy(),
        contexts=contexts,
        context_notices=() if mismatch == "unbound" else (notice,),
    )
    context = queue(p, c).contexts[0].notices[0]
    assert context.reason.state == "UNKNOWN" and context.related_documents.state == "UNKNOWN"
    assert context.human_review == "UNKNOWN"


def test_ambiguous_context_family_is_rejected(reviewed):
    contexts, notice = bound_context(reviewed)
    other = replace(notice, dependency=replace(notice.dependency, family="other-family"))
    with pytest.raises(ValueError, match="ambiguous source-family"):
        RetailProjector(
            reviewed[8],
            reviewed[0].shared.policy,
            RetailReadPolicy(),
            contexts=contexts,
            context_notices=(notice, other),
        )


@pytest.mark.parametrize(
    "mutation",
    [
        "missing",
        "late",
        "mutable",
        "future",
        "before_run",
        "run_id",
        "session_id",
        "incident_id",
        "binding_hash",
        "deadline",
        "extraction_hash",
        "observation_hash",
        "result_hash",
        "extraction_key",
        "verification_key",
        "observation_revision",
        "result_revision",
    ],
)
def test_compact_completion_witness_cannot_sustain_unproved_result(reviewed, mutation):
    c = reviewed
    acquire(c)
    s = snapshot(c)
    proof, run = s.completion, s.usage.runs[-1]
    now = c[3][5][0]
    if mutation == "missing":
        proof = None
    elif mutation == "late":
        proof = dataclass_replace(proof, created_at=run.deadline, updated_at=run.deadline)
    elif mutation == "mutable":
        proof = dataclass_replace(proof, updated_at=proof.updated_at + timedelta(microseconds=1))
    elif mutation == "future":
        proof = dataclass_replace(
            proof, created_at=now + timedelta(seconds=1), updated_at=now + timedelta(seconds=1)
        )
    elif mutation == "before_run":
        proof = dataclass_replace(
            proof,
            created_at=run.started_at - timedelta(microseconds=1),
            updated_at=run.started_at - timedelta(microseconds=1),
        )
    else:
        value = (
            run.deadline + timedelta(seconds=1)
            if mutation == "deadline"
            else 2
            if mutation.endswith("revision")
            else "f" * 64
            if mutation.endswith("hash")
            else "f" * 32
        )
        proof = dataclass_replace(proof, record=replace(proof.record, **{mutation: value}))
        # Exercise the deeper binding check, not only the run's receipt digest.
        run = replace(run, completion_hash=proof.record.digest())
    s = dataclass_replace(s, completion=proof, usage=replace(s.usage, runs=(run,)))
    result = queue(projector(c), c, s)
    assert not result.snapshot.rows[0].current
    assert category(result) == QueueCategory.RENEWED_REVIEW


def test_full_history_is_validated_before_corrections_are_stripped(reviewed):
    c = reviewed
    acquire(c)
    before = view(c)
    c[7].correct(
        c[2], c[1].incident_id, "queue-history", 1, "PRODUCT_NAME", before.observation.identity.name
    )
    s = snapshot(c)
    latest = s.evidence.observations[-1]
    forged = replace(
        latest.observation,
        identity=replace(
            latest.observation.identity,
            resolved_name="Forged identity",
            resolution_review_hash="f" * 64,
        ),
    )
    state = replace(
        s.evidence,
        observations=(*s.evidence.observations[:-1], replace(latest, observation=forged)),
    )
    with pytest.raises(GuestDenied, match="identity_history_unavailable"):
        prepare(projector(c), c, dataclass_replace(s, evidence=state))


def test_twenty_incidents_are_complete_and_stably_sorted_with_unchanged_filter_counts(reviewed):
    c = reviewed
    acquire(c)
    for index in range(19):
        c[7].guest.create_incident(c[2], f"queue-draft-{index}")
    s = snapshot(c)
    p = projector(c)
    prepared = tuple(prepare(p, c, snapshot(c, item.id)) for item in s.guest.incidents)
    result = p.view(c[6].capability_hash, s.guest, s.usage, prepared, s.environment)
    assert len(result.snapshot.rows) == sum(result.snapshot.category_counts.values()) == 20
    assert result.visible_incident_ids == tuple(sorted(i.id for i in s.guest.incidents))
    negative = p.view(
        c[6].capability_hash,
        s.guest,
        s.usage,
        prepared,
        s.environment,
        selected_filter=QueueFilter.NOT_LISTED,
    )
    assert negative.visible_incident_ids == (c[1].incident_id,)
    assert negative.snapshot.category_counts == result.snapshot.category_counts
    assert negative.snapshot.count_scope == "BOUNDED_SHOP"
    material = tuple(r.last_material_update for r in result.snapshot.rows)
    c[3][5][0] += timedelta(seconds=1)
    later = p.view(c[6].capability_hash, s.guest, s.usage, prepared, s.environment)
    assert tuple(r.last_material_update for r in later.snapshot.rows) == material
    assert later.snapshot.generated_at > result.snapshot.generated_at
    # Configured row ceiling is enforced without truncation, independently of creation cap.
    gp = replace(c[7].guest.policy, retail=replace(c[7].guest.policy.retail, max_summary_rows=19))
    c[7].guest.policy = gp
    p = RetailProjector(
        c[8], replace(c[0].shared.policy, guest_policy_hash=gp.digest()), RetailReadPolicy()
    )
    with pytest.raises(GuestDenied, match="retail_snapshot_unavailable"):
        p.view(
            c[6].capability_hash,
            replace(s.guest, policy_hash=gp.digest()),
            s.usage,
            (),
            s.environment,
        )


def test_known_empty_differs_from_unavailable_and_foreign_owner(reviewed):
    c = reviewed
    token, guest = c[7].guest.issue()
    from tests.unit.test_firestore_store import saved

    usage = saved(c[3], "usage", guest.capability_hash)
    environment = snapshot(c).environment
    p = projector(c)
    empty = p.view(guest.capability_hash, guest, usage, (), environment)
    assert empty.snapshot.rows == () and sum(empty.snapshot.category_counts.values()) == 0
    for bad_usage, bad_environment in (
        (None, environment),
        (usage, None),
        (snapshot(c).usage, environment),
    ):
        with pytest.raises(GuestDenied):
            p.view(guest.capability_hash, guest, bad_usage, (), bad_environment)
    with pytest.raises(GuestDenied):
        p.view(c[6].capability_hash, guest, usage, (), environment)


def test_byte_and_capability_policy_exact_boundaries_reach_consumers(reviewed):
    c = reviewed
    acquire(c)
    s = snapshot(c)
    base = projector(c)
    n = len(prepare(base, c, s).original)
    assert len(prepare(projector(c, replace(base.policy, projection_bytes=n)), c, s).original) == n
    with pytest.raises(GuestDenied):
        prepare(projector(c, replace(base.policy, projection_bytes=n - 1)), c, s)
    observed = replace(capability(c), valid_until=c[3][5][0] + timedelta(seconds=61))
    assert (
        queue(base, c, s, new_verification=observed).new_verification.state
        == CapabilityState.UNKNOWN
    )
    expanded = projector(c, replace(base.policy, capability_validity_seconds=61))
    assert (
        queue(expanded, c, s, new_verification=observed).new_verification.state
        == CapabilityState.AVAILABLE
    )


@pytest.mark.parametrize("reviewed", [(0,)], indirect=True)
def test_snapshot_basis_binds_capability_category_and_time(reviewed):
    c = reviewed
    c[5][0]["label"]["best_before"] = unknown(kind="DATE")
    acquire(c)
    p, s = projector(c), snapshot(c)
    prepared = prepare(p, c, s)
    a = queue(p, c, s, prepared)
    b = queue(p, c, s, prepared, new_verification=capability(c))
    assert category(a) == QueueCategory.HUMAN_REVIEW
    assert category(b) == QueueCategory.NEEDS_EVIDENCE
    assert a.snapshot.currentness_basis_hash != b.snapshot.currentness_basis_hash
    assert a.snapshot.id != b.snapshot.id
    c[3][5][0] += timedelta(seconds=1)
    later = queue(p, c, s, prepared)
    assert a.snapshot.currentness_basis_hash != later.snapshot.currentness_basis_hash


def test_reconstructed_prepared_wrapper_cannot_restore_untimely_completion(reviewed):
    c = reviewed
    acquire(c)
    s = snapshot(c)
    late = s.completion.record.deadline + timedelta(microseconds=1)
    bad = dataclass_replace(
        s, completion=dataclass_replace(s.completion, created_at=late, updated_at=late)
    )
    p = projector(c)
    prepared = prepare(p, c, bad)
    assert not queue(p, c, bad, prepared).snapshot.rows[0].current
    witness = replace(
        prepared.record.acquisition.completion,
        created_at=s.completion.created_at,
        updated_at=s.completion.updated_at,
    )
    changed = replace(
        prepared.record, acquisition=replace(prepared.record.acquisition, completion=witness)
    )
    reconstructed = dataclass_replace(
        prepared, record=changed, original=changed.model_dump_json().encode()
    )
    with pytest.raises(GuestDenied, match="retail_projection_not_prepared"):
        queue(p, c, bad, reconstructed)


def test_snapshot_serialized_byte_boundary_applies_to_complete_view(reviewed):
    c = reviewed
    for index in range(19):
        c[7].guest.create_incident(c[2], f"bytes-draft-{index}")
    s = snapshot(c)
    snapshots = tuple(snapshot(c, i.id) for i in s.guest.incidents)
    p = projector(c)
    prepared = tuple(prepare(p, c, item) for item in snapshots)
    value = p.view(c[6].capability_hash, s.guest, s.usage, prepared, s.environment)
    size = len(value.model_dump_json().encode())
    projection_size = max(len(item.original) for item in prepared)
    for difference in (0, -1):
        bounded = projector(
            c,
            RetailReadPolicy(
                projection_bytes=projection_size,
                context_bytes=128,
                snapshot_bytes=size + difference,
            ),
        )
        selected = tuple(prepare(bounded, c, item) for item in snapshots)
        if difference == 0:
            actual = bounded.view(c[6].capability_hash, s.guest, s.usage, selected, s.environment)
            assert len(actual.model_dump_json().encode()) == size
        else:
            with pytest.raises(GuestDenied, match="retail_snapshot_unavailable"):
                bounded.view(c[6].capability_hash, s.guest, s.usage, selected, s.environment)


def test_context_serialized_byte_boundary_and_manifest_binding(reviewed):
    import json

    contexts, notice = bound_context(reviewed)
    payload = {
        "manifest": contexts.model_dump(mode="json"),
        "notices": [RetailProjector._notice_metadata(notice)],
    }
    size = len(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode())
    options = dict(contexts=contexts, context_notices=(notice,))
    p = RetailProjector(
        reviewed[8], reviewed[0].shared.policy, RetailReadPolicy(context_bytes=size), **options
    )
    assert p.context_binding_hash
    with pytest.raises(ValueError, match="context manifest exceeds"):
        RetailProjector(
            reviewed[8],
            reviewed[0].shared.policy,
            RetailReadPolicy(context_bytes=size - 1),
            **options,
        )


@pytest.mark.parametrize("terminal", ["failed", "timed_out", "completed", "expired", "running"])
def test_no_result_acquisition_distinguishes_processing_from_review(reviewed, terminal):
    c = reviewed
    c[5][0]["source"]["products"].pop()
    acquire(c)
    s = snapshot(c)
    assert not s.evidence.results
    run = s.usage.runs[-1]
    if terminal in {"expired", "running"}:
        run = replace(run, terminal=None)
        if terminal == "expired":
            c[3][5][0] = run.deadline
    else:
        run = replace(run, terminal=terminal)
    s = dataclass_replace(s, usage=replace(s.usage, runs=(run,)))
    assert category(queue(projector(c), c, s)) == (
        QueueCategory.IN_PROGRESS if terminal == "running" else QueueCategory.HUMAN_REVIEW
    )


def test_complete_twenty_one_cannot_be_silently_truncated(reviewed):
    from batchbeacon.guest_service import GuestIncident
    from batchbeacon.shared_admission import IncidentUsage

    c, p = reviewed, projector(reviewed)
    s = snapshot(c)
    incidents = tuple(
        GuestIncident(id=f"{i:032x}", request_key=f"synthetic-{i}") for i in range(1, 22)
    )
    guest = replace(s.guest, incidents=incidents)
    usage = replace(s.usage, incidents=tuple(IncidentUsage(incident_id=i.id) for i in incidents))
    prepared = []
    for incident in incidents:
        own = dataclass_replace(
            s,
            guest=guest,
            usage=usage,
            evidence=replace(s.evidence, incident_id=incident.id),
            actions=replace(s.actions, incident_id=incident.id),
        )
        prepared.append(prepare(p, c, own))
    with pytest.raises(GuestDenied, match="retail_snapshot_unavailable"):
        p.view(c[6].capability_hash, guest, usage, tuple(prepared), s.environment)


def test_material_update_requires_bound_aware_nonfuture_time_and_stable_order(reviewed):
    c, p = reviewed, projector(reviewed)
    second = c[7].guest.create_incident(c[2], "material-second")
    original_time = c[3][5][0]
    first_snapshot = snapshot(c)
    first = prepare(p, c, first_snapshot)
    c[3][5][0] += timedelta(seconds=1)
    s = snapshot(c, second.id)
    later = prepare(p, c, s)
    v = p.view(c[6].capability_hash, s.guest, s.usage, (first, later), s.environment)
    assert v.visible_incident_ids == (second.id, c[1].incident_id)
    assert v.visible_count == 2
    for changed_at in (original_time - timedelta(seconds=1), c[3][5][0] + timedelta(seconds=1)):
        with pytest.raises(GuestDenied, match="retail_material_state_unavailable"):
            p.project(
                c[6].capability_hash,
                s,
                material=replace(later.record.material, changed_at=changed_at),
            )
    with pytest.raises(ValidationError):
        replace(later.record.material, changed_at=original_time.replace(tzinfo=None))
    with pytest.raises(ValidationError):
        replace(later.record.material, sequence=0)


def test_projection_and_view_recheck_expiry_at_exit(reviewed, monkeypatch):
    c, p = reviewed, projector(reviewed)
    s = snapshot(c)
    prepared = prepare(p, c, s)
    original = p._bound

    def expire(record, limit):
        original(record, limit)
        c[3][5][0] = s.guest.scope.expires_at

    monkeypatch.setattr(p, "_bound", expire)
    with pytest.raises(GuestDenied, match="guest_expired_or_invalid"):
        prepare(p, c, s)
    c[3][5][0] = s.guest.scope.issued_at
    with pytest.raises(GuestDenied, match="guest_expired_or_invalid"):
        queue(p, c, s, prepared)


@pytest.mark.parametrize("reviewed", [(0,)], indirect=True)
def test_exhausted_verification_allowance_cannot_offer_actionable_recapture(reviewed):
    c = reviewed
    c[5][0]["label"]["best_before"] = unknown(kind="DATE")
    acquire(c)
    p = projector(c)
    assert category(queue(p, c, new_verification=capability(c))) == QueueCategory.NEEDS_EVIDENCE
    for index in range(c[0].shared.policy.max_verifications - 1):
        reverify(c, f"queue-verification-{index}")
    s = snapshot(c)
    assert len(s.usage.incidents[0].verifications) == c[0].shared.policy.max_verifications
    assert s.usage.incidents[0].acquisitions < 1 + c[0].shared.policy.max_recaptures
    assert category(queue(p, c, s, new_verification=capability(c))) == QueueCategory.HUMAN_REVIEW


def test_new_own_verification_reservation_invalidates_old_projection_basis(reviewed):
    c = reviewed
    acquire(c)
    p, s = projector(c), snapshot(c)
    prepared = prepare(p, c, s)
    binding = c[7].verification_binding(c[2], c[1].incident_id)
    c[0].shared.reserve_verification(
        c[6].capability_hash, c[1].incident_id, "queue-reserved", binding
    )
    changed = snapshot(c)
    assert changed.evidence == s.evidence and changed.actions == s.actions
    with pytest.raises(GuestDenied, match="retail_snapshot_unavailable"):
        queue(p, c, changed, prepared)
    assert material_state_hash(changed) != material_state_hash(s)
