"""IR01–18 exact reviewed synthetic identity; no inference or new human review."""

import copy
import json
from hashlib import sha256
from pathlib import Path

import pytest
from pydantic import ValidationError

from batchbeacon.contracts import (
    EvidenceKind,
    EvidenceRef,
    IdentifierKind,
    ObservedIdentifier,
    ValueType,
)
from batchbeacon.evidence_service import ExtractedIdentity, ExtractedValues, replace
from batchbeacon.identity_resolution import (
    AdmittedIdentities,
    IdentityAdmission,
    IdentityCatalog,
    decide_identity,
)
from batchbeacon.uploads import UploadPolicy, sanitize_images
from tests.unit.domain_fixtures import known, notice, unknown

CATALOG = Path('fixtures/synthetic/identity-catalog.json')
PIN = '379e96b96b2f10bc1ac9beecc72d6950d6727c3532aed024e070710db0543164'


def admitted():
    return AdmittedIdentities.load(CATALOG.read_bytes(), IdentityAdmission(catalog_sha256=PIN))


def refs(*indices):
    catalog = admitted().catalog
    return tuple(EvidenceRef(kind=EvidenceKind.CAPTURE, artifact_id=str(i + 1) * 32,
        sha256=catalog.identities[index].approved_image_sha256, locator='original entire image')
        for i, index in enumerate(indices))


def values(index=2, captures=None):
    captures = captures or refs(index)
    entry = admitted().catalog.identities[index]
    return ExtractedValues(identity=ExtractedIdentity(name=known(entry.name, evidence=captures[0]),
        pack=known(entry.pack_text, evidence=captures[-1])), fields=())


def decision(value=None, captures=None, catalog=None):
    captures = captures or refs(2)
    return decide_identity(catalog or admitted(), value or values(captures=captures), captures,
                           (notice().dependency,))


def test_catalog_is_exact_identity_only_derivation_of_existing_approval():
    catalog = admitted().catalog
    label_bytes = Path('fixtures/synthetic/manifest.json').read_bytes()
    source_bytes = Path('fixtures/sources/sfa-reviewed.json').read_bytes()
    labels, source = json.loads(label_bytes), json.loads(source_bytes)
    assert sha256(label_bytes).hexdigest() == catalog.admitted_manifest_sha256
    assert sha256(source_bytes).hexdigest() == catalog.approved_source_record_sha256
    review = labels['human_review']
    assert review == source['human_review']
    canonical = json.dumps(review, sort_keys=True, separators=(',', ':')).encode()
    assert sha256(canonical).hexdigest() == catalog.existing_review_record_sha256
    assert review['reviewed_label_manifest_sha256'] == \
        catalog.historical_reviewed_label_manifest_sha256
    assert catalog.historical_reviewed_label_manifest_sha256 != catalog.admitted_manifest_sha256
    for entry, fixture in zip(catalog.identities, labels['fixtures'], strict=True):
        raw = Path(fixture['path']).read_bytes()
        assert fixture['human_review'] == 'APPROVED' and fixture['synthetic']
        assert sha256(raw).hexdigest() == fixture['sha256'] == entry.approved_image_sha256
        assert (entry.name, entry.pack_text) == (fixture['identity'], f"{fixture['pack_g']} g")
        sanitized, = sanitize_images((raw,), UploadPolicy())
        assert sanitized.data == raw
        assert (sanitized.width, sanitized.height) == (entry.width, entry.height)
    forbidden = {'lot', 'best_before', 'expected_case', 'proposed_result', 'verdict'}
    assert not forbidden & set(IdentityCatalog.model_fields)
    assert not forbidden & set(type(catalog.identities[0]).model_fields)


@pytest.mark.parametrize('change', ['pin', 'bytes', 'size', 'entries'])
def test_catalog_admission_fails_closed(change):
    raw = CATALOG.read_bytes()
    policy = IdentityAdmission(catalog_sha256=PIN)
    if change == 'pin':
        policy = replace(policy, catalog_sha256='a' * 64)
    elif change == 'bytes':
        raw += b' '
    elif change == 'size':
        policy = replace(policy, max_catalog_bytes=len(raw) - 1)
    else:
        policy = replace(policy, max_identities=2)
    with pytest.raises(ValueError):
        AdmittedIdentities.load(raw, policy)


@pytest.mark.parametrize('field,value', [('max_catalog_bytes', 0), ('max_identities', -1),
    ('max_identities', True), ('max_identities', '3')])
def test_invalid_admission_configuration(field, value):
    with pytest.raises(ValidationError):
        IdentityAdmission(catalog_sha256=PIN, **{field: value})


@pytest.mark.parametrize('mutation', ['duplicate_hash', 'duplicate_id', 'missing_review', 'gold'])
def test_malformed_catalog_cannot_be_admitted_even_with_its_own_hash(mutation):
    data = json.loads(CATALOG.read_bytes())
    if mutation == 'duplicate_hash':
        data['identities'][1]['approved_image_sha256'] = \
            data['identities'][0]['approved_image_sha256']
    elif mutation == 'duplicate_id':
        data['identities'][1]['fixture_id'] = data['identities'][0]['fixture_id']
    elif mutation == 'missing_review':
        del data['existing_review_record_sha256']
    else:
        data['identities'][2]['proposed_result'] = 'NOT_LISTED_IN_CHECKED_NOTICES'
    raw = json.dumps(data).encode()
    with pytest.raises(ValidationError):
        AdmittedIdentities.load(raw, IdentityAdmission(catalog_sha256=sha256(raw).hexdigest()))


@pytest.mark.parametrize('index', [0, 1, 2])
@pytest.mark.parametrize('panels', [1, 2])
def test_exact_reviewed_input_agreement_resolves_without_verdict(index, panels):
    captures = refs(*([index] * panels))
    value = values(index, captures)
    before = value.model_dump_json()
    result = decision(value, captures)
    assert result.state == 'RESOLVED' and result.entry == admitted().catalog.identities[index]
    assert value.model_dump_json() == before and not hasattr(result, 'verdict')


@pytest.mark.parametrize('field', ['name', 'pack'])
@pytest.mark.parametrize('ambiguous', [False, True])
def test_unknown_required_identity_is_not_filled(field, ambiguous):
    original = values()
    value = replace(original, identity=replace(original.identity,
        **{field: unknown(ambiguous, value_type=ValueType.TEXT)}))
    before = value.model_dump_json()
    assert decision(value).state == 'UNRESOLVED' and value.model_dump_json() == before


@pytest.mark.parametrize('field', ['name', 'pack'])
@pytest.mark.parametrize('other_unknown', [False, True])
def test_known_conflict_precedes_unknown_field(field, other_unknown):
    original = values()
    other = 'pack' if field == 'name' else 'name'
    changes = {field: known('Camembert Superieur Au Lait Cru' if field == 'name' else '500 g',
                            evidence=refs(2)[0])}
    if other_unknown:
        changes[other] = unknown(value_type=ValueType.TEXT)
    value = replace(original, identity=replace(original.identity, **changes))
    assert decision(value).state == 'DISAGREES'


@pytest.mark.parametrize('kind', ['PRODUCT_CODE', 'GTIN'])
@pytest.mark.parametrize('state', ['KNOWN', 'AMBIGUOUS', 'UNKNOWN'])
def test_unsupported_identifier_cannot_create_an_alternate_positive(kind, state):
    original = values(0, refs(0))
    observed = known('123', evidence=refs(0)[0]) if state == 'KNOWN' else unknown(
        state == 'AMBIGUOUS', value_type=ValueType.TEXT)
    identity = replace(original.identity, identifiers=(ObservedIdentifier(kind=IdentifierKind(kind),
                                                                         observation=observed),))
    result = decision(replace(original, identity=identity), refs(0))
    assert result.state == ('RESOLVED' if state == 'UNKNOWN' else 'DISAGREES')


@pytest.mark.parametrize('indices', [(0, 1), (0, 2), (1, 2)])
def test_mixed_recognized_panels_disagree_even_when_name_unknown(indices):
    captures = refs(*indices)
    original = values(captures=captures)
    value = replace(original, identity=replace(original.identity, name=unknown()))
    assert decision(value, captures).state == 'DISAGREES'


@pytest.mark.parametrize('conflict', [False, True])
def test_unlisted_extra_prevents_proof_but_does_not_hide_known_conflict(conflict):
    original = refs(2, 2)
    captures = (original[0], replace(original[1], sha256='f' * 64))
    value = values(captures=captures)
    if conflict:
        value = replace(value, identity=replace(value.identity, name=known('Wrong name',
                                                                            evidence=captures[0])))
    assert decision(value, captures).state == ('DISAGREES' if conflict else 'UNRESOLVED')


def test_unlisted_changed_image_and_unconfigured_resolver_never_grant_exclusion():
    captures = (replace(refs(2)[0], sha256='f' * 64),)
    assert decision(values(captures=captures), captures).state == 'UNRESOLVED'
    assert decide_identity(None, values(), refs(2), (notice().dependency,)).state == 'UNRESOLVED'


@pytest.mark.parametrize('field', ['name', 'pack'])
def test_identity_support_cannot_point_to_unselected_capture(field):
    value = values()
    wrong = replace(refs(2)[0], artifact_id='f' * 32)
    observed = replace(getattr(value.identity, field), evidence=(wrong,))
    value = replace(value, identity=replace(value.identity, **{field: observed}))
    assert decision(value).state == 'DISAGREES'


def test_source_scope_and_model_resolution_authority_stay_separate():
    dependency = replace(notice().dependency, content_hash='f' * 64)
    assert decide_identity(admitted(), values(), refs(2), (dependency,)).state == 'UNRESOLVED'
    with pytest.raises(ValidationError):
        ExtractedIdentity.model_validate(values().identity.model_dump() |
                                          {'resolved_name': 'trusted'})


def test_identity_projection_does_not_depend_on_gold_outcomes():
    labels = json.loads(Path('fixtures/synthetic/manifest.json').read_text())
    def only_identity(document):
        return [(row['identity'], row['pack_g'], row['sha256']) for row in document['fixtures']]
    altered = copy.deepcopy(labels)
    for row in altered['fixtures']:
        row.update(expected_case='private-test', proposed_result='REVIEW_REQUIRED',
                   lot='different', best_before_raw='different')
    assert only_identity(labels) == only_identity(altered)


def test_constructed_catalog_cannot_keep_admission_for_different_identity_bytes():
    from dataclasses import replace as dataclass_replace
    original = admitted()
    changed = replace(original.catalog, identities=(
        replace(original.catalog.identities[0], name='Different identity'),
        *original.catalog.identities[1:]))
    with pytest.raises(ValueError, match='identity_catalog_admission_failed'):
        dataclass_replace(original, catalog=changed)
