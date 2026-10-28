"""OPS-03a runtime emitter controls; all stores/providers are local fakes."""

import json

import pytest
from pydantic import ValidationError

from batchbeacon import admission_events
from batchbeacon.shared_admission import SharedDenied
from tests.unit import test_shared_admission
from tests.unit.durable_fixtures import record_wire, wire_response
from tests.unit.test_shared_admission import begin, claim, reserve

env = test_shared_admission.env


@pytest.fixture
def events(monkeypatch):
    records = []
    monkeypatch.setattr(admission_events._logger, 'info',
                        lambda wire: records.append(json.loads(wire)))
    return records


def expected(service, event):
    return dict(application='batchbeacon', origin='runtime', event=event,
                policy_hash=service.policy.digest(), grant_hash=service.grant.digest())


def test_allowance_denial_reports_once_outside_retry_callback(env, events):
    service, store, *_ = env
    phase = store.state().phase.model_copy(update={'max_pool_liability_nanos': 1})
    service.activate_phase(phase)
    run = begin(env, 'new')
    before = (store.budget, dict(store.usage), dict(store.attempts))
    with pytest.raises(SharedDenied, match='insufficient uncommitted'):
        reserve(env, run)
    assert events == [expected(service, 'allowance_exhausted')]
    assert before == (store.budget, store.usage, store.attempts)


@pytest.mark.parametrize('second_fails', [False, True])
def test_committed_circuit_report_survives_receipt_failure(env, events, second_fails):
    service, store, *_ = env
    run = begin(env)
    attempt = reserve(env, run)
    claim(env, run, attempt)
    record_wire(service, attempt, wire_response(12001, 1))
    original = store.transact
    calls = []
    def transact(address, callback):
        calls.append(address)
        if len(calls) == 2 and second_fails:
            raise ValueError('controlled receipt failure')
        return original(address, callback)
    store.transact = transact
    with pytest.raises((SharedDenied, ValueError)):
        service.reconcile(attempt.id)
    assert store.state().circuit == 'open_bound'
    assert events == [expected(service, 'cost_circuit_open')]
    assert store.state().balance(attempt.pool).lifetime_attempts == 1
    if second_fails:
        assert store.state().balance(attempt.pool).reserved_nanos == attempt.reserved_nanos


def test_success_and_foreign_owner_denial_do_not_report_exhaustion(env, events):
    run = begin(env)
    reserve(env, run)
    with pytest.raises(SharedDenied):
        env[0].reserve('foreign', run.id, 'a' * 32, 'b' * 64, operation_key='extract')
    assert events == []


def test_sink_failure_cannot_change_denial(env, monkeypatch):
    service, store, *_ = env
    phase = store.state().phase.model_copy(update={'max_pool_liability_nanos': 1})
    service.activate_phase(phase)
    run = begin(env, 'new')
    def fail(*args):
        raise OSError('controlled unavailable log sink')
    monkeypatch.setattr(admission_events._logger, 'info', fail)
    with pytest.raises(SharedDenied, match='insufficient uncommitted'):
        reserve(env, run)


def test_event_schema_rejects_private_fields_and_unknown_vocabulary():
    base = dict(event='allowance_exhausted', policy_hash='a' * 64, grant_hash='b' * 64)
    for extra in [dict(session_id='private'), dict(event='unknown'), dict(policy_hash='bad')]:
        with pytest.raises(ValidationError):
            admission_events.AdmissionEvent(**(base | extra))
