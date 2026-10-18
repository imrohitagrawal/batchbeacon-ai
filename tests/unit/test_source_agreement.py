"""Actual proposal validation must precede per-acquisition source agreement."""
import asyncio

import pytest

from batchbeacon.contracts import ActionType
from batchbeacon.evidence_service import replace
from batchbeacon.extraction_service import SourceBundle
from batchbeacon.guest_service import GuestDenied
from tests.unit.test_firestore_store import no_network_or_credentials as no_network_or_credentials  # noqa
from tests.unit.test_firestore_store import saved
from tests.unit.test_firestore_store import setup as setup  # noqa
from tests.unit.test_reviewed_extraction import build_reviewed
from tests.unit.test_shared_admission import env as env  # noqa


def unproven(setup, env):
    c = build_reviewed(setup, env, (0,))
    service = c[0]
    old = service.sources['first']
    notice = replace(old.notice, source_proposal_agrees=False)
    from types import MappingProxyType
    service.sources = MappingProxyType({'first': SourceBundle(notice, old.original)})
    stores, server = setup[:2]
    environment = replace(saved(setup, 'environment'), notices=(notice,))
    server.seed(stores._encode(stores.name('environment'), 'environment', environment))
    return c


def test_first_proposal_establishes_agreement_without_changing_source(setup, env):
    c = unproven(setup, env)
    status = asyncio.run(c[0].acquire(c[2], c[1]))
    view = c[7].read_evidence(c[2], c[1].incident_id)
    proof = view.observation.source_agreement
    assert status.current and view.hold_eligible and len(c[4]) == 2
    assert proof == view.state.extractions[0].envelope.source_agreement
    assert proof.run_id == status.run_id
    assert not saved(setup, 'environment').notices[0].source_proposal_agrees
    c[8].prepare(c[2], c[1].incident_id, ActionType.SIMULATED_HOLD)
    # Correction preserves original source validation but needs a new result.
    lot = view.observation.fields[0].observation
    c[7].correct(c[2], c[1].incident_id, 'same-lot', 1, 'LOT', lot)
    assert c[7].read_evidence(c[2], c[1].incident_id).observation.source_agreement == proof


def test_disagreement_cannot_create_source_receipt(setup, env):
    c = unproven(setup, env)
    c[5][0]['source']['jurisdictions'] = ['GB']
    status = asyncio.run(c[0].acquire(c[2], c[1]))
    view = c[7].read_evidence(c[2], c[1].incident_id)
    assert not status.current and not view.state.observations
    assert view.state.extractions[0].envelope.source_agreement is None


@pytest.mark.parametrize('field', ['run_id', 'binding_hash', 'notice_digest', 'schema_hash'])
def test_tampered_persisted_agreement_denies_owned_evidence(setup, env, field):
    c = unproven(setup, env)
    asyncio.run(c[0].acquire(c[2], c[1]))
    state = c[7].read_evidence(c[2], c[1].incident_id).state
    extraction = state.extractions[0]
    proof = replace(extraction.envelope.source_agreement,
                    **{field: 'f' * (32 if field == 'run_id' else 64)})
    state = replace(state, extractions=(replace(extraction,
        envelope=replace(extraction.envelope, source_agreement=proof)),))
    stores, server = setup[:2]
    server.seed(stores._encode(stores.name('evidence', c[6].capability_hash, c[1].incident_id),
                               'evidence', state))
    with pytest.raises(GuestDenied, match='source_agreement_unavailable'):
        c[7].read_evidence(c[2], c[1].incident_id)


def test_source_semantic_change_invalidates_agreement_without_epoch_change(setup, env):
    c = unproven(setup, env)
    asyncio.run(c[0].acquire(c[2], c[1]))
    stores, server = setup[:2]
    old = saved(setup, 'environment')
    source = replace(old.notices[0], source_available=False)
    server.seed(stores._encode(stores.name('environment'), 'environment',
                               replace(old, notices=(source,))))
    assert not c[7].read_evidence(c[2], c[1].incident_id).current
    with pytest.raises(GuestDenied):
        c[8].prepare(c[2], c[1].incident_id, ActionType.SIMULATED_HOLD)
