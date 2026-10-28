"""Owned replay / trusted refresh with installed SDK controlled RPC, never live truth."""

from datetime import timedelta
from hashlib import sha256

import httpcore
import pytest
from fastapi.testclient import TestClient
from google.api_core import exceptions
from pydantic import ValidationError

from batchbeacon.action_service import ActionConfirmation
from batchbeacon.contracts import ActionType
from batchbeacon.evidence_service import replace
from batchbeacon.guest_service import GuestDenied, csrf_for
from batchbeacon.incident_api import IncidentHTTPPolicy, create_incident_test_app
from batchbeacon.retail_projection import RetailProjector, RetailReadPolicy
from batchbeacon.source_api import mount_source_api
from batchbeacon.source_fetch import (
    FetchedSource,
    SourceFetchPolicy,
    SourceFetchRefused,
    fetch_source,
)
from batchbeacon.source_refresh import RefreshDenied, TrustedRefresh, TrustedRefreshPolicy
from batchbeacon.source_service import SourceCommand, SourceService, StartSourceReview
from batchbeacon.source_state import FamilyRefresh, SourceCatalog, SourceChoice, SourceRegistry
from batchbeacon.source_update import SourceUpdatePolicy, prepare_source_update
from tests.unit.domain_fixtures import NOW, known
from tests.unit.test_firestore_store import env as env
from tests.unit.test_firestore_store import extract, owned, publish, saved
from tests.unit.test_firestore_store import no_network_or_credentials as no_network_or_credentials
from tests.unit.test_firestore_store import setup as setup
from tests.unit.test_source_state_reader import enable
from tests.unit.test_source_update import version


def source_registry(setup):
    return registry_for_environment(saved(setup, "environment"))


def registry_for_environment(base):
    policy = SourceUpdatePolicy(
        original=version("original", b"original"),
        update=version(
            "update",
            b"update",
            supersedes="original",
            jurisdictions=("GB-ENG", "GB-NIR", "GB-WLS", "GB-SCT"),
        ),
    )
    receipt = prepare_source_update(b"original", b"update", policy)
    choices = [SourceChoice(key="sfa", capture_kind="RAW_HTTP_BODY", environment=base)]
    for key, v in (("uk-original", policy.original), ("uk-update", policy.update)):
        dep = replace(
            base.notices[0].dependency,
            family=v.family,
            version=v.version,
            content_hash=v.content_hash,
        )
        notice = replace(
            base.notices[0],
            dependency=dep,
            authority="UK FSA",
            published_at=v.published_at,
            jurisdictions=v.jurisdictions,
            review=None,
            retrieved_at=None,
            interpretation_complete=False,
            products=(),
        )
        environment = replace(
            base,
            notices=(notice,),
            context=replace(base.context, jurisdiction="GB-ENG", current_sources=(dep,)),
        )
        choices.append(
            SourceChoice(key=key, capture_kind="RETAINED_RENDERED_TEXT", environment=environment)
        )
    catalog = SourceCatalog(
        default_choice="sfa",
        choices=tuple(choices),
        update=receipt,
        original_choice="uk-original",
        update_choice="uk-update",
    )
    return SourceRegistry(
        catalog=catalog,
        families=tuple(
            FamilyRefresh(family=family, epoch=1, status="NEVER_REQUESTED")
            for family in (base.notices[0].dependency.family, policy.original.family)
        ),
    )


def source_service(setup, env=None):
    registry = source_registry(setup)
    enable(setup, registry)
    setup[0].source_runtime = replace(setup[0].source_runtime, replay_enabled=True)
    if env is not None:
        setup[0].enable_retail(RetailProjector(setup[4], env[0].policy, RetailReadPolicy()))
    return SourceService(setup[3], setup[0])


def start(service, token, key="start"):
    ctx = service.context(token)
    return service.start(
        token,
        key,
        StartSourceReview(
            catalog_hash=ctx["catalog_hash"], session_reference=ctx["session_reference"]
        ),
    )


def forward(service, token, value, key="forward", revision=None):
    return service.select(
        token,
        value["incident_id"],
        key,
        SourceCommand(
            catalog_hash=value["catalog_hash"],
            choice="uk-update",
            expected_revision=value["selection_revision"] if revision is None else revision,
        ),
    )


def refresher(setup, *, fetcher=None):
    registry = saved(setup, "source_registry")
    notice = registry.catalog.environment(None).notices[0]
    policy = TrustedRefreshPolicy(
        family=notice.dependency.family,
        version=notice.dependency.version,
        expected_hash=notice.dependency.content_hash,
        catalog_hash=registry.catalog.digest(),
        fetch=SourceFetchPolicy(
            url=notice.final_url,
            allowed_hosts=(
                __import__("urllib.parse", fromlist=["urlsplit"])
                .urlsplit(notice.final_url)
                .hostname,
            ),
            public_addresses=("8.8.8.8",),
        ),
        not_before=NOW - timedelta(seconds=1),
        expires_at=NOW + timedelta(hours=1),
        freshness_seconds=30,
    )
    kwargs = {} if fetcher is None else {"fetcher": fetcher}
    return TrustedRefresh(setup[0], policy, clock=lambda: setup[5][0], **kwargs)


def test_owned_forward_only_history_queue_and_logical_dedup(setup, env):
    service = source_service(setup, env)
    token, session, previous = owned(setup)
    value = start(service, token)
    assert value["selected_choice"] == "uk-original" and value["review_only"]
    iid = value["incident_id"]
    usage = saved(setup, "usage", session.capability_hash)
    updated = forward(service, token, value)
    alias = forward(service, token, value, key="different-key-same-logical-command")
    assert alias["selection_revision"] == updated["selection_revision"] == 2
    assert start(service, token)["selected_choice"] == "uk-update"
    assert len(setup[2].resolve(token).incidents) == 2
    state = saved(setup, "evidence", session.capability_hash, iid)
    assert len(state.source_selection.receipts) == 3
    assert len(state.source_selection.receipts) == len(
        {r.key for r in state.source_selection.receipts}
    )
    assert not state.extractions and not state.results and state.active_result is None
    assert saved(setup, "usage", session.capability_hash) == usage
    assert setup[3].read_evidence(token, previous.id).state.source_selection is None
    assert {r.incident_id for r in setup[0].retail.read(token).snapshot.rows} == {iid, previous.id}
    with pytest.raises(GuestDenied, match="source_forward_replay_only"):
        service.select(
            token,
            iid,
            "back",
            SourceCommand(
                catalog_hash=value["catalog_hash"], choice="uk-original", expected_revision=2
            ),
        )
    with pytest.raises(GuestDenied, match="source_request_conflict"):
        forward(service, token, value, key="forward", revision=2)
    assert saved(setup, "source_registry").families == source_registry(setup).families


def test_start_owner_reference_foreign_expiry_and_receipt_bound(setup):
    service = source_service(setup)
    token, session, _ = owned(setup)
    ctx = service.context(token)
    other, _ = setup[2].issue()
    command = StartSourceReview(
        catalog_hash=ctx["catalog_hash"], session_reference=ctx["session_reference"]
    )
    with pytest.raises(GuestDenied, match="owner_changed"):
        service.start(other, "start", command)
    assert not setup[2].resolve(other).incidents
    value = start(service, token)
    with pytest.raises(GuestDenied) as error:
        service.read(other, value["incident_id"])
    assert error.value.status == 404
    setup[0].source_runtime = replace(setup[0].source_runtime, max_selection_receipts=1)
    with pytest.raises(GuestDenied) as error:
        forward(service, token, value)
    assert error.value.status == 429
    setup[5][0] = session.scope.expires_at
    versions = setup[1].versions.copy()
    with pytest.raises(GuestDenied) as error:
        forward(service, token, value)
    assert error.value.status == 401 and setup[1].versions == versions


@pytest.mark.parametrize("phase", ["create", "select"])
def test_start_lost_ack_reconciles_original_key_no_extra_incident(setup, phase):
    service = source_service(setup)
    token, session, _ = owned(setup)
    stores, server, *_ = setup

    def lost(request):
        kinds = [
            stores._decode(w.update, w.update.fields["kind"].string_value) for w in request.writes
        ]
        if (
            phase == "create"
            and any(getattr(r, "incidents", ()) and len(r.incidents) == 2 for r in kinds)
        ) or (
            phase == "select"
            and any(getattr(r, "source_selection", None) is not None for r in kinds)
        ):
            raise exceptions.DeadlineExceeded("injected lost ack")

    server.after_commit = lost
    with pytest.raises(GuestDenied) as error:
        start(service, token)
    assert error.value.status == 503
    server.after_commit = lambda request: None
    found = service.reconcile_start(token, "start")
    assert found["start_state"] == (
        "INVESTIGATION_CREATED" if phase == "create" else "SOURCE_SELECTED"
    )
    complete = start(service, token)
    assert complete["selected_choice"] == "uk-original"
    assert len(setup[2].resolve(token).incidents) == 2
    assert (
        len(
            saved(
                setup, "evidence", session.capability_hash, complete["incident_id"]
            ).source_selection.receipts
        )
        == 1
    )


def test_source_http_owner_body_guards_unknown_recovery_and_no_global_route(setup):
    service = source_service(setup)
    app = create_incident_test_app(setup[2], setup[3], setup[4], IncidentHTTPPolicy())
    mount_source_api(app, service, IncidentHTTPPolicy())
    http = TestClient(app, base_url=setup[2].policy.origin)
    assert http.get("/api/source-reviews/context").status_code == 401
    token, _, foreign = owned(setup)
    http.cookies.set(setup[2].policy.cookie_name, token)
    headers = {
        "Origin": setup[2].policy.origin,
        "X-CSRF-Token": csrf_for(token),
        "Idempotency-Key": "start",
    }
    ctx = http.get("/api/source-reviews/context").json()
    body = {k: ctx[k] for k in ("catalog_hash", "session_reference")}
    response = http.post("/api/source-reviews", headers=headers, json=body)
    assert response.status_code == 200, response.text
    iid = response.json()["incident_id"]
    assert http.get(f"/api/incidents/{iid}/source").json()["selected_choice"] == "uk-original"
    assert (
        http.get("/api/source-reviews/reconcile", headers={"Idempotency-Key": "start"}).json()[
            "start_state"
        ]
        == "SOURCE_SELECTED"
    )
    assert http.post(f"/api/incidents/{iid}/source", json={}).status_code == 403
    assert http.post("/api/source-registry", headers=headers, json={}).status_code == 404
    other, _ = setup[2].issue()
    http.cookies.set(setup[2].policy.cookie_name, other)
    assert (
        http.post(
            f"/api/incidents/{foreign.id}/source", content=b"{broken", headers=headers
        ).status_code
        == 404
    )


@pytest.mark.parametrize("lost_phase", ["begin", "publish"])
def test_refresh_lost_ack_never_refetches_or_double_epochs(setup, lost_phase):
    source_service(setup)
    calls = []

    def fetch(policy, **kwargs):
        calls.append(policy)
        return FetchedSource(b"changed", 1)

    service = refresher(setup, fetcher=fetch)

    def lost(request):
        name = service._name("refresh")
        journals = [
            setup[0]._decode(w.update, "source_refresh")
            for w in request.writes
            if w.update.name == name
        ]
        if journals and (journals[0].result is None) == (lost_phase == "begin"):
            raise exceptions.DeadlineExceeded("injected lost ack")

    setup[1].after_commit = lost
    with pytest.raises(OSError):
        service.execute("refresh")
    setup[1].after_commit = lambda request: None
    before = service.reconcile("refresh")
    assert service.execute("refresh") == before
    assert len(calls) == (0 if lost_phase == "begin" else 1)
    assert before.previous.epoch == 1
    assert (before.result.epoch if before.result else 1) == (2 if lost_phase == "publish" else 1)


def test_refresh_overlap_recovery_and_retained_baseline_epoch_sequence(setup):
    source_service(setup)
    service = refresher(setup)
    intent, created = service.begin("first")
    assert created
    assert (
        setup[0]
        .run(lambda tx: setup[0].source_registry(tx))
        .resolve(None, NOW)
        .source_refresh_outcome
        == "UNAVAILABLE"
    )
    with pytest.raises(RefreshDenied, match="pending"):
        service.begin("overlap")
    hashes = (sha256(b"X").hexdigest(), None, sha256(b"X").hexdigest(), sha256(b"Y").hexdigest())
    epochs = []
    for n, digest in enumerate(hashes):
        key = "first" if n == 0 else f"next{n}"
        if n:
            service.begin(key)
        result = service.publish(key, digest).result
        epochs.append(result.epoch)
    assert epochs == [2, 2, 2, 3]
    old, _ = service.begin("expired")
    setup[5][0] = old.deadline
    new, _ = service.begin("recovery")
    with pytest.raises(RefreshDenied):
        service.publish("expired", sha256(b"late").hexdigest())
    assert service.publish("recovery", hashes[-1]).result.epoch == 3
    assert new.previous.pending_refresh == old.key_hash


@pytest.mark.parametrize("negative", [False, True])
def test_actual_refresh_writer_invalidates_results_actions_queue_and_publish_race(
    setup, env, negative
):
    service = source_service(setup, env)
    token, session, incident = owned(setup)
    envelope = extract(setup, token, incident)
    if negative:
        setup[3].correct(
            token,
            incident.id,
            "negative",
            1,
            "LOT",
            known("unlisted", evidence=envelope.captures[0]),
        )
    publish(setup, env, token, session, incident)
    old = setup[3].read_evidence(token, incident.id)
    target = None
    if not negative:
        target = setup[4].prepare(token, incident.id, ActionType.SIMULATED_HOLD)
    refresh = refresher(setup)
    refresh.begin("refresh")
    assert not setup[3].read_evidence(token, incident.id).current
    refresh.publish("refresh", "c" * 64)
    assert not setup[3].read_evidence(token, incident.id).current
    assert not setup[0].retail.read(token).snapshot.rows[0].current
    if target:
        with pytest.raises(GuestDenied):
            setup[4].confirm(
                token,
                incident.id,
                "stale",
                ActionConfirmation(target=target, explicit_confirmation=True),
            )
    assert setup[3].read_evidence(token, incident.id).result == old.result
    assert service.read(token, incident.id)["selected_choice"] == "sfa"


@pytest.mark.parametrize("failure", [OSError, httpcore.RemoteProtocolError, SourceFetchRefused])
def test_fetch_failure_publishes_unavailable_without_historical_relabel(setup, failure):
    source_service(setup)

    def denied(*args, **kwargs):
        raise failure("controlled failure")

    service = refresher(setup, fetcher=denied)
    done = service.execute("failed")
    assert done.result.status == "UNAVAILABLE" and done.result.epoch == 1
    environment = saved(setup, "source_registry").resolve(None, NOW)
    assert (
        environment.context.mode.value == "LIVE"
        and environment.source_refresh_outcome == "UNAVAILABLE"
    )
    setup[5][0] += timedelta(seconds=30)
    assert (
        saved(setup, "source_registry").resolve(None, setup[5][0]).source_refresh_outcome
        == "EXPIRED"
    )


@pytest.mark.parametrize(
    "values",
    [
        {"url": "http://example.com/"},
        {"url": "https://127.0.0.1/", "allowed_hosts": ("127.0.0.1",)},
        {"url": "https://example.com/#fragment"},
        {"url": "https://example.com:444/"},
        {"url": "https://a@example.com/"},
        {"url": "https://other.example/"},
        {"public_addresses": ("127.0.0.1",)},
        {"public_addresses": ("169.254.169.254",)},
        {"public_addresses": ("::1",)},
        {"public_addresses": ("ff02::1",)},
        {"network_seconds": True},
        {"network_seconds": float("inf")},
        {"max_attempts": 3},
        {"max_body_bytes": 5, "max_wire_bytes": 4},
        {"retry_delay_seconds": 20, "max_attempts": 2},
    ],
)
def test_fetch_configuration_refuses_unsafe_or_invalid_values(values):
    with pytest.raises((ValidationError, ValueError)):
        SourceFetchPolicy.model_validate(
            {
                "url": "https://example.com/",
                "allowed_hosts": ("example.com",),
                "public_addresses": ("8.8.8.8",),
            }
            | values
        )


def test_raw_representation_required_and_config_reaches_actual_fetcher(setup):
    source_service(setup)
    service = refresher(setup)
    registry = saved(setup, "source_registry")
    uk = registry.catalog.choices[1].environment.notices[0]
    ukpolicy = replace(
        service.policy,
        family=uk.dependency.family,
        version=uk.dependency.version,
        expected_hash=uk.dependency.content_hash,
        fetch=replace(service.policy.fetch, url=uk.final_url),
    )
    with pytest.raises(RefreshDenied, match="raw_authority"):
        TrustedRefresh(setup[0], ukpolicy, clock=lambda: setup[5][0]).begin("uk")
    p = SourceFetchPolicy(
        url="https://example.com/", allowed_hosts=("example.com",), public_addresses=("8.8.8.8",)
    )
    with pytest.raises(ValueError):
        fetch_source(p, horizon_seconds=True)


def test_unchanged_refresh_reverification_then_exact_expiry_and_no_network_in_retry(setup, env):
    source_service(setup)
    token, session, incident = owned(setup)
    extract(setup, token, incident)
    publish(setup, env, token, session, incident)
    refresh = refresher(setup)
    setup[1].before_commit = lambda request: None
    refresh.begin("unchanged")
    refresh.publish("unchanged", refresh.policy.expected_hash)
    assert not setup[3].read_evidence(token, incident.id).current
    binding = setup[3].verification_binding(token, incident.id)
    from tests.unit.test_firestore_store import shared

    shared(setup, env).reserve_verification(
        session.capability_hash, incident.id, "live-verify", binding
    )
    setup[3].publish_verification(token, incident.id, "live-verify", binding)
    assert setup[3].read_evidence(token, incident.id).current
    setup[5][0] += timedelta(seconds=30)
    assert not setup[3].read_evidence(token, incident.id).current


def test_transaction_retry_never_repeats_network_and_late_publication_denies(setup, monkeypatch):
    source_service(setup)
    calls, in_callback = [], []
    original_run = setup[0].run

    def run(operation, **kwargs):
        def callback(tx):
            in_callback.append(True)
            try:
                return operation(tx)
            finally:
                in_callback.pop()

        return original_run(callback, **kwargs)

    monkeypatch.setattr(setup[0], "run", run)

    def fetch(policy, **kwargs):
        assert not in_callback
        calls.append(policy)
        return FetchedSource(b"changed", 1)

    service = refresher(setup, fetcher=fetch)
    seen = []

    def abort_once(request):
        if request.writes and not seen:
            seen.append(True)
            raise exceptions.Aborted("retry callback only")

    setup[1].before_commit = abort_once
    result = service.execute("retry")
    assert result.result.epoch == 2 and len(calls) == 1
    pending, _ = service.begin("late")
    setup[5][0] = pending.deadline
    with pytest.raises(RefreshDenied, match="deadline"):
        service.publish("late", service.policy.expected_hash)
    assert service.reconcile("late").result is None


@pytest.mark.parametrize("phase", ["before", "during", "after"])
def test_source_change_action_races_preserve_history_never_current(setup, env, phase):
    source_service(setup)
    token, session, incident = owned(setup)
    extract(setup, token, incident)
    publish(setup, env, token, session, incident)
    target = setup[4].prepare(token, incident.id, ActionType.SIMULATED_HOLD)
    service = refresher(setup)

    def change():
        service.begin("race")
        service.publish("race", "e" * 64)

    if phase == "before":
        change()
    elif phase == "during":

        def race(request):
            if any(
                w.update.name == setup[0].name("actions", session.capability_hash, incident.id)
                for w in request.writes
            ):
                setup[1].before_commit = lambda request: None
                change()

        setup[1].before_commit = race
    if phase != "after":
        with pytest.raises(GuestDenied):
            setup[4].confirm(
                token,
                incident.id,
                "hold",
                ActionConfirmation(target=target, explicit_confirmation=True),
            )
        assert not setup[4].list_actions(token, incident.id)
    else:
        action = setup[4].confirm(
            token,
            incident.id,
            "hold",
            ActionConfirmation(target=target, explicit_confirmation=True),
        )
        change()
        read = setup[4].get_action(token, incident.id, action.action.id)
        assert not read.current and read.requires_renewed_review
    assert not setup[3].read_evidence(token, incident.id).current


class Socket:
    def settimeout(self, value):
        assert value > 0

    def sendall(self, value):
        assert isinstance(value, bytes)


class Stream(httpcore.NetworkStream):
    def __init__(self, raw, clock, tls):
        self.raw, self.clock, self.tls, self.closed = raw, clock, tls, False

    def read(self, max_bytes, timeout=None):
        self.clock[0] += 0.1
        result, self.raw = self.raw[:max_bytes], self.raw[max_bytes:]
        return result

    def close(self):
        self.closed = True

    def get_extra_info(self, key):
        return {"socket": Socket(), "server_addr": ("8.8.8.8", 443)}.get(key)

    def start_tls(self, ssl_context, server_hostname=None, timeout=None):
        assert ssl_context.check_hostname and timeout > 0
        self.tls.append(server_hostname)
        return self


@pytest.mark.parametrize(
    "response,values,expected",
    [
        (b"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nContent-Length: 2\r\n\r\nOK", {}, b"OK"),
        (
            b"HTTP/1.1 302 Found\r\nLocation: http://169.254.169.254/\r\nContent-Length: 0\r\n\r\n",
            {},
            None,
        ),
        (
            b"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n"
            b"Content-Encoding: gzip\r\nContent-Length: 2\r\n\r\nOK",
            {},
            None,
        ),
        (
            b"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nContent-Length: 9\r\n\r\n123456789",
            {"max_body_bytes": 4},
            None,
        ),
        (
            b"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nContent-Length: 2\r\n\r\nOK",
            {"network_seconds": 0.2},
            None,
        ),
    ],
)
def test_actual_httpcore_consumer_public_pin_tls_deadline_refusals(
    monkeypatch, response, values, expected
):
    clock, peers, tls = [0.0], [], []

    class Backend:
        def connect_tcp(self, host, port, **kwargs):
            peers.append((host, port))
            return Stream(response, clock, tls)

    monkeypatch.setattr(httpcore, "SyncBackend", Backend)
    policy = SourceFetchPolicy(
        url="https://example.com/",
        allowed_hosts=("example.com",),
        public_addresses=("8.8.8.8",),
        read_chunk_bytes=16,
        **values,
    )
    if expected:
        assert fetch_source(policy, monotonic=lambda: clock[0]).raw == expected
    else:
        with pytest.raises((SourceFetchRefused, TimeoutError)):
            fetch_source(policy, monotonic=lambda: clock[0])
    assert peers == [("8.8.8.8", 443)] and tls == ["example.com"]


@pytest.mark.parametrize("delta", [-1, 0, 1])
def test_refresh_freshness_must_fit_admitted_verifier_before_any_write(setup, delta):
    source_service(setup)
    service = refresher(setup)
    limit = (
        saved(setup, "source_registry")
        .catalog.environment(None)
        .verifier_policy.live_freshness_seconds
    )
    service = TrustedRefresh(
        setup[0],
        replace(service.policy, freshness_seconds=limit + delta),
        clock=lambda: setup[5][0],
    )
    before = setup[1].versions.copy()
    if delta > 0:
        with pytest.raises(RefreshDenied, match="freshness"):
            service.begin("oversized")
        assert setup[1].versions == before
    else:
        assert service.begin("bounded")[0].deadline > setup[5][0]
