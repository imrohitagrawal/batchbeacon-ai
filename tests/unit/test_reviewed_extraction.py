"""Actual approved synthetic PNGs through ADK/mock HTTP and SDK/fake RPC.

The source text is an explicitly synthetic test representation of reviewed facts,
so its matching test catalog scope is re-bound here only. No source approval changes.
"""

import asyncio
import copy
import json
from hashlib import sha256
from importlib.metadata import version
from pathlib import Path

import httpx
import pytest

from batchbeacon.action_service import ActionService
from batchbeacon.contracts import ActionType
from batchbeacon.evidence_service import EvidenceEnvironment, EvidenceService, replace
from batchbeacon.extraction_service import AcquisitionCommand, ExtractionService, SourceBundle
from batchbeacon.guest_service import GuestDenied
from batchbeacon.identity_resolution import AdmittedIdentities, IdentityAdmission
from batchbeacon.model_runtime import ExtractionConfig
from batchbeacon.shared_admission import SharedAdmission
from batchbeacon.uploads import sanitize_images
from tests.unit.domain_fixtures import context
from tests.unit.durable_fixtures import wire_response
from tests.unit.test_extraction_proposal import known, rig, unknown
from tests.unit.test_firestore_store import no_network_or_credentials as no_network_or_credentials  # noqa
from tests.unit.test_firestore_store import owned, saved
from tests.unit.test_firestore_store import setup as setup  # noqa
from tests.unit.test_identity_resolution import CATALOG
from tests.unit.test_probe_runner import credentials
from tests.unit.test_shared_admission import env as env  # noqa


@pytest.fixture
def reviewed(setup, env, request):
    indices = getattr(request, 'param', (2,))
    stores, server, guest, old_evidence, _, now = setup
    server.clock = lambda: now[0]
    proposal, source, notice, _ = rig()
    projection = json.loads(CATALOG.read_bytes())
    projection['source_scope']['capture_sha256'] = notice.dependency.content_hash
    raw_catalog = json.dumps(projection).encode()
    admission = IdentityAdmission(catalog_sha256=sha256(raw_catalog).hexdigest())
    identities = AdmittedIdentities.load(raw_catalog, admission)
    ep = replace(old_evidence.policy, identity_admission=admission)
    stores.evidence_policy = ep
    evidence = EvidenceService(guest, stores.evidence, ep, identities=identities)
    actions = ActionService(evidence, stores.actions, stores.action_policy)
    config = ExtractionConfig(mode='offline_test', project_id='synthetic-project',
        model_id='gemini-3.8-flash', model_location='global', api_version='v1beta1',
        adk_version=version('google-adk'), genai_version=version('google-genai'),
        identity_resolution_policy_hash=admission.digest())
    p = replace(env[0].policy, model_configuration_hash=config.digest(),
                run_seconds=config.run_seconds)
    grant = replace(env[0].grant, policy_hash=p.digest())
    shared = SharedAdmission(p, grant, stores.shared, clock=lambda: now[0])
    shared.initialize(env[7])
    shared.activate_phase(env[1].state().phase)
    token, session, incident = owned(setup)
    entries = identities.catalog.identities
    images = tuple(Path('fixtures/synthetic/' + entries[index].fixture_id + '.png').read_bytes()
                   for index in indices)
    batch = guest.retain(token, incident.id, 'upload',
                         sanitize_images(images, guest.policy.uploads))
    environment = EvidenceEnvironment(context=replace(context(),
        current_sources=(notice.dependency,)), notices=(notice,),
        verifier_policy=saved(setup, 'environment').verifier_policy)
    server.seed(stores._encode(stores.name('environment'), 'environment', environment))
    proposal['label']['name'] = known(entries[indices[0]].name)
    proposal['label']['best_before'] = known('2026-10-17', kind='DATE', panel=len(indices) - 1)
    calls, output = [], [proposal]
    async def fake(request):
        calls.append(request)
        if str(request.url).endswith(':countTokens'):
            return httpx.Response(200, json={'totalTokens': 100})
        return httpx.Response(200, content=wire_response(candidates=[{
            'content': {'role': 'model', 'parts': [{'text': json.dumps(output[0])}]},
            'finishReason': 'STOP', 'index': 0}]))
    service = ExtractionService(evidence, shared, config, {'first': SourceBundle(notice, source)},
        transport_factory=lambda: httpx.MockTransport(fake), credentials_factory=credentials)
    command = AcquisitionCommand(incident_id=incident.id, request_key='reviewed-extraction',
        source_selection='first', capture_ids=tuple(c.id for c in batch.captures),
        expected_observation_revision=0)
    return service, command, token, setup, calls, output, session, evidence, actions


def acquire(c, **changes):
    return asyncio.run(c[0].acquire(c[2], replace(c[1], **changes)))


def view(c):
    return c[7].read_evidence(c[2], c[1].incident_id)


@pytest.mark.parametrize('reviewed', [(0,), (1,), (2,), (2, 2)], indirect=True)
def test_actual_approved_images_have_bound_proof_and_deterministic_result(reviewed):
    c = reviewed
    before = copy.deepcopy(c[5][0])
    status = acquire(c)
    assert status.state == 'COMPLETE' and status.current
    result = view(c)
    proof = result.state.extractions[0].identity_receipt
    assert proof is not None
    assert proof.values_hash == result.state.extractions[0].envelope.values.digest()
    assert proof.captures == result.observation.captures
    assert result.observation.identity.resolved_name == c[5][0]['label']['name']['value']
    assert result.observation.identity.resolution_review_hash == \
        c[0].evidence.identities.catalog.historical_reviewed_label_manifest_sha256
    is_third = proof.resolved_name == 'Meadow Vale Brie'
    assert result.result.verdict == ('NOT_LISTED_IN_CHECKED_NOTICES' if is_third
                                     else 'MATCHED_HOLD_FOR_REVIEW')
    assert result.hold_eligible is not is_third
    assert c[5][0] == before and acquire(c) == status and len(c[4]) == 2
    attempt = next(iter(saved(c[3], 'usage', c[6].capability_hash).runs))
    assert attempt.completion_hash and proof.run_binding_hash == attempt.binding.digest()
    sent = json.loads(c[4][1].content)
    assert 'Meadow Vale Brie' not in json.dumps(sent['contents'][0]['parts'][0])
    assert 'historical_reviewed_label_manifest' not in c[4][1].content.decode()


@pytest.mark.parametrize('mutation', ['name_a', 'name_b', 'pack', 'known_code', 'ambiguous_code'])
def test_recognized_image_model_conflict_retained_as_review_without_values(reviewed, mutation):
    c = reviewed
    label = c[5][0]['label']
    if mutation in ('name_a', 'name_b'):
        label['name'] = known(c[5][0]['source']['products'][mutation == 'name_b']['name'])
    elif mutation == 'pack':
        label['pack'] = known('500 g')
    else:
        code = known('123') if mutation == 'known_code' else unknown(kind='TEXT', ambiguous=True)
        label['identifiers'] = [{'kind': 'GTIN', 'observation': code}]
    before = copy.deepcopy(c[5][0])
    status = acquire(c)
    assert status.state == 'REVIEW_REQUIRED' and not status.current
    assert status.diagnostics == ('IDENTITY_EVIDENCE_DISAGREEMENT',)
    result = view(c)
    assert len(result.state.extractions) == 1 and not result.state.observations
    assert not result.state.results and result.state.extractions[0].identity_receipt is None
    assert result.state.extractions[0].envelope.values is None
    assert c[5][0] == before and len(c[4]) == 2


@pytest.mark.parametrize('field', ['name', 'pack'])
@pytest.mark.parametrize('ambiguous', [False, True])
def test_incomplete_identity_stays_typed_and_unresolved(reviewed, field, ambiguous):
    c = reviewed
    c[5][0]['label'][field] = unknown(kind='TEXT', ambiguous=ambiguous)
    status = acquire(c)
    result = view(c)
    assert status.state == 'REVIEW_REQUIRED' and status.current
    assert getattr(result.observation.identity, field).state == (
        'AMBIGUOUS' if ambiguous else 'UNKNOWN')
    assert result.observation.identity.resolved_name is None
    assert result.state.extractions[0].identity_receipt is None and not result.hold_eligible


@pytest.mark.parametrize('reviewed', [(0, 2), (0, 1)], indirect=True)
def test_mixed_original_images_never_resolve_from_only_first_panel(reviewed):
    status = acquire(reviewed)
    assert status.state == 'REVIEW_REQUIRED' and not status.current
    assert not view(reviewed).state.observations


@pytest.mark.parametrize('mutation', ['values_hash', 'run_binding_hash', 'catalog_hash',
    'captures', 'sources', 'removed', 'first_observation'])
def test_tampered_identity_proof_or_first_observation_fails_closed(reviewed, mutation):
    c = reviewed
    status = acquire(c)
    state = view(c).state
    original = state.extractions[0]
    if mutation == 'first_observation':
        first = state.observations[0]
        identity = replace(first.observation.identity, resolved_name='Different reviewed name')
        state = replace(state, observations=(replace(first,
            observation=replace(first.observation, identity=identity)),))
    else:
        proof = original.identity_receipt
        if mutation == 'removed':
            proof = None
        elif mutation == 'captures':
            proof = replace(proof, captures=(replace(proof.captures[0], artifact_id='f' * 32),))
        elif mutation == 'sources':
            proof = replace(proof, sources=(replace(proof.sources[0], epoch=2),))
        else:
            proof = replace(proof, **{mutation: 'f' * 64})
        state = replace(state, extractions=(replace(original, identity_receipt=proof),))
    stores, server = c[3][:2]
    server.seed(stores._encode(stores.name('evidence', c[6].capability_hash, c[1].incident_id),
                               'evidence', state))
    with pytest.raises(GuestDenied, match='identity_history_unavailable'):
        view(c)
    with pytest.raises(GuestDenied):
        c[0].status(c[2], status.run_id)
    with pytest.raises(GuestDenied):
        c[8].prepare(c[2], c[1].incident_id, ActionType.SIMULATED_HOLD)


@pytest.mark.parametrize('field', ['PRODUCT_NAME', 'PACK', 'LOT', 'BEST_BEFORE'])
def test_correction_preserves_original_proof_and_only_retains_unchanged_identity(reviewed, field):
    from tests.unit.domain_fixtures import known as observed
    c = reviewed
    acquire(c)
    before = view(c)
    proof = before.state.extractions[0].identity_receipt
    attribute = 'name' if field == 'PRODUCT_NAME' else 'pack'
    replacement = (getattr(before.observation.identity, attribute)
        if field in {'PRODUCT_NAME', 'PACK'} else
        next(item.observation for item in before.observation.fields if item.field == field))
    c[7].correct(c[2], c[1].incident_id, 'correction', 1, field,
                 observed(replacement.value, replacement.value_type,
                          evidence=replacement.evidence[0]))
    after = view(c)
    assert after.state.extractions[0].identity_receipt == proof
    assert not after.current and not after.hold_eligible
    assert (after.observation.identity.resolved_name is None) == (field in {'PRODUCT_NAME', 'PACK'})


def test_catalog_and_effective_configuration_must_agree(reviewed):
    c = reviewed
    from batchbeacon.model_runtime import ModelFailure
    with pytest.raises(ValueError, match='identity_catalog_policy_mismatch'):
        EvidenceService(c[3][2], c[3][0].evidence, c[7].policy)
    with pytest.raises((ValueError, ModelFailure)):
        ExtractionService(c[7], c[0].shared,
            replace(c[0].config, identity_resolution_policy_hash=None), dict(c[0].sources),
            transport_factory=c[0].transport_factory, credentials_factory=credentials)


def test_publication_recomputes_identity_even_if_coordinator_gate_is_skipped(reviewed, monkeypatch):
    c = reviewed
    c[5][0]['label']['name'] = known(c[5][0]['source']['products'][0]['name'])
    original = c[7].identity_decision
    calls = [0]
    def omitted_once(*args):
        from batchbeacon.identity_resolution import IdentityDecision
        calls[0] += 1
        return IdentityDecision(state='UNRESOLVED') if calls[0] == 1 else original(*args)
    monkeypatch.setattr(c[7], 'identity_decision', omitted_once)
    status = acquire(c)
    assert not status.current and not view(c).state.observations
    assert calls[0] >= 2


@pytest.mark.parametrize('mutation', ['resolved_name', 'review_hash', 'restore_name',
    'restore_pack', 'unresolved_gain', 'name', 'pack', 'codes', 'captures',
    'dropped_correction', 'changed_correction'])
def test_corrected_history_cannot_gain_or_move_identity_authority(reviewed, mutation):
    from batchbeacon.contracts import IdentifierKind, ObservedIdentifier
    from tests.unit.domain_fixtures import known as observed
    c = reviewed
    if mutation == 'unresolved_gain':
        c[5][0]['label']['pack'] = unknown(kind='TEXT')
    status = acquire(c)
    before = view(c)
    original = before.observation.identity
    field = {'restore_name': 'PRODUCT_NAME', 'restore_pack': 'PACK'}.get(mutation, 'LOT')
    old = (original.name if field == 'PRODUCT_NAME' else original.pack if field == 'PACK'
           else next(v.observation for v in before.observation.fields if v.field == 'LOT'))
    c[7].correct(c[2], c[1].incident_id, 'corrected-history', 1, field, old)
    state = view(c).state
    last = state.observations[-1]
    obs, identity = last.observation, last.observation.identity
    if mutation == 'resolved_name':
        identity = replace(identity, resolved_name='Camembert Superieur Au Lait Cru')
    elif mutation == 'review_hash':
        identity = replace(identity, resolution_review_hash='f' * 64)
    elif mutation.startswith('restore_') or mutation == 'unresolved_gain':
        identity = replace(identity, resolved_name='Meadow Vale Brie',
            resolution_review_hash=c[7].identities.catalog.historical_reviewed_label_manifest_sha256)
    elif mutation in {'name', 'pack'}:
        identity = replace(identity, **{mutation: observed('Changed identity',
            evidence=getattr(identity, mutation).evidence[0])})
    elif mutation == 'codes':
        identity = replace(identity, identifiers=(ObservedIdentifier(kind=IdentifierKind.GTIN,
            observation=observed('123', evidence=identity.name.evidence[0])),))
    elif mutation == 'captures':
        obs = replace(obs, captures=(*obs.captures, obs.captures[0]))
    elif mutation == 'dropped_correction':
        obs = replace(obs, corrections=())
    elif mutation == 'changed_correction':
        correction = obs.corrections[0]
        obs = replace(obs, corrections=(replace(correction,
            previous=observed('different previous', evidence=old.evidence[0])),))
    poisoned = replace(last, observation=replace(obs, identity=identity))
    state = replace(state, observations=(*state.observations[:-1], poisoned))
    stores, server = c[3][:2]
    server.seed(stores._encode(stores.name('evidence', c[6].capability_hash, c[1].incident_id),
                               'evidence', state))
    operations = (lambda: view(c), lambda: c[0].status(c[2], status.run_id),
        lambda: c[7].verification_binding(c[2], c[1].incident_id),
        lambda: c[8].prepare(c[2], c[1].incident_id, ActionType.SIMULATED_HOLD))
    for operation in operations:
        with pytest.raises(GuestDenied, match='identity_history_unavailable'):
            operation()


def test_reviewed_negative_action_denial_and_currentness_after_allowance_consumed(reviewed):
    from fastapi.testclient import TestClient

    from batchbeacon.contracts import LiveStatus
    from batchbeacon.incident_api import IncidentHTTPPolicy, create_incident_test_app
    c = reviewed
    acquire(c)
    for i in range(5):
        binding = c[7].verification_binding(c[2], c[1].incident_id)
        c[0].shared.reserve_verification(c[6].capability_hash, c[1].incident_id,
                                         f'negative-{i}', binding)
        c[7].publish_verification(c[2], c[1].incident_id, f'negative-{i}', binding)
    result = view(c)
    assert result.current and result.result.verdict == 'NOT_LISTED_IN_CHECKED_NOTICES'
    assert not result.hold_eligible
    guest = c[7].guest
    app = create_incident_test_app(guest, c[7], c[8], IncidentHTTPPolicy())
    with TestClient(app, base_url=guest.policy.origin) as client:
        client.cookies.set(guest.policy.cookie_name, c[2])
        path = f'/api/incidents/{c[1].incident_id}'
        response = client.get(path + '/evidence')
        assert response.status_code == 200 and response.json()['current']
        for kind in ActionType:
            with pytest.raises(GuestDenied, match='action_not_eligible'):
                c[8].prepare(c[2], c[1].incident_id, kind)
            assert client.get(path + '/actions/prepare', params={
                'action_type': kind.value}).status_code == 409
    stores, server = c[3][:2]
    environment = saved(c[3], 'environment')
    changed = replace(environment, context=replace(environment.context,
                                                   live_status=LiveStatus.FAILED))
    server.seed(stores._encode(stores.name('environment'), 'environment', changed))
    assert not view(c).current and not view(c).hold_eligible
