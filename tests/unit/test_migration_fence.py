"""Old SDK transactions must fail closed across conditional metadata migration."""
from pathlib import Path

import pytest
from google.cloud.firestore_v1.types import Document, Value

from batchbeacon.action_service import ActionConfirmation, ActionService
from batchbeacon.contracts import ActionType
from batchbeacon.evidence_service import EvidenceService, replace
from batchbeacon.firestore_store import FirestoreStores
from batchbeacon.guest_service import GuestDenied, GuestService
from batchbeacon.learning_decisions import GuidanceLimits
from batchbeacon.learning_evaluator import EvaluationPolicy, LearningEvaluator, PreparedSuite
from batchbeacon.retail_projection import RetailProjector, RetailReadPolicy
from batchbeacon.shared_admission import SharedAdmission
from tests.unit.domain_fixtures import known
from tests.unit.firestore_rpc_fake import client
from tests.unit.test_firestore_store import no_network_or_credentials as no_network_or_credentials
from tests.unit.test_firestore_store import setup as setup
from tests.unit.test_reviewed_extraction import acquire, build_reviewed
from tests.unit.test_shared_admission import env as env


@pytest.mark.parametrize(('operation', 'field'), [
    ('action', 'retail_policy_hash'), ('correction', 'learning_policy_hash')])
def test_stale_existing_writer_cannot_commit_across_migration(setup, env, operation, field):
    def configure(stores, actions, shared):
        p = EvaluationPolicy(retail=stores.guest_policy.retail,
            limits=GuidanceLimits.from_shared(shared.policy))
        suite = PreparedSuite.load(Path('fixtures/learning/inputs.json').read_bytes(),
            Path('fixtures/learning/expectations.json').read_bytes(), p)
        evaluator = LearningEvaluator(suite, p, wall_clock=lambda: setup[5][0],
            monotonic_clock=lambda: 0.)
        stores.enable_retail(RetailProjector(actions, shared.policy, RetailReadPolicy()))
        stores.enable_learning(actions.evidence, shared.policy, evaluator)

    c = build_reviewed(setup, env, (0,), configure=configure)
    assert acquire(c).current
    stores, server, guest, *_ = setup
    key, iid = c[6].capability_hash, c[1].incident_id
    command = ActionConfirmation(target=c[8].prepare(c[2], iid,
        ActionType.SIMULATED_HOLD), explicit_confirmation=True)
    view = c[7].read_evidence(c[2], iid)
    nc = replace(c[0].config, run_seconds=50, request_timeout_seconds=40.0)
    p = replace(c[0].shared.policy, run_seconds=50, model_configuration_hash=nc.digest())
    g = replace(c[0].shared.grant, policy_hash=p.digest())
    other = FirestoreStores(client(server), stores.policy, stores.guest_policy,
        stores.evidence_policy, stores.action_policy, clock=lambda: setup[5][0])
    og = GuestService(guest.policy, other.guests, guest.objects, clock=guest.clock)
    oe = EvidenceService(og, other.evidence, stores.evidence_policy, identities=c[7].identities)
    oa = ActionService(oe, other.actions, stores.action_policy)
    newshared = SharedAdmission(p, g, other.shared, clock=lambda: setup[5][0])
    configure(other, oa, newshared)
    gn = stores.name('guest', key)
    newhash = (other.retail.projector.configuration_hash if field == 'retail_policy_hash'
        else other.learning.configuration_hash)
    expected, triggered = {}, [False]
    wanted = 'actions' if operation == 'action' else 'evidence'

    def before(request):
        if triggered[0] or not any(w.update.fields['kind'].string_value == wanted
                                  for w in request.writes):
            return
        triggered[0] = True
        gd = Document(server.docs[gn])
        gd.fields[field] = Value(string_value=newhash)
        server.seed(gd)
        expected.update({n: Document(d) for n, d in server.docs.items()})

    server.before_commit = before
    with pytest.raises(GuestDenied) as error:
        if operation == 'action':
            c[8].confirm(c[2], iid, 'fenced-action', command)
        else:
            c[7].correct(c[2], iid, 'fenced-correction', view.observation.revision,
                'LOT', known('000aB', evidence=view.state.extractions[-1].envelope.captures[0]))
    assert error.value.status == 503
    assert triggered[0] and server.aborts == 1
    assert server.docs == expected
