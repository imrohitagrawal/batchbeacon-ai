"""Explicit production composition; startup never provisions data or model allowance."""

import os
from contextlib import asynccontextmanager
from datetime import timedelta
from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field, model_validator

from batchbeacon.action_service import ActionPolicy, ActionService
from batchbeacon.attempt_evidence import NonbillablePolicy
from batchbeacon.contracts import Record
from batchbeacon.evidence_service import EvidencePolicy, EvidenceService
from batchbeacon.extraction_api import ExtractionHTTPPolicy
from batchbeacon.extraction_service import ExtractionService
from batchbeacon.firestore_store import FirestorePolicy, FirestoreStores
from batchbeacon.guest_admission import GuestAdmissionPolicy
from batchbeacon.guest_service import GuestPolicy, GuestService
from batchbeacon.learning_decisions import GuidanceLimits
from batchbeacon.learning_evaluator import EvaluationPolicy, LearningEvaluator, PreparedSuite
from batchbeacon.learning_service import LearningPolicy
from batchbeacon.model_runtime import ExtractionConfig
from batchbeacon.retail_projection import (
    CapabilityObservation,
    CapabilityReason,
    CapabilityState,
    RetailProjector,
    RetailReadPolicy,
)
from batchbeacon.retail_refresh import RefreshPolicy, RetailRefresh
from batchbeacon.reviewed_source import SourceAdmission, load_sfa
from batchbeacon.shared_admission import (
    Address,
    Change,
    PredecessorLiabilities,
    SharedAdmission,
    SharedDenied,
    SharedGrant,
    SharedPolicy,
)
from batchbeacon.source_state import SourceRuntimeAdmission
from batchbeacon.storage_objects import StorageObjects, StoragePolicy
from batchbeacon.workbench import create_workbench_app

RelativePath = Annotated[str, Field(min_length=1, max_length=256)]


class RuntimeAssets(Record):
    reviewed_record: RelativePath
    retrieval_record: RelativePath
    original: RelativePath
    identity_catalog: RelativePath
    label_manifest: RelativePath
    images: tuple[RelativePath, ...] = Field(min_length=1)
    learning_inputs: RelativePath
    learning_expectations: RelativePath

    @model_validator(mode="after")
    def relative(self):
        for value in self.model_dump().values():
            for name in value if isinstance(value, tuple) else (value,):
                path = Path(name)
                if path.is_absolute() or ".." in path.parts or str(path) != name:
                    raise ValueError("runtime asset paths must be canonical and relative")
        return self




class RuntimeConfig(Record):
    version: Literal["production-runtime-1"] = "production-runtime-1"
    guest: GuestPolicy
    guest_admission: GuestAdmissionPolicy
    evidence: EvidencePolicy
    action: ActionPolicy
    firestore: FirestorePolicy
    storage: StoragePolicy
    extraction: ExtractionConfig
    shared: SharedPolicy
    grant: SharedGrant
    source_admission: SourceAdmission
    source_selection: Annotated[str, Field(pattern=r"^[a-z][a-z0-9_-]{0,79}$")]
    http: ExtractionHTTPPolicy
    retail_read: RetailReadPolicy
    refresh: RefreshPolicy
    learning: LearningPolicy
    evaluation: EvaluationPolicy
    assets: RuntimeAssets
    source_runtime: SourceRuntimeAdmission | None = Field(
        default=None, exclude_if=lambda value: value is None
    )
    nonbillable_policy: NonbillablePolicy | None = Field(
        default=None, exclude_if=lambda value: value is None
    )
    predecessor_liabilities: PredecessorLiabilities | None = Field(
        default=None, exclude_if=lambda value: value is None
    )

    @model_validator(mode="after")
    def coherent(self):
        projects = (
            self.firestore.project_id,
            self.storage.project_id,
            self.extraction.project_id,
            self.shared.project_id,
            self.grant.project_id,
        )
        if len(set(projects)) != 1:
            raise ValueError("runtime projects disagree")
        if (
            self.guest.mode != "deployment"
            or self.firestore.mode != "production"
            or self.storage.mode != "production"
            or self.extraction.mode != "vertex"
        ):
            raise ValueError("production requires HTTPS, actual data endpoints and Vertex")
        if self.firestore.namespace != self.storage.namespace:
            raise ValueError("runtime namespaces disagree")
        if (
            self.shared.guest_policy_hash != self.guest.digest()
            or self.shared.model_configuration_hash != self.extraction.digest()
            or self.grant.policy_hash != self.shared.digest()
            or self.guest.uploads != self.extraction.preparation.upload
            or self.evaluation.retail != self.guest.retail
            or self.evaluation.read != self.retail_read
            or self.evaluation.limits != GuidanceLimits.from_shared(self.shared)
        ):
            raise ValueError("runtime configuration lineage disagrees")
        if self.nonbillable_policy is not None and (
            self.nonbillable_policy.model_id != self.extraction.model_id
            or self.nonbillable_policy.model_configuration_hash != self.extraction.digest()
            or self.nonbillable_policy.endpoint != self.extraction.endpoint("generateContent")
        ):
            raise ValueError("nonbillable runtime binding invalid")
        self.learning.validate_capacity(self.guest.retail)
        if self.predecessor_liabilities is not None:
            self.predecessor_liabilities.validate_successor(self.shared, self.grant)
            self.predecessor_liabilities.validate_storage(self.firestore)
        # Pure consumer checks use no store operation or credential discovery.
        self.extraction.validate_consumer(SharedAdmission(self.shared, self.grant, object()))
        if self.shared.max_recaptures + 1 != self.evidence.max_extractions:
            raise ValueError("runtime acquisition limits disagree")
        return self


def load_assets(root: Path, config: RuntimeConfig):
    root = root.resolve()

    def read(name, limit):
        path = (root / name).resolve()
        if not path.is_relative_to(root) or not path.is_file() or path.stat().st_size > limit:
            raise ValueError("runtime asset unavailable")
        with path.open("rb") as stream:
            value = stream.read(limit + 1)
        if len(value) > limit:
            raise ValueError("runtime asset exceeds bound")
        return value

    a, p = config.assets, config.source_admission
    reviewed = load_sfa(
        reviewed_record=read(a.reviewed_record, p.max_record_bytes),
        retrieval_record=read(a.retrieval_record, p.max_record_bytes),
        original=read(a.original, p.max_original_bytes),
        identity_catalog=read(a.identity_catalog, p.max_record_bytes),
        label_manifest=read(a.label_manifest, p.max_record_bytes),
        images=tuple(read(name, config.guest.uploads.max_image_bytes) for name in a.images),
        upload=config.guest.uploads,
        admission=p,
    )
    suite = PreparedSuite.load(
        read(a.learning_inputs, config.evaluation.input_bytes),
        read(a.learning_expectations, config.evaluation.input_bytes),
        config.evaluation,
    )
    return reviewed, suite


class ObservedCapacity:
    """Short-lived server observation; every later paid request reserves independently."""

    def __init__(self, shared, read_policy):
        self.shared, self.policy = shared, read_policy

    def __call__(self, session):
        s = self.shared
        address = Address(session.capability_hash)
        now = s._now()
        until = min(
            session.scope.expires_at,
            now + timedelta(seconds=self.policy.capability_validity_seconds),
        )
        state, reason = CapabilityState.UNKNOWN, CapabilityReason.BACKEND_UNAVAILABLE
        try:

            def observe(snapshot):
                guest = s._guest(snapshot, address)
                budget = s._budget(snapshot)
                balance, amount = budget.balance(budget.phase.pool), s.policy.reserve_nanos
                if (
                    balance.committed + amount
                    > min(s.grant.ceiling(budget.phase.pool), budget.phase.max_pool_liability_nanos)
                    or sum(b.committed for b in budget.balances) + amount
                    > s.grant.root_ceiling_nanos
                    or any(
                        r.terminal is None and s._now() < r.deadline for r in snapshot.usage.runs
                    )
                ):
                    raise SharedDenied("new extraction unavailable")
                return Change(
                    budget,
                    snapshot.usage,
                    not_after=min(
                        guest.scope.expires_at,
                        budget.phase.expires_at,
                        s.grant.expires_at,
                        s.policy.price.valid_until,
                        until,
                    ),
                )

            result = s.store.transact(address, observe)
            until = min(until, result.not_after)
            state, reason = CapabilityState.AVAILABLE, CapabilityReason.OBSERVED
        except SharedDenied:
            state, reason = CapabilityState.UNAVAILABLE, CapabilityReason.OBSERVED
        except (OSError, ValueError):
            pass
        if until <= s._now():
            return None
        return CapabilityObservation(
            session_id=session.scope.session_id,
            capability="NEW_VERIFICATION",
            state=state,
            reason=reason,
            observed_at=now,
            valid_until=until,
        )


def build_app(config: RuntimeConfig, asset_root: Path):
    from batchbeacon.workbench import SupportContact

    support = SupportContact(email=os.environ.get("BATCHBEACON_SUPPORT_EMAIL"))
    # Validate all pure inputs before credential discovery or SDK construction.
    if (
        os.environ.get("DISABLE_GCS_PYTHON_CLIENT_OTEL_BUCKET_METADATA") != "true"
        or os.environ.get("FIRESTORE_EMULATOR_HOST")
        or os.environ.get("STORAGE_EMULATOR_HOST")
    ):
        raise ValueError("production environment is not explicitly admitted")
    reviewed, suite = load_assets(asset_root, config)
    if (
        config.evidence.identity_admission != reviewed.identities.admission
        or config.extraction.identity_resolution_policy_hash
        != reviewed.identities.admission.digest()
        or config.extraction.identity_normalization_hash != reviewed.identities.derivation_hash
    ):
        raise ValueError("runtime reviewed identity lineage disagrees")
    import google.auth
    from google.api_core.client_options import ClientOptions
    from google.cloud import storage
    from google.cloud.firestore_v1.services.firestore import FirestoreClient

    credentials, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    firestore = FirestoreClient(
        credentials=credentials,
        client_options=ClientOptions(api_endpoint=config.firestore.api_endpoint),
    )
    objects_client = None
    try:
        objects_client = storage.Client(
            project=config.storage.project_id,
            credentials=credentials,
            client_options=ClientOptions(api_endpoint=config.storage.api_endpoint),
        )
        stores = FirestoreStores(
            firestore,
            config.firestore,
            config.guest,
            config.evidence,
            config.action,
            guest_admission=config.guest_admission,
            source_runtime=config.source_runtime,
            predecessor_liabilities=config.predecessor_liabilities,
        )
        objects = StorageObjects(objects_client, config.storage)
        guest = GuestService(config.guest, stores.guests, objects)
        evidence = EvidenceService(
            guest, stores.evidence, config.evidence, identities=reviewed.identities
        )
        actions = ActionService(evidence, stores.actions, config.action)
        shared = SharedAdmission(
            config.shared, config.grant, stores.shared,
            nonbillable_policy=config.nonbillable_policy,
            predecessor_liabilities=config.predecessor_liabilities,
        )
        stores.enable_retail(RetailProjector(actions, config.shared, config.retail_read))
        evaluator = LearningEvaluator(suite, config.evaluation)
        stores.enable_learning(
            evidence,
            config.shared,
            evaluator,
            config.learning,
            capability=ObservedCapacity(shared, config.retail_read),
        )
        extraction = ExtractionService(
            evidence, shared, config.extraction, {config.source_selection: reviewed.bundle}
        )
        refresh = RetailRefresh(stores.retail, config.refresh)
        app = create_workbench_app(
            extraction, actions, refresh, config.http, learning=stores.learning, support=support
        )
        app.state.runtime_configuration_hash = config.digest()

        @asynccontextmanager
        async def lifespan(application):
            try:
                yield
            finally:
                firestore.transport.close()
                objects_client.close()

        app.router.lifespan_context = lifespan
        return app
    except BaseException:
        firestore.transport.close()
        if objects_client is not None:
            objects_client.close()
        raise


def create_app():
    mode = os.environ.get("BATCHBEACON_RUNTIME_MODE")
    if mode == "closed":
        from fastapi import FastAPI

        app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

        @app.get("/health")
        @app.get("/healthz")
        def health():
            return {"process": "ok", "product": "not_ready", "mode": "closed_preparation"}

        return app
    if mode != "connected":
        raise ValueError("explicit runtime mode required")
    path = os.environ.get("BATCHBEACON_RUNTIME_CONFIG")
    inline = os.environ.get("BATCHBEACON_RUNTIME_JSON")
    if bool(path) == bool(inline):
        raise ValueError("exactly one explicit runtime configuration required")
    raw = Path(path).read_bytes() if path else inline
    config = RuntimeConfig.model_validate_json(raw)
    return build_app(config, Path(__file__).resolve().parents[2])
