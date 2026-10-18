"""Pure projection of the approved SFA record and exact retained source bytes.

Admission hashes come from operator-reviewed inputs, not a public request. This
loader establishes neither a new human approval nor actual model agreement.
"""

import json
from dataclasses import dataclass
from datetime import date, datetime
from hashlib import sha256
from typing import Annotated

from pydantic import Field

from batchbeacon.contracts import (
    AffectedProductRule,
    AuthorityNotice,
    Digest,
    EvidenceKind,
    EvidenceRef,
    HumanReview,
    IdentityRule,
    Operator,
    PredicateField,
    PredicateRule,
    Record,
    SourceDependency,
    ValueType,
)
from batchbeacon.evidence_service import canonical
from batchbeacon.extraction_service import SourceBundle
from batchbeacon.identity_resolution import AdmittedIdentities, IdentityAdmission
from batchbeacon.uploads import UploadPolicy


class SourceAdmission(Record):
    reviewed_record_sha256: Digest
    retrieval_record_sha256: Digest
    identity_catalog_sha256: Digest
    label_manifest_sha256: Digest
    epoch: Annotated[int, Field(ge=1)]
    review_revision: Annotated[int, Field(ge=1)]
    max_original_bytes: Annotated[int, Field(gt=0)]
    max_record_bytes: Annotated[int, Field(gt=0)] = 65536


@dataclass(frozen=True)
class ReviewedSource:
    bundle: SourceBundle
    identities: AdmittedIdentities
    admission: SourceAdmission


def load_sfa(*, reviewed_record: bytes, retrieval_record: bytes, original: bytes,
             identity_catalog: bytes, label_manifest: bytes, images: tuple[bytes, ...],
             upload: UploadPolicy, admission: SourceAdmission) -> ReviewedSource:
    for raw, expected in (
        (reviewed_record, admission.reviewed_record_sha256),
        (retrieval_record, admission.retrieval_record_sha256),
        (identity_catalog, admission.identity_catalog_sha256),
        (label_manifest, admission.label_manifest_sha256),
    ):
        if type(raw) is not bytes or len(raw) > admission.max_record_bytes \
                or sha256(raw).hexdigest() != expected:
            raise ValueError('reviewed_source_admission_failed')
    doc, metadata = json.loads(reviewed_record), json.loads(retrieval_record)
    source, review = doc['source'], doc['human_review']
    catalog, manifest = json.loads(identity_catalog), json.loads(label_manifest)
    if type(original) is not bytes or not original or len(original) > admission.max_original_bytes \
            or sha256(original).hexdigest() != source['capture_sha256'] \
            or metadata['sha256'] != source['capture_sha256'] \
            or metadata['bytes'] != len(original) or metadata['exit'] != 0 \
            or metadata['url'] != source['url'] or metadata['response'] != '200 ' + source['url'] \
            or source['human_review'] != 'APPROVED' or source['authority'] != 'SFA' \
            or source['jurisdictions'] != ['SG']:
        raise ValueError('reviewed_source_capture_failed')
    if catalog['approved_source_record_sha256'] != admission.reviewed_record_sha256 \
            or catalog['admitted_manifest_sha256'] != admission.label_manifest_sha256 \
            or catalog['existing_review_record_sha256'] != canonical(review) \
            or manifest['human_review'] != review \
            or catalog['historical_reviewed_label_manifest_sha256'] != \
                review['reviewed_label_manifest_sha256'] \
            or catalog['historical_reviewed_packet_sha256'] != review['reviewed_packet_sha256'] \
            or catalog['source_scope'] != dict(family=source['family'], id=source['id'],
                capture_sha256=source['capture_sha256'], jurisdictions=source['jurisdictions']):
        raise ValueError('reviewed_source_lineage_failed')
    ref = EvidenceRef(kind=EvidenceKind.SOURCE, artifact_id=source['id'],
        sha256=source['capture_sha256'], locator='reviewed notice product table')
    products = []
    for index, product in enumerate(source['products']):
        if len(product['codes']) != 1 or product['codes'][0]['type'] != 'LOT' \
                or product['best_before']['mode'] != 'EXACT':
            raise ValueError('unsupported_reviewed_predicate')
        products.append(AffectedProductRule(id=f'sfa-{index}',
            identity=IdentityRule(canonical_name=product['name'],
                pack=f"{product['pack_g']} g", evidence=(ref,)),
            predicates=(PredicateRule(field=PredicateField.LOT, operator=Operator.EXACT,
                value_type=ValueType.TEXT, values=(product['codes'][0]['value'],), evidence=(ref,)),
                PredicateRule(field=PredicateField.BEST_BEFORE, operator=Operator.EXACT,
                value_type=ValueType.DATE, values=tuple(product['best_before']['values']),
                evidence=(ref,)))))
    notice = AuthorityNotice(dependency=SourceDependency(family=source['family'],
        version=source['id'], content_hash=source['capture_sha256'], epoch=admission.epoch,
        review_revision=admission.review_revision), authority=source['authority'],
        original_url=source['url'], final_url=source['url'],
        published_at=date.fromisoformat(source['published_date']),
        retrieved_at=datetime.fromisoformat(metadata['retrieved_at']),
        jurisdictions=tuple(source['jurisdictions']), review=HumanReview(
            revision=admission.review_revision, reviewer=review['reviewer'],
            reviewed_at=datetime.fromisoformat(review['reviewed_at']),
            record_hash=review['reviewed_manifest_sha256'], rights_basis=review['scope']),
        interpretation_complete=True, source_available=True, source_proposal_agrees=False,
        products=tuple(products))
    identities = AdmittedIdentities.load(identity_catalog, IdentityAdmission(
        catalog_sha256=admission.identity_catalog_sha256, sanitization_policy_hash=upload.digest()),
        reviewed_images=images, upload_policy=upload)
    return ReviewedSource(SourceBundle(notice, original), identities, admission)
