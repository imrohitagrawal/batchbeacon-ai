"""Exact reviewed synthetic identity evidence, never a model verdict or ownership grant."""

from dataclasses import dataclass, field
from hashlib import sha256
from typing import Annotated, Literal, Self

from pydantic import Field, model_validator

from batchbeacon.contracts import (
    Digest,
    EvidenceRef,
    Nonempty,
    Record,
    SourceDependency,
    ValueState,
)

Positive = Annotated[int, Field(gt=0)]


class IdentityAdmission(Record):
    catalog_sha256: Digest
    max_catalog_bytes: Positive = 32768
    max_identities: Positive = 20


class ReviewedIdentity(Record):
    fixture_id: Annotated[str, Field(pattern=r'^[a-z][a-z0-9-]{0,63}$')]
    approved_image_sha256: Digest
    width: Positive
    height: Positive
    mime_type: Literal['image/png']
    jurisdiction: Literal['SG']
    name: Nonempty
    pack_text: Nonempty
    synthetic: Literal[True]


class IdentitySourceScope(Record):
    family: Nonempty
    id: Nonempty
    capture_sha256: Digest
    jurisdictions: tuple[Literal['SG'], ...] = Field(min_length=1, max_length=1)


class IdentityCatalog(Record):
    version: Literal['synthetic-identity-projection-1']
    status: Literal['TECHNICAL_PROJECTION_OF_EXISTING_APPROVAL_NOT_NEW_HUMAN_REVIEW']
    admitted_manifest_sha256: Digest
    approved_source_record_sha256: Digest
    existing_review_record_sha256: Digest
    historical_reviewed_label_manifest_sha256: Digest
    historical_reviewed_packet_sha256: Digest
    normalization: Literal['name-casefold-whitespace-v1; pack exact rendered text']
    source_scope: IdentitySourceScope
    identities: tuple[ReviewedIdentity, ...] = Field(min_length=1)

    @model_validator(mode='after')
    def unique(self) -> Self:
        for attribute in ('fixture_id', 'approved_image_sha256'):
            values = [getattr(item, attribute) for item in self.identities]
            if len(set(values)) != len(values):
                raise ValueError('duplicate_identity_catalog_entry')
        return self


@dataclass(frozen=True)
class AdmittedIdentities:
    catalog: IdentityCatalog
    admission: IdentityAdmission
    original: bytes = field(repr=False)

    def __post_init__(self):
        if type(self.original) is not bytes \
                or len(self.original) > self.admission.max_catalog_bytes \
                or sha256(self.original).hexdigest() != self.admission.catalog_sha256 \
                or IdentityCatalog.model_validate_json(self.original) != self.catalog:
            raise ValueError('identity_catalog_admission_failed')
        if len(self.catalog.identities) > self.admission.max_identities:
            raise ValueError('identity_catalog_entry_limit')

    @classmethod
    def load(cls, original: bytes, admission: IdentityAdmission):
        if type(original) is not bytes or len(original) > admission.max_catalog_bytes \
                or sha256(original).hexdigest() != admission.catalog_sha256:
            raise ValueError('identity_catalog_admission_failed')
        catalog = IdentityCatalog.model_validate_json(original)
        if len(catalog.identities) > admission.max_identities:
            raise ValueError('identity_catalog_entry_limit')
        return cls(catalog, admission, original)


class IdentityDecision(Record):
    state: Literal['RESOLVED', 'UNRESOLVED', 'DISAGREES']
    entry: ReviewedIdentity | None = None

    @model_validator(mode='after')
    def coherent(self) -> Self:
        if (self.state == 'RESOLVED') != (self.entry is not None):
            raise ValueError('identity_resolution_shape')
        return self


class IdentityReceipt(Record):
    policy_hash: Digest
    catalog_hash: Digest
    admitted_manifest_hash: Digest
    identity_record_hash: Digest
    existing_review_record_hash: Digest
    historical_reviewed_label_manifest_hash: Digest
    resolved_name: Nonempty
    approved_image_hash: Digest
    captures: tuple[EvidenceRef, ...] = Field(min_length=1, max_length=2)
    sources: tuple[SourceDependency, ...] = Field(min_length=1, max_length=1)
    identity_support: tuple[EvidenceRef, ...] = Field(min_length=1)
    run_id: Annotated[str, Field(pattern=r'^[a-f0-9]{32}$')]
    run_binding_hash: Digest
    values_hash: Digest


def _name(value):
    return ' '.join(value.casefold().split())


def decide_identity(admitted, values, captures, sources) -> IdentityDecision:
    """Pure decision over validated original model values and owned input references."""
    unresolved = IdentityDecision(state='UNRESOLVED')
    disagrees = IdentityDecision(state='DISAGREES')
    if admitted is None:
        return unresolved
    catalog = admitted.catalog
    scope = catalog.source_scope
    if len(sources) != 1 or (sources[0].family, sources[0].version, sources[0].content_hash) != (
            scope.family, scope.id, scope.capture_sha256):
        return unresolved
    by_hash = {entry.approved_image_sha256: entry for entry in catalog.identities}
    selected = [by_hash.get(ref.sha256) for ref in captures]
    recognized = {entry.fixture_id: entry for entry in selected if entry is not None}
    if not recognized:
        return unresolved
    if len(recognized) != 1:
        return disagrees
    entry = next(iter(recognized.values()))
    identity = values.identity
    # These complete reviewed labels contain no product-code/GTIN identity fields.
    # An unsupported identifier must not provide another route to a positive match.
    if any(code.observation.state != ValueState.UNKNOWN for code in identity.identifiers):
        return disagrees
    if identity.name.state == ValueState.KNOWN and _name(identity.name.value) != _name(entry.name):
        return disagrees
    if identity.pack.state == ValueState.KNOWN and identity.pack.value != entry.pack_text:
        return disagrees
    if any(item is None for item in selected) \
            or identity.name.state != ValueState.KNOWN or identity.pack.state != ValueState.KNOWN:
        return unresolved
    selected_refs = {(ref.artifact_id, ref.sha256) for ref in captures if ref.kind == 'CAPTURE'}
    if len(selected_refs) != len(captures):
        return disagrees
    for observed in (identity.name, identity.pack):
        if not observed.evidence or any(ref.kind != 'CAPTURE'
                or (ref.artifact_id, ref.sha256) not in selected_refs for ref in observed.evidence):
            return disagrees
    return IdentityDecision(state='RESOLVED', entry=entry)


def identity_receipt(admitted, decision, values, captures, sources, run) -> IdentityReceipt:
    if decision.state != 'RESOLVED' or run is None:
        raise ValueError('identity_resolution_run_required')
    catalog, entry = admitted.catalog, decision.entry
    return IdentityReceipt(policy_hash=admitted.admission.digest(),
        catalog_hash=admitted.admission.catalog_sha256,
        admitted_manifest_hash=catalog.admitted_manifest_sha256,
        identity_record_hash=entry.digest(),
        existing_review_record_hash=catalog.existing_review_record_sha256,
        historical_reviewed_label_manifest_hash=catalog.historical_reviewed_label_manifest_sha256,
        resolved_name=entry.name, approved_image_hash=entry.approved_image_sha256,
        captures=captures, sources=sources,
        identity_support=values.identity.name.evidence + values.identity.pack.evidence,
        run_id=run.id, run_binding_hash=run.binding.digest(), values_hash=values.digest())
