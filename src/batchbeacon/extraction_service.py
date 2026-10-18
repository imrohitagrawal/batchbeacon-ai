"""Owned single-acquisition coordinator. No default app mount or provider activation."""

import asyncio
import inspect
import json
from dataclasses import dataclass, field
from datetime import timedelta
from functools import wraps
from hashlib import sha256
from types import MappingProxyType
from typing import Annotated, Literal

from pydantic import Field

from batchbeacon.contracts import AuthorityNotice, Record, Verdict
from batchbeacon.evidence_service import EvidenceService, ExtractionEnvelope
from batchbeacon.extraction_input import prepare_input
from batchbeacon.extraction_proposal import ProposalInvalid
from batchbeacon.extraction_records import RunBinding
from batchbeacon.guest_service import GuestDenied, OpaqueId, RequestKey
from batchbeacon.model_runtime import ExtractionConfig, ModelFailure, execute_model
from batchbeacon.shared_admission import SharedAdmission, SharedDenied


def _safe_failure(error):
    if isinstance(error, GuestDenied):
        return error.status, error.code
    if isinstance(error, SharedDenied):
        return 409, 'acquisition_not_admitted'
    return 503, 'acquisition_unavailable'


def owned_boundary(operation):
    """Public service errors carry no storage/provider payload or exception chain."""
    if inspect.iscoroutinefunction(operation):
        @wraps(operation)
        async def asynchronous(*args, **kwargs):
            try:
                return await operation(*args, **kwargs)
            except Exception as error:
                failure = _safe_failure(error)
            raise GuestDenied(*failure)
        return asynchronous
    @wraps(operation)
    def synchronous(*args, **kwargs):
        try:
            return operation(*args, **kwargs)
        except Exception as error:
            failure = _safe_failure(error)
        raise GuestDenied(*failure)
    return synchronous


class AcquisitionCommand(Record):
    incident_id: OpaqueId
    request_key: RequestKey
    source_selection: Annotated[str, Field(pattern=r'^[a-z][a-z0-9_-]{0,63}$')]
    capture_ids: tuple[OpaqueId, ...] = Field(min_length=1, max_length=2)
    expected_observation_revision: Annotated[int, Field(ge=0)]


class AcquisitionStatus(Record):
    run_id: OpaqueId
    incident_id: OpaqueId
    state: Literal['COMPLETE', 'REVIEW_REQUIRED', 'FAILED', 'TIMED_OUT',
                   'INCOMPLETE', 'SUPERSEDED', 'STALE']
    current: bool
    extraction_revision: int | None = None
    observation_revision: int | None = None
    result_revision: int | None = None
    diagnostics: tuple[Literal['SOURCE_DISAGREEMENT', 'SOURCE_REVIEW_REQUIRED',
        'IDENTITY_EVIDENCE_DISAGREEMENT', 'IDENTITY_INPUT_UNAVAILABLE',
        'PROPOSAL_INVALID', 'CHECK_FAILED'], ...] = ()


@dataclass(frozen=True)
class SourceBundle:
    notice: AuthorityNotice
    original: bytes = field(repr=False)

    def __post_init__(self):
        if type(self.original) is not bytes or not self.original \
                or sha256(self.original).hexdigest() != self.notice.dependency.content_hash:
            raise ValueError('source_catalog_binding_invalid')


class ExtractionService:
    def __init__(self, evidence: EvidenceService, shared: SharedAdmission,
                 config: ExtractionConfig, sources: dict[str, SourceBundle], *,
                 transport_factory=None, credentials_factory=None):
        config.validate_consumer(shared)
        if not sources or any(not isinstance(v, SourceBundle) for v in sources.values()):
            raise ValueError('explicit_source_catalog_required')
        if config.mode == 'offline_test':
            if transport_factory is None or credentials_factory is None:
                raise ValueError('explicit_offline_factories_required')
        elif transport_factory is not None or credentials_factory is not None:
            raise ValueError('runtime_factory_override_forbidden')
        if shared.policy.guest_policy_hash != evidence.guest.policy.digest() \
                or shared.policy.max_recaptures + 1 != evidence.policy.max_extractions:
            raise ValueError('coordinator_policy_mismatch')
        identity_policy = evidence.policy.identity_admission
        if config.identity_resolution_policy_hash != (identity_policy.digest()
                                                       if identity_policy else None):
            raise ValueError('identity_configuration_mismatch')
        if config.identity_normalization_hash != (evidence.identities.derivation_hash
                                                  if evidence.identities else None):
            raise ValueError('identity_normalization_configuration_mismatch')
        self.evidence, self.shared, self.config = evidence, shared, config
        self.sources = MappingProxyType(dict(sources))
        self.transport_factory, self.credentials_factory = transport_factory, credentials_factory

    @owned_boundary
    def status(self, capability, run_id):
        key = self.evidence.guest._key(capability)
        run = self.shared.inspect_run(key, run_id)
        view = self.evidence.read_evidence(capability, run.incident_id)
        saved = next((e for e in view.state.extractions if e.run_id == run_id), None)
        current = bool(view.current and view.latest_run_id == run_id)
        diagnostics = ()
        if view.latest_run_id != run_id:
            state = 'SUPERSEDED'
        elif current:
            state = ('REVIEW_REQUIRED' if view.result.verdict == Verdict.REVIEW_REQUIRED
                     else 'COMPLETE')
        elif run.completion_hash:
            state = 'STALE'
        elif run.terminal == 'timed_out' or self.shared._now() >= run.deadline:
            state = 'TIMED_OUT'
        elif run.terminal == 'failed' or (saved and saved.envelope.validation == 'INVALID'):
            state = 'FAILED'
            codes = saved.envelope.validation_codes if saved else ()
            diagnostics = (('SOURCE_REVIEW_REQUIRED',) if 'SOURCE_REVIEW_REQUIRED' in codes else
                ('IDENTITY_INPUT_UNAVAILABLE',) if 'IDENTITY_INPUT_UNAVAILABLE' in codes else
                ('IDENTITY_EVIDENCE_DISAGREEMENT',)
                if 'IDENTITY_EVIDENCE_DISAGREEMENT' in codes else
                ('SOURCE_DISAGREEMENT',) if any(c.startswith('SOURCE_') for c in codes) else
                ('PROPOSAL_INVALID',) if saved else ('CHECK_FAILED',))
            if diagnostics in {('IDENTITY_EVIDENCE_DISAGREEMENT',),
                               ('IDENTITY_INPUT_UNAVAILABLE',)}:
                state = 'REVIEW_REQUIRED'
        else:
            state = 'INCOMPLETE'  # Status never asserts that an executor is still running.
        return AcquisitionStatus(run_id=run.id, incident_id=run.incident_id, state=state,
            current=current, extraction_revision=saved.revision if saved else None,
            observation_revision=view.observation.revision if current else None,
            result_revision=view.result.revision if current else None, diagnostics=diagnostics)

    @owned_boundary
    def status_for_key(self, capability, incident_id, request_key):
        key = self.evidence.guest._key(capability)
        run = self.shared.find_run(key, incident_id, request_key)
        if run is None:
            raise GuestDenied(404, 'acquisition_unavailable')
        return self.status(capability, run.id)

    @staticmethod
    def _same_command(run, command):
        # Source selection identity is the stable, non-secret logical operation.
        return (run.incident_id == command.incident_id
            and run.binding.logical_operation == 'extract_' + command.source_selection
            and run.binding.expected_observation_revision == command.expected_observation_revision
            and tuple(c.id for c in run.binding.manifest.captures) == command.capture_ids)

    @owned_boundary
    async def acquire(self, capability, command: AcquisitionCommand):
        # One absolute cap includes owned reads, original-input preparation and admission.
        started = self.shared._now()
        deadline = started + timedelta(seconds=self.config.run_seconds)
        loop = asyncio.get_running_loop()
        loop_deadline = loop.time() + self.config.run_seconds
        def fresh():
            if self.shared._now() >= deadline or loop.time() >= loop_deadline:
                raise GuestDenied(409, 'acquisition_deadline_elapsed')
        key = self.evidence.guest._key(capability)
        prior = self.shared.find_run(key, command.incident_id, command.request_key)
        if prior is not None:
            if not self._same_command(prior, command):
                raise GuestDenied(409, 'acquisition_request_conflict')
            return self.status(capability, prior.id)
        bundle = self.sources.get(command.source_selection)
        if bundle is None:
            raise GuestDenied(422, 'source_selection_unavailable')
        captures = self.evidence.acquisition_inputs(capability, command.incident_id,
            bundle.notice, command.capture_ids, command.expected_observation_revision)
        prepared = prepare_input(source_bytes=bundle.original, notice=bundle.notice,
            captures=tuple((c, self.evidence.guest.image(capability, command.incident_id, c.id))
                           for c in captures), instruction=self.config.instruction,
            prompt_version=self.config.prompt_version, policy=self.config.preparation)
        fresh()
        binding = RunBinding(manifest=prepared.manifest,
            expected_observation_revision=command.expected_observation_revision,
            application_configuration_hash=self.config.digest(),
            logical_operation='extract_' + command.source_selection)
        admitted = self.shared.admit_run(key, command.incident_id, command.request_key,
                                        binding, not_after=deadline)
        run = admitted.run
        if not admitted.fresh:
            return self.status(capability, run.id)
        complete, unknown = False, False
        try:
            fresh()
            # Preparation/admission may block; refresh dependency checks before the model.
            self.evidence.acquisition_inputs(capability, command.incident_id,
                bundle.notice, command.capture_ids, command.expected_observation_revision)
            credentials = self.credentials_factory() if self.credentials_factory else None
            transport = self.transport_factory() if self.transport_factory else None
            output = await execute_model(self.config, self.shared, key, run, prepared,
                transport=transport, credentials=credentials, monotonic_deadline=loop_deadline)
            fresh()
            values, codes, source_status = None, (), None
            try:
                report = prepared.translate(output.candidate, bundle.notice)
                source_status, codes = report.source_status, report.diagnostics
                if source_status == 'AGREES_WITH_REVIEW':
                    values = report.label_values
                    decision = self.evidence.identity_decision(values,
                        tuple(c.evidence() for c in prepared.manifest.captures),
                        (prepared.manifest.source,))
                    if decision.state in {'DISAGREES', 'UNAVAILABLE'}:
                        values, codes = None, (('IDENTITY_INPUT_UNAVAILABLE',)
                            if decision.state == 'UNAVAILABLE'
                            else ('IDENTITY_EVIDENCE_DISAGREEMENT',))
            except ProposalInvalid:
                codes = ('PROPOSAL_INVALID',)
            summary = json.dumps({'redaction': self.config.redaction_version,
                'proposal_hash': sha256(output.candidate).hexdigest(),
                'source_status': source_status, 'diagnostics': codes}, sort_keys=True)
            envelope = ExtractionEnvelope(provenance='fake' if self.config.mode == 'offline_test'
                else 'live', redacted_output_json=summary,
                validation='VALID' if values is not None else 'INVALID', values=values,
                validation_codes=codes, model_id=self.config.model_id,
                prompt_version=self.config.prompt_version, configuration_hash=self.config.digest(),
                sources=(prepared.manifest.source,),
                captures=tuple(c.evidence() for c in prepared.manifest.captures),
                started_at=run.started_at, completed_at=self.shared._now())
            extraction_key, verification_key = 'extract_' + run.id, 'verify_' + run.id
            self.evidence.record_extraction(capability, command.incident_id, extraction_key,
                command.expected_observation_revision, envelope, run_id=run.id)
            fresh()
            if values is not None:
                verification = self.evidence.verification_binding(capability, command.incident_id,
                                                                  run_id=run.id)
                self.shared.reserve_verification(key, command.incident_id, verification_key,
                                                 verification)
                fresh()
                self.evidence.publish_verification(capability, command.incident_id,
                    verification_key, verification, run_id=run.id)
                fresh()
                view = self.evidence.complete_acquisition(capability, command.incident_id,
                    run.id, extraction_key, verification_key)
                complete = view.current
        except asyncio.CancelledError:
            self._finish(key, run.id, failed=True)
            raise
        except ModelFailure:
            pass
        except GuestDenied as error:
            unknown = error.status >= 500
        except Exception:
            # Durable status/attempt history is the recovery path; no automatic re-execution.
            unknown = True
        self._finish(key, run.id, failed=not complete)
        fresh()
        if self.shared._now() >= run.deadline:
            raise GuestDenied(409, 'acquisition_deadline_elapsed')
        if unknown:
            raise GuestDenied(503, 'acquisition_outcome_unknown')
        result = self.status(capability, run.id)
        fresh()
        if self.shared._now() >= run.deadline:
            raise GuestDenied(409, 'acquisition_deadline_elapsed')
        return result

    def _finish(self, key, run_id, *, failed):
        try:
            self.shared.finish_run(key, run_id, failed=failed)
        except Exception:
            # Cleanup is scoped to this run; failures neither refund nor restart anything.
            pass
