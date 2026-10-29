"""Content-free private observations. Never authority or a new database read."""

import logging
from hashlib import sha256
from typing import Annotated, Literal

from pydantic import Field, model_validator

from batchbeacon.contracts import Digest, Record


class ProvenancePolicy(Record):
    max_sources: Annotated[int, Field(gt=0)] = 16
    max_event_bytes: Annotated[int, Field(gt=0)] = 16384


class DeploymentRevision(Record):
    value: Annotated[str, Field(pattern=r'^[a-z][a-z0-9-]{0,62}$')]


class ProvenanceContext(Record):
    policy: ProvenancePolicy
    runtime_hash: Digest
    deployment_revision_hash: Digest | None = None


def identifier_hash(value):
    return sha256(value.encode()).hexdigest()


def context(policy, runtime_hash, revision=None):
    admitted = DeploymentRevision(value=revision) if revision is not None else None
    return ProvenanceContext(policy=policy, runtime_hash=runtime_hash,
        deployment_revision_hash=identifier_hash(admitted.value) if admitted else None)


class SourceLineage(Record):
    family_hash: Digest
    version_hash: Digest
    capture_hash: Digest
    epoch: Annotated[int, Field(ge=0)]
    review_revision: Annotated[int, Field(ge=0)]


def sources(dependencies):
    return tuple(sorted((SourceLineage(family_hash=identifier_hash(s.family),
        version_hash=identifier_hash(s.version), capture_hash=s.content_hash,
        epoch=s.epoch, review_revision=s.review_revision) for s in dependencies),
        key=lambda s: (s.family_hash, s.version_hash)))


class Lineage(Record):
    event: Literal['acquisition_lineage_v1', 'guidance_lineage_v1'] = 'acquisition_lineage_v1'
    runtime_hash: Digest
    deployment_revision_hash: Digest | None = None
    deployment_evidence: Literal['ENVIRONMENT_BINDING_ONLY', 'UNKNOWN'] = 'UNKNOWN'
    request_hash: Digest | None = None
    run_hash: Digest | None = None
    reconciliation_only: bool = False
    sources: tuple[SourceLineage, ...] = ()
    source_currentness: Literal['NOT_ASSESSED'] = 'NOT_ASSESSED'
    input_manifest_hash: Digest | None = None
    prompt_hash: Digest | None = None
    schema_hash: Digest | None = None
    preparation_hash: Digest | None = None
    model_configuration_hash: Digest | None = None
    generation: Literal['RESULT_NOT_RETURNED', 'RESULT_RETURNED'] = 'RESULT_NOT_RETURNED'
    validation: Literal['NOT_OBSERVED', 'VALID', 'INVALID'] = 'NOT_OBSERVED'
    extraction_persistence: Literal['NOT_ACKNOWLEDGED', 'ACKNOWLEDGED'] = 'NOT_ACKNOWLEDGED'
    verifier_publication: Literal['NOT_ACKNOWLEDGED', 'ACKNOWLEDGED'] = 'NOT_ACKNOWLEDGED'
    verifier_receipt_hash: Digest | None = None
    verifier_policy_hash: Digest | None = None
    verifier_version_hash: Digest | None = None
    result_hash: Digest | None = None
    observation_hash: Digest | None = None
    guidance_policy_hash: Digest | None = None
    guidance_activation_revision: Annotated[int, Field(gt=0)] | None = None
    guidance_receipt_hash: Digest | None = None
    guidance_state: Literal['NOT_OBSERVED', 'ACKNOWLEDGED'] = 'NOT_OBSERVED'
    outcome: Literal['COMPLETE', 'REVIEW_REQUIRED', 'FAILED', 'TIMED_OUT', 'INCOMPLETE',
                     'SUPERSEDED', 'STALE', 'refused', 'unknown', 'disconnected',
                     'ACKNOWLEDGED'] = 'unknown'


    @model_validator(mode='after')
    def facts(self):
        if ((self.deployment_revision_hash is None) != (self.deployment_evidence == 'UNKNOWN')
            or self.validation != 'NOT_OBSERVED' and self.generation != 'RESULT_RETURNED'
            or self.extraction_persistence == 'ACKNOWLEDGED' and self.validation == 'NOT_OBSERVED'
            or self.verifier_publication == 'ACKNOWLEDGED' and (
                self.extraction_persistence != 'ACKNOWLEDGED' or self.validation != 'VALID'
                or self.verifier_receipt_hash is None)
            or self.reconciliation_only and (self.generation != 'RESULT_NOT_RETURNED'
                or self.verifier_publication != 'NOT_ACKNOWLEDGED')
            or self.guidance_state == 'ACKNOWLEDGED' and any(value is None for value in (
                self.guidance_policy_hash, self.guidance_activation_revision,
                self.guidance_receipt_hash))):
            raise ValueError('lineage_fact_conflict')
        return self


def initial(binding):
    return Lineage(runtime_hash=binding.runtime_hash,
        deployment_revision_hash=binding.deployment_revision_hash,
        deployment_evidence=('ENVIRONMENT_BINDING_ONLY'
                             if binding.deployment_revision_hash else 'UNKNOWN'))


_logger = logging.getLogger(__name__)
_logger.setLevel(logging.INFO)
_logger.propagate = False
if not _logger.handlers:
    _logger.addHandler(logging.StreamHandler())


def emit(binding, record):
    try:
        if binding is None:
            return None
        record = Lineage.model_validate(record)
        if (record.runtime_hash != binding.runtime_hash
            or record.deployment_revision_hash != binding.deployment_revision_hash
            or len(record.sources) > binding.policy.max_sources):
            return None
        raw = record.model_dump_json()
        if len(raw.encode()) > binding.policy.max_event_bytes:
            return None
        _logger.info(raw)
        return record
    except Exception:
        # Observations cannot change admission, persistence or accounting.
        return None


def guidance(binding, request):
    try:
        if binding is None:
            return None
        base = initial(binding)
        return emit(binding, Lineage.model_validate(base.model_dump() | {
            'event': 'guidance_lineage_v1', 'sources': sources(request.basis.sources),
            'guidance_policy_hash': request.binding.policy.content_hash,
            'guidance_activation_revision': request.binding.activation_revision,
            'guidance_receipt_hash': request.digest(), 'guidance_state': 'ACKNOWLEDGED',
            'observation_hash': request.basis.observation.content_hash,
            'result_hash': request.basis.result.content_hash, 'outcome': 'ACKNOWLEDGED'}))
    except Exception:
        return None
