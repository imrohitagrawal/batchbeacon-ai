"""OR11: new extraction publication binds fresh selected source dependencies."""

import pytest
from pydantic import ValidationError

from batchbeacon.evidence_service import replace
from batchbeacon.guest_service import GuestDenied
from tests.unit.test_evidence_service import extract, publish, view
from tests.unit.test_evidence_service import rig as rig


def advance(store, field="epoch"):
    environment = store.environment
    notice = environment.notices[0]
    dependency = notice.dependency
    if field in {"epoch", "review_revision"}:
        changed = replace(dependency, **{field: getattr(dependency, field) + 1})
        review = replace(notice.review, revision=changed.review_revision)
        updated = replace(notice, dependency=changed, review=review)
    else:
        new_value = "f" * 64 if field == "content_hash" else "new-test-version"
        updated = type(notice).model_validate_json(notice.model_dump_json().replace(
            getattr(dependency, field), new_value))
    store.environment = replace(environment, notices=(updated,),
        context=replace(environment.context, current_sources=(updated.dependency,)))


@pytest.mark.parametrize("field", ["epoch", "version", "content_hash", "review_revision"])
def test_new_valid_extraction_rejects_changed_source_without_append(rig, field):
    advance(rig[1], field)
    with pytest.raises(GuestDenied) as caught:
        extract(rig)
    assert caught.value.code == "extraction_sources_changed"
    state = view(rig).state
    assert not state.extractions and not state.observations and not state.results


def test_source_changed_during_retained_object_read_is_checked_in_transaction(rig):
    objects, store = rig[0].guest.objects, rig[1]
    original = objects.get

    def changed(*args):
        result = original(*args)
        advance(store)
        return result

    objects.get = changed
    with pytest.raises(GuestDenied) as caught:
        extract(rig)
    assert caught.value.code == "extraction_sources_changed"
    assert not store.state(rig[3].capability_hash, rig[4].id).observations


def test_source_change_on_transaction_retry_rechecks_new_snapshot(rig):
    from batchbeacon.evidence_service import EvidenceSnapshot

    store = rig[1]
    original = store.transact
    callback_successes = []

    def retry(key, incident, change):
        snapshot = EvidenceSnapshot(store.guests.get(key), store.state(key, incident),
                                    store.environment, store.usage.get(key))
        callback_successes.append(change(snapshot))  # Uncommitted first attempt.
        advance(store)
        return original(key, incident, change)

    store.transact = retry
    with pytest.raises(GuestDenied) as caught:
        extract(rig)
    assert callback_successes and caught.value.code == "extraction_sources_changed"
    assert not store.state(rig[3].capability_hash, rig[4].id).observations


def test_committed_retry_after_source_change_is_history_without_reactivation(rig):
    first = extract(rig)
    publish(rig)
    advance(rig[1])
    before = view(rig).state
    assert not view(rig).current
    assert extract(rig) == first
    assert view(rig).state == before
    assert not view(rig).current and not view(rig).hold_eligible
    with pytest.raises(GuestDenied) as caught:
        extract(rig, envelope=replace(rig[5], redacted_output_json='{"changed":true}'))
    assert caught.value.code == "evidence_request_conflict"


def test_failed_stale_attempt_retained_without_reviving_prior_success(rig):
    extract(rig)
    publish(rig)
    advance(rig[1])
    original = rig[5]
    with pytest.raises(GuestDenied):
        extract(rig, key="stale-new", expected=1)
    failed = replace(original, validation="INVALID", values=None,
                     validation_codes=("SOURCE_DEPENDENCY_CHANGED",))
    extract(rig, key="failed-attempt", expected=1, envelope=failed)
    state = view(rig).state
    assert state.extractions[-1].envelope == failed
    assert state.extractions[-1].envelope.redacted_output_json == original.redacted_output_json
    assert len(state.observations) == 1 and state.active_result is None
    with pytest.raises(GuestDenied) as caught:
        publish(rig, key="retry-verification")
    assert caught.value.code == "latest_extraction_invalid"


def test_intentional_reverification_of_retained_observation_uses_new_reviewed_source(rig):
    extract(rig)
    publish(rig)
    old_observation = view(rig).observation
    advance(rig[1])
    assert not view(rig).current
    publish(rig, key="intentional-new-verification")
    assert view(rig).current and view(rig).hold_eligible
    assert view(rig).observation == old_observation
    assert len(view(rig).state.extractions) == 1


@pytest.mark.parametrize("change", ["empty", "duplicate", "extra", "context_mismatch",
                                    "empty_catalog", "duplicate_catalog"])
def test_selected_dependency_set_must_be_complete_unique_and_current(rig, change):
    store, envelope = rig[1], rig[5]
    environment = store.environment
    dependency = envelope.sources[0]
    if change == "empty":
        envelope = replace(envelope, sources=())
    elif change == "duplicate":
        envelope = replace(envelope, sources=envelope.sources * 2)
    elif change == "extra":
        envelope = replace(envelope, sources=(*envelope.sources,
            replace(dependency, family="unselected-test-source")))
    elif change == "context_mismatch":
        store.environment = replace(environment, context=replace(environment.context,
            current_sources=(replace(dependency, epoch=2),)))
    elif change == "empty_catalog":
        store.environment = replace(environment, notices=())
    else:
        store.environment = replace(environment, notices=environment.notices * 2)
    with pytest.raises(GuestDenied) as caught:
        extract(rig, envelope=envelope)
    assert caught.value.code == "extraction_sources_changed"


def test_duplicate_current_dependency_is_rejected_by_context_contract(rig):
    context = rig[1].environment.context
    with pytest.raises(ValidationError):
        replace(context, current_sources=context.current_sources * 2)


def test_unrelated_current_catalog_entry_does_not_expand_selected_extraction_scope(rig):
    environment = rig[1].environment
    extra = replace(environment.context.current_sources[0], family="unselected-test-source")
    rig[1].environment = replace(environment, context=replace(environment.context,
        current_sources=(*environment.context.current_sources, extra)))
    extract(rig)
    publish(rig)
    assert view(rig).current and view(rig).hold_eligible


def test_new_valid_extraction_requires_source_environment(rig):
    rig[1].environment = None
    with pytest.raises(GuestDenied) as caught:
        extract(rig)
    assert caught.value.code == "source_state_unavailable"


@pytest.mark.parametrize("omit_second", [False, True])
def test_all_selected_sources_required_with_order_independent_binding(rig, omit_second):
    environment, envelope = rig[1].environment, rig[5]
    second = replace(environment.notices[0], dependency=replace(
        environment.notices[0].dependency, family="second-selected-test-family"))
    rig[1].environment = replace(environment, notices=(*environment.notices, second),
        context=replace(environment.context,
                        current_sources=(*environment.context.current_sources, second.dependency)))
    if omit_second:
        with pytest.raises(GuestDenied) as caught:
            extract(rig)
        assert caught.value.code == "extraction_sources_changed"
    else:
        extract(rig, envelope=replace(envelope, sources=(second.dependency, *envelope.sources)))
        assert len(view(rig).state.observations) == 1
