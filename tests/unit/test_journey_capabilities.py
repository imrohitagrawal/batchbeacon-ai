"""Capabilities are owned, read-only projections, never dispatch permission."""
# ruff: noqa: F811
from datetime import timedelta
from uuid import uuid4

import httpx
import pytest

from batchbeacon.evidence_service import replace
from batchbeacon.guest_service import GuestDenied
from tests.unit.domain_fixtures import known
from tests.unit.test_extraction_api import api, start  # noqa: F401
from tests.unit.test_extraction_service import acquire, coordinator  # noqa: F401
from tests.unit.test_firestore_store import setup  # noqa: F401
from tests.unit.test_shared_admission import env  # noqa: F401


def test_capabilities_preserve_stale_completed_correction_and_make_no_writes(api):
    client, _, _, path, c, _ = api
    endpoint = path.removesuffix('/acquisitions')+'/capabilities'
    before = client.get(endpoint).json()
    assert before['workspace']['extraction']['available']
    assert not any(v['available'] for v in before['incident'].values())
    start(api)
    view = c[0].evidence.read_evidence(c[2], c[1].incident_id)
    c[0].evidence.correct(c[2], c[1].incident_id, 'edit', 1, 'LOT',
                         known('232511', evidence=view.observation.captures[0]))
    docs = dict(c[3][1].docs)
    response = client.get(endpoint)
    assert response.status_code == 200
    result = response.json()
    assert result['incident']['correction']['available']
    assert result['incident']['verification']['available']
    assert not result['incident']['action']['available']
    assert c[3][1].docs == docs and len(c[4]) == 2
    assert response.headers['cache-control'] == 'no-store, private'


def test_unresolved_attempt_blocks_new_case_without_hiding_completed_case_capabilities(coordinator):
    c = coordinator
    assert acquire(c).current
    guest = c[0].evidence.guest
    incident = guest.create_incident(c[2], 'second-case')
    from batchbeacon.uploads import sanitize_images
    from tests.unit.test_guest_boundary import picture
    batch = guest.retain(c[2], incident.id, 'image',
                         sanitize_images((picture(),), guest.policy.uploads))
    command = replace(c[1], incident_id=incident.id, request_key='second-check',
                      capture_ids=tuple(x.id for x in batch.captures))
    async def unavailable(request):
        if str(request.url).endswith(':countTokens'):
            return httpx.Response(200, json={'totalTokens':100})
        raise httpx.ReadTimeout('controlled unknown')
    c[0].transport_factory = lambda: httpx.MockTransport(unavailable)
    acquire(c, command)
    blank = guest.create_incident(c[2], 'blank-case')
    result = c[0].capabilities(c[2], blank.id)
    assert result.workspace.extraction.reason == 'UNRESOLVED_ATTEMPT'
    assert not result.workspace.extraction.available
    assert not result.incident.correction.available
    complete = c[0].capabilities(c[2], c[1].incident_id)
    assert not complete.workspace.extraction.available
    assert complete.incident.correction.available and complete.incident.action.available
    assert complete.incident.verification.available


@pytest.mark.parametrize('condition', ['missing', 'foreign', 'expired', 'unknown'])
def test_capability_endpoint_owns_every_read(api, condition):
    client, _, _, path, c, _ = api
    if condition == 'missing':
        client.cookies.clear()
    elif condition == 'foreign':
        token, _ = c[3][2].issue()
        client.cookies.set(c[3][2].policy.cookie_name, token)
    elif condition == 'expired':
        c[3][5][0] = c[6].scope.expires_at
    else:
        path = '/api/incidents/'+uuid4().hex+'/acquisitions'
    response = client.get(path.removesuffix('/acquisitions')+'/capabilities')
    assert response.status_code in (401,404)
    assert 'workspace' not in response.json() and not c[4]


def test_capability_read_expiring_during_storage_denies(coordinator):
    c = coordinator
    original = c[0].shared.operation_availability
    def late(*args):
        result = original(*args)
        c[3][5][0] = c[6].scope.expires_at + timedelta(seconds=1)
        return result
    c[0].shared.operation_availability = late
    with pytest.raises(GuestDenied):
        c[0].capabilities(c[2],c[1].incident_id)
