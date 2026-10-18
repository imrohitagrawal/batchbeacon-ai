"""Explicit loopback Firestore integration; not deployed IAM/Storage/model proof.

Run only with BATCHBEACON_EMULATOR_CONFIG pointing to a private, provenance-
admitted server configuration. This module never starts a server or uses ADC.
"""

import json
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from uuid import uuid4

import google.auth
import grpc
import pytest
from google.api_core import exceptions
from google.api_core.client_options import ClientOptions
from google.auth.credentials import AnonymousCredentials
from google.cloud.firestore_v1.services.firestore import FirestoreClient
from google.cloud.firestore_v1.services.firestore.transports.grpc import FirestoreGrpcTransport

from batchbeacon.action_service import ActionConfirmation, ActionPolicy, ActionService
from batchbeacon.contracts import ActionType, VerifierPolicy
from batchbeacon.evidence_service import (
    EvidenceEnvironment,
    EvidencePolicy,
    EvidenceService,
    replace,
)
from batchbeacon.firestore_store import FirestorePolicy, FirestoreStores
from batchbeacon.guest_service import GuestDenied, GuestPolicy, GuestService
from batchbeacon.shared_admission import SharedAdmission
from tests.unit.domain_fixtures import NOW, context, known, notice
from tests.unit.test_firestore_store import extract
from tests.unit.test_guest_boundary import ORIGIN, MemoryObjects
from tests.unit.test_shared_admission import env as env

pytestmark = pytest.mark.skipif(not os.environ.get("BATCHBEACON_EMULATOR_CONFIG"),
                                reason="explicit admitted loopback emulator required")


def seed(stores, record):
    name = stores.name("environment")
    def change(tx):
        old = tx.read({name: "environment"})[name]
        tx.write(name, "environment", record, create=old is None)
    stores.run(change)


def open_instance(policy, now, objects):
    channel = grpc.insecure_channel(policy.api_endpoint)
    transport = FirestoreGrpcTransport(channel=channel, credentials=AnonymousCredentials(),
                                        host=policy.api_endpoint)
    client = FirestoreClient(transport=transport,
        client_options=ClientOptions(api_endpoint=policy.api_endpoint))
    gp, ep, ap = GuestPolicy(origin=ORIGIN), EvidencePolicy(), ActionPolicy()
    stores = FirestoreStores(client, policy, gp, ep, ap, clock=lambda: now[0])
    guest = GuestService(gp, stores.guests, objects, clock=lambda: now[0])
    evidence = EvidenceService(guest, stores.evidence, ep)
    actions = ActionService(evidence, stores.actions, ap)
    return (stores, None, guest, evidence, actions, now), channel


@pytest.fixture
def runtime(monkeypatch):
    def no_credentials(*args, **kwargs):
        raise AssertionError("emulator must never discover credentials")
    monkeypatch.setattr(google.auth, "default", no_credentials)
    config = json.loads(Path(os.environ["BATCHBEACON_EMULATOR_CONFIG"]).read_text())
    assert config["host"] == "127.0.0.1" and config["project_id"].startswith("demo-")
    endpoint = f'127.0.0.1:{config["rpc_port"]}'
    policy = FirestorePolicy(project_id=config["project_id"], database_id=config["database_id"],
        namespace="integration_" + uuid4().hex, environment_id="first_slice",
        mode="emulator", api_endpoint=endpoint, rpc_seconds=config["rpc_seconds"],
        operation_seconds=config["operation_seconds"], cleanup_seconds=config["cleanup_seconds"],
        max_transaction_attempts=config["transaction_attempts"])
    now, objects = [NOW], MemoryObjects()
    channels, instances = [], []
    for _ in range(2):
        instance, channel = open_instance(policy, now, objects)
        channels.append(channel)
        instances.append(instance)
    seed(instances[0][0], EvidenceEnvironment(context=context(), notices=(notice(),),
                                              verifier_policy=VerifierPolicy()))
    yield instances
    for channel in channels:
        channel.close()


def prepared(runtime, env):
    first = runtime[0]
    stores, _, guest, evidence, actions, _ = first
    token, session = guest.issue()
    incident = guest.create_incident(token, "first")
    envelope = extract(first, token, incident)
    policy = replace(env[0].policy, project_id=stores.policy.project_id)
    grant = replace(env[0].grant, project_id=policy.project_id, policy_hash=policy.digest())
    admission = SharedAdmission(policy, grant, stores.shared, clock=lambda: first[5][0])
    binding = evidence.verification_binding(token, incident.id)
    admission.reserve_verification(session.capability_hash, incident.id, "verify", binding)
    evidence.publish_verification(token, incident.id, "verify", binding)
    target = actions.prepare(token, incident.id, ActionType.SIMULATED_HOLD)
    return token, session, incident, envelope, ActionConfirmation(
        target=target, explicit_confirmation=True)


def test_fresh_guest_atomic_creation_and_independent_client_restart(runtime):
    first, second = runtime
    token, session = first[2].issue()
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(r[2].create_incident, token, "same") for r in runtime]
        incidents = [f.result() for f in futures]
    assert incidents[0] == incidents[1]
    iid = incidents[0].id
    assert len(second[2].resolve(token).incidents) == 1
    assert second[3].read_evidence(token, iid).observation is None
    assert second[4].list_actions(token, iid) == ()
    stores = second[0]
    budget = stores.run(lambda tx: tx.read({stores.name("budget"): "budget"}))
    assert budget[stores.name("budget")] is None
    cold, channel = open_instance(stores.policy, first[5], first[2].objects)
    try:
        assert cold[2].resolve(token).incidents[0].id == iid
        assert cold[3].read_evidence(token, iid).state.incident_id == iid
    finally:
        channel.close()


def test_lost_ack_after_actual_commit_reconciles_on_other_client(runtime):
    first, second = runtime
    token, session = first[2].issue()
    call = first[0]._call
    def lost(method, request, *args):
        result = call(method, request, *args)
        if method == "commit" and len(request.writes) == 4:
            raise exceptions.DeadlineExceeded("injected response loss after real emulator commit")
        return result
    first[0]._call = lost
    with pytest.raises(GuestDenied):
        first[2].create_incident(token, "lost")
    retained = second[2].resolve(token)
    assert len(retained.incidents) == 1
    reconciled = second[2].create_incident(token, "lost")
    assert reconciled == retained.incidents[0]
    assert second[3].read_evidence(token, reconciled.id).observation is None


def test_concurrent_confirmation_then_correction_preserves_history(runtime, env):
    token, session, incident, envelope, command = prepared(runtime, env)
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(r[4].confirm, token, incident.id, f"confirm-{i}", command)
                   for i, r in enumerate(runtime)]
        views = [f.result() for f in futures]
    assert views[0].action.id == views[1].action.id
    assert len(runtime[1][4].list_actions(token, incident.id)) == 1
    runtime[0][3].correct(token, incident.id, "lot-edit", 1, "LOT",
                         known("000aB", evidence=envelope.captures[0]))
    reread = runtime[1][3].read_evidence(token, incident.id)
    assert not reread.current
    assert reread.state.observations[0].observation.fields[0].observation.value == "232511"
    assert reread.observation.fields[0].observation.value == "000aB"
    assert runtime[1][4].get_action(token, incident.id, views[0].action.id).requires_renewed_review


def test_source_update_racing_confirmation_never_renews_old_result(runtime, env):
    token, session, incident, _, command = prepared(runtime, env)
    source = notice().dependency
    changed = EvidenceEnvironment(context=replace(context(),
        current_sources=(replace(source, epoch=source.epoch + 1),)),
        notices=(notice(),), verifier_policy=VerifierPolicy())
    def confirm():
        try:
            return runtime[0][4].confirm(token, incident.id, "race", command)
        except GuestDenied as exc:
            assert exc.status in {409, 503}  # bounded contention may require renewed review
            return None
    with ThreadPoolExecutor(max_workers=2) as pool:
        action = pool.submit(confirm)
        update = pool.submit(seed, runtime[1][0], changed)
        update.result()
        result = action.result()
    assert not runtime[1][3].read_evidence(token, incident.id).current
    if result:
        history = runtime[1][4].get_action(token, incident.id, result.action.id)
        assert history.requires_renewed_review
    with pytest.raises(GuestDenied):
        runtime[1][4].prepare(token, incident.id, ActionType.SIMULATED_HOLD)
