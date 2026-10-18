"""Source-context completeness and notice-version binding, not human approval."""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from batchbeacon.app import app
from batchbeacon.source_context import (
    ContextFact,
    ContextManifest,
    RelatedDocument,
    RelatedDocuments,
)

ROOT = Path(__file__).resolve().parents[2]


def test_context_preserves_all_source_versions_without_approving_predicates():
    manifest = ContextManifest.model_validate_json(
        (ROOT / 'fixtures/sources/context.draft.json').read_text()
    )
    sources = json.loads((ROOT / 'fixtures/sources/manifest.draft.json').read_text())['sources']
    assert {n.source_id for n in manifest.notices} == {s['id'] for s in sources}
    for notice in manifest.notices:
        source = next(s for s in sources if s['id'] == notice.source_id)
        assert notice.source_url == source['url']
        assert notice.capture_sha256 == source['capture_sha256']
        assert notice.human_review == 'PENDING'
        assert notice.total_quantity.state == 'NOT_STATED'
        assert notice.total_quantity.text is None
        assert notice.legal_action.state == 'NOT_STATED'
    assert 'Possible' in manifest.notices[0].reason.text
    assert 'was found' in manifest.notices[1].basis.text
    assert 'Wales' not in manifest.notices[1].geography.text
    assert 'Wales' in manifest.notices[2].geography.text


@pytest.mark.parametrize('state,text', [('STATED', None), ('NOT_STATED', '0'),
                                        ('UNKNOWN', 'No legal action')])
def test_absence_and_unknown_cannot_be_fabricated_facts(state, text):
    with pytest.raises(ValidationError):
        ContextFact(state=state, text=text, locator='Complete notice')


def test_preview_serves_draft_context_without_trusted_source_status():
    response = TestClient(app).get('/prototype/refined/source-context.json')
    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'HUMAN_REVIEW_PENDING'
    assert len(data['notices']) == 3
    assert all(n['human_review'] == 'PENDING' for n in data['notices'])


def test_customer_documents_preserve_version_and_link_only_provenance():
    manifest = ContextManifest.model_validate_json(
        (ROOT / 'fixtures/sources/context.draft.json').read_text())
    assert manifest.notices[0].related_documents.state == 'UNKNOWN'
    original, update = manifest.notices[1:]
    a, b = (n.related_documents.documents[0] for n in (original, update))
    assert a.url != b.url
    assert '/FSA-PRIN-47-2026/' in a.url
    assert '/FSA-PRIN-47-2026-update-1/' in b.url
    assert a.title.startswith('Customer notice: World of Sweets')
    assert b.title.startswith('Customer notice: Alyan')
    assert not a.contents_reviewed and not b.contents_reviewed
    assert str(a.link_observed_on) == '2026-10-18'
    assert original.capture_sha256 != update.capture_sha256


@pytest.mark.parametrize('url', ['javascript:alert(1)', 'http://example.com/a.pdf',
    'https://user:password@example.com/a.pdf', 'https://example.com/a b.pdf'])
def test_customer_documents_reject_unsafe_links(url):
    data = json.loads((ROOT / 'fixtures/sources/context.draft.json').read_text())
    document = data['notices'][1]['related_documents']['documents'][0]
    with pytest.raises(ValidationError):
        RelatedDocument.model_validate_json(json.dumps(document | {'url': url}))


def test_unverified_links_cannot_be_claimed_present_or_absent_with_documents():
    with pytest.raises(ValidationError):
        RelatedDocuments(state='PRESENT', documents=(), locator='Unknown')
    data = ContextManifest.model_validate_json(
        (ROOT / 'fixtures/sources/context.draft.json').read_text())
    with pytest.raises(ValidationError):
        RelatedDocuments(state='UNKNOWN', documents=data.notices[1].related_documents.documents,
                         locator='Unknown')
