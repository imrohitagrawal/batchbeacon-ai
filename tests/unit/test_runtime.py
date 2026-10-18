"""Production composition validation without provider or data-service requests."""

from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from google.auth.credentials import AnonymousCredentials
from pydantic import ValidationError

from batchbeacon.evidence_service import replace
from batchbeacon.extraction_api import ExtractionHTTPPolicy
from batchbeacon.firestore_store import FirestorePolicy
from batchbeacon.learning_decisions import GuidanceLimits
from batchbeacon.learning_evaluator import EvaluationPolicy, PreparedSuite
from batchbeacon.learning_service import LearningPolicy
from batchbeacon.retail_projection import CapabilityState, RetailReadPolicy
from batchbeacon.retail_refresh import RefreshPolicy
from batchbeacon.reviewed_source import SourceAdmission
from batchbeacon.runtime import (
    ObservedCapacity,
    RuntimeAssets,
    RuntimeConfig,
    build_app,
    create_app,
)
from batchbeacon.storage_objects import StoragePolicy
from tests.unit.test_firestore_store import no_network_or_credentials as no_network_or_credentials  # noqa
from tests.unit.test_firestore_store import setup as setup  # noqa
from tests.unit.test_reviewed_extraction import build_reviewed
from tests.unit.test_shared_admission import env as env  # noqa


@pytest.fixture
def runtime(setup, env):
    c = build_reviewed(setup, env, (0,))
    ex, stores = c[0], c[3][0]
    gp = replace(ex.evidence.guest.policy, origin="https://synthetic.example", mode="deployment")
    mc = replace(ex.config, mode="vertex")
    sp = replace(
        ex.shared.policy, guest_policy_hash=gp.digest(), model_configuration_hash=mc.digest()
    )
    grant = replace(ex.shared.grant, policy_hash=sp.digest())
    ep = EvaluationPolicy(retail=gp.retail, limits=GuidanceLimits.from_shared(sp))
    config = RuntimeConfig(
        guest=gp,
        evidence=ex.evidence.policy,
        action=stores.action_policy,
        firestore=FirestorePolicy(
            project_id=mc.project_id,
            database_id="(default)",
            namespace="synthetic_runtime",
            environment_id="reviewed",
            mode="production",
            api_endpoint="firestore.googleapis.com",
        ),
        storage=StoragePolicy(
            project_id=mc.project_id,
            bucket="synthetic-runtime",
            namespace="synthetic_runtime",
            mode="production",
            api_endpoint="https://storage.googleapis.com",
        ),
        extraction=mc,
        shared=sp,
        grant=grant,
        source_admission=SourceAdmission(
            reviewed_record_sha256="0" * 64,
            retrieval_record_sha256="0" * 64,
            identity_catalog_sha256="0" * 64,
            label_manifest_sha256="0" * 64,
            epoch=1,
            review_revision=1,
            max_original_bytes=4096,
        ),
        source_selection="synthetic-reviewed",
        http=ExtractionHTTPPolicy(),
        retail_read=ep.read,
        refresh=RefreshPolicy(),
        learning=LearningPolicy(),
        evaluation=ep,
        assets=RuntimeAssets(
            reviewed_record="missing",
            retrieval_record="missing",
            original="missing",
            identity_catalog="missing",
            label_manifest="missing",
            images=("missing",),
            learning_inputs="fixtures/learning/inputs.json",
            learning_expectations="fixtures/learning/expectations.json",
        ),
    )
    source = SimpleNamespace(
        bundle=next(iter(ex.sources.values())), identities=ex.evidence.identities
    )
    suite = PreparedSuite.load(
        Path("fixtures/learning/inputs.json").read_bytes(),
        Path("fixtures/learning/expectations.json").read_bytes(),
        ep,
    )
    return config, source, suite


def test_production_factory_constructs_owned_graph_without_rpc_or_budget_initialization(
    runtime, monkeypatch
):
    import google.auth

    import batchbeacon.runtime as module
    from batchbeacon.shared_admission import SharedAdmission

    config, source, suite = runtime
    monkeypatch.setenv("DISABLE_GCS_PYTHON_CLIENT_OTEL_BUCKET_METADATA", "true")
    monkeypatch.setattr(module, "load_assets", lambda root, c: (source, suite))
    monkeypatch.setattr(
        google.auth, "default", lambda **kw: (AnonymousCredentials(), "synthetic-project")
    )

    def forbidden(*a, **kw):
        pytest.fail("startup attempted provisioning or service request")

    monkeypatch.setattr(SharedAdmission, "initialize", forbidden)
    monkeypatch.setattr(SharedAdmission, "activate_phase", forbidden)
    monkeypatch.setattr(module.FirestoreStores, "run", forbidden)
    with TestClient(build_app(config, Path("."))) as client:
        response = client.get("/health")
        assert response.status_code == 200 and response.json()["product"] == "not_ready"
        public = client.get("/api/workbench/config").json()
        assert public["guidance"] == "OWNED_LIFECYCLE_CONNECTED"
        assert public["mode"] == "REAL_VERTEX_EXTRACTION"
        assert client.app.state.runtime_configuration_hash == config.digest()


def test_missing_environment_assets_and_policy_mismatch_fail_before_credentials(
    runtime, monkeypatch, tmp_path
):
    config, _, _ = runtime
    monkeypatch.setenv("BATCHBEACON_RUNTIME_MODE", "connected")
    monkeypatch.delenv("BATCHBEACON_RUNTIME_CONFIG", raising=False)
    with pytest.raises(ValueError, match="explicit runtime"):
        create_app()
    monkeypatch.delenv("DISABLE_GCS_PYTHON_CLIENT_OTEL_BUCKET_METADATA", raising=False)
    with pytest.raises(ValueError, match="environment"):
        build_app(config, tmp_path)
    monkeypatch.setenv("DISABLE_GCS_PYTHON_CLIENT_OTEL_BUCKET_METADATA", "true")
    with pytest.raises(ValueError, match="asset unavailable"):
        build_app(config, tmp_path)
    for field, value in [
        ("storage", replace(config.storage, namespace="different")),
        ("firestore", replace(config.firestore, project_id="different-project")),
        ("shared", replace(config.shared, guest_policy_hash="1" * 64)),
    ]:
        with pytest.raises(ValueError):
            replace(config, **{field: value})
    for path in ("/etc/passwd", "../private", "folder/../private", "./private"):
        with pytest.raises(ValidationError):
            replace(config.assets, original=path)


def test_capacity_observes_real_shared_admission_conditions_without_reserving(env):
    from batchbeacon.shared_admission import Pool

    service, store, guests, token, iid, clock, _, _ = env
    guest = guests.resolve(token)
    observer = ObservedCapacity(service, RetailReadPolicy())
    before = store.state()
    assert observer(guest).state == CapabilityState.AVAILABLE
    assert store.state() == before and not store.attempts
    phase = replace(before.phase, max_pool_liability_nanos=service.policy.reserve_nanos - 1)
    service.activate_phase(phase)
    assert observer(guest).state == CapabilityState.UNAVAILABLE
    assert store.state().balance(Pool.PUBLIC).lifetime_attempts == 0
    store.budget = None
    assert observer(guest).state == CapabilityState.UNAVAILABLE


def test_closed_startup_has_only_cheap_health_and_no_guest_admission(monkeypatch):
    monkeypatch.setenv("BATCHBEACON_RUNTIME_MODE", "closed")
    with TestClient(create_app()) as client:
        assert client.get("/health").json()["mode"] == "closed_preparation"
        assert client.get("/healthz").json() == client.get("/health").json()
        assert client.post("/api/guest").status_code == 404
    monkeypatch.delenv("BATCHBEACON_RUNTIME_MODE")
    with pytest.raises(ValueError, match="runtime mode"):
        create_app()


def test_runtime_consumer_mismatch_rejected_before_any_credentials(runtime):
    config, _, _ = runtime
    shared = replace(config.shared, run_seconds=config.shared.run_seconds + 1)
    with pytest.raises(ValueError):
        replace(
            config,
            shared=shared,
            grant=replace(config.grant, policy_hash=shared.digest()),
            evaluation=replace(config.evaluation, limits=GuidanceLimits.from_shared(shared)),
        )
    with pytest.raises(ValueError):
        replace(config, evidence=replace(config.evidence, max_extractions=2))
