"""S01-S16 local SDK/HTTP and guest integration; no actual bucket or cloud calls."""

import copy
import json
import socket
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from urllib.parse import parse_qs, urlsplit

import google.auth
import pytest
from google.cloud.storage.exceptions import DataCorruption
from pydantic import ValidationError
from requests.exceptions import Timeout

from batchbeacon.guest_service import GuestDenied, GuestPolicy, GuestService
from batchbeacon.storage_objects import StorageObjects, StoragePolicy
from batchbeacon.uploads import sanitize_images
from tests.unit.storage_http_fake import StoredHTTP, response
from tests.unit.test_guest_boundary import ORIGIN, MemoryRepository, picture


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    monkeypatch.setenv("DISABLE_GCS_PYTHON_CLIENT_OTEL_BUCKET_METADATA", "true")
    def forbidden(*args, **kwargs):
        raise AssertionError("network or credential discovery forbidden")
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(google.auth, "default", forbidden)


@pytest.fixture
def setup():
    policy = StoragePolicy(project_id="demo-batchbeacon", bucket="synthetic-images",
        namespace="captures", mode="offline_test", api_endpoint="http://127.0.0.1:8888")
    http, now, mono = StoredHTTP(), [datetime(2026, 10, 18, tzinfo=UTC)], [0.0]
    def build(settings=policy):
        return StorageObjects(http.client(settings), settings,
            clock=lambda: now[0], monotonic=lambda: mono[0])
    objects = build()
    data = picture()
    digest = sha256(data).hexdigest()
    key = "/".join(("1" * 32, "2" * 32, "3" * 32, digest))
    return objects, http, data, key, now, mono, build


def stored(setup):
    objects, http, data, key, *_ = setup
    objects.put_once(key, data, sha256(data).hexdigest())
    return http.objects[(objects.policy.bucket, f"{objects.policy.namespace}/{key}")]


def test_exact_sdk_multipart_raw_download_and_cold_client_reopen(setup):
    objects, http, data, key, _, _, build = setup
    assert not http.calls
    meta, body = stored(setup)
    assert body == data
    assert len(http.calls) == 3
    assert all(c["timeout"] == 5.0 for c in http.calls)
    assert meta["contentType"] == "image/png" and "contentEncoding" not in meta
    assert meta["cacheControl"] == "private, no-store" and "acl" not in meta
    receipt = json.loads(meta["metadata"]["batchbeacon"])
    assert receipt["writer_config_hash"] == objects.policy.digest()
    assert receipt["retention_seconds"] == 86400
    assert build().get(key, len(data)) == data
    query = parse_qs(urlsplit(http.calls[-1]["url"]).query)
    assert query["generation"] == query["ifGenerationMatch"] == ["1"]
    assert query["ifMetagenerationMatch"] == ["1"]
    assert http.calls[-1]["stream"] is True


def test_retry_and_concurrent_clients_preserve_original_receipt(setup):
    objects, http, data, key, now, _, build = setup
    original = copy.deepcopy(stored(setup))
    now[0] += timedelta(hours=1)
    with ThreadPoolExecutor(2) as pool:
        list(pool.map(lambda obj: obj.put_once(key, data, sha256(data).hexdigest()),
                      [objects, build()]))
    assert len(http.objects) == 1 and next(iter(http.objects.values())) == original
    assert [c["method"] for c in http.calls].count("POST") == 3


@pytest.mark.parametrize("change", [
    {"max_object_bytes": 5242881}, {"max_object_bytes": True},
    {"rpc_seconds": 16.0}, {"operation_seconds": float("nan")},
    {"retention_seconds": 0}, {"max_metadata_bytes": 0}, {"max_sdk_calls": 2},
    {"bucket": "../../elsewhere"}, {"namespace": "../x"},
    {"api_endpoint": "http://127.0.0.1:8888/extra"},
    {"mode": "production"}, {"api_endpoint": "https://example.com"},
])
def test_policy_rejects_invalid_or_incompatible_settings(setup, change):
    with pytest.raises((ValidationError, ValueError)):
        StoragePolicy.model_validate(setup[0].policy.model_dump() | change)


def test_explicit_client_configuration_and_effective_overrides(setup):
    objects, http, data, key, _, _, build = setup
    different = StoragePolicy.model_validate(objects.policy.model_dump() | {
        "bucket": "alternate-images", "namespace": "other", "rpc_seconds": 0.25,
        "operation_seconds": 1.0, "retention_seconds": 3600, "max_object_bytes": len(data)})
    revised = build(different)
    revised.put_once(key, data, sha256(data).hexdigest())
    meta = http.objects[(different.bucket, f"other/{key}")][0]
    receipt = json.loads(meta["metadata"]["batchbeacon"])
    assert receipt["retention_seconds"] == 3600
    assert receipt["writer_config_hash"] == different.digest()
    assert all(c["timeout"] == 0.25 and f"/b/{different.bucket}/" in c["url"]
               for c in http.calls)
    with pytest.raises(ValueError):
        StorageObjects(http.client(objects.policy), different.model_copy(
            update={"project_id": "other-project"}))
    with pytest.raises(ValueError):
        StorageObjects(http.client(objects.policy), different.model_copy(
            update={"api_endpoint": "http://127.0.0.1:8889"}))


@pytest.mark.parametrize("key", ["../file", "gs://elsewhere/object", "a/b/c/d", "1/2/3", ""])
def test_invalid_key_never_reaches_sdk(setup, key):
    objects, http, data, *_ = setup
    with pytest.raises(OSError):
        objects.put_once(key, data, sha256(data).hexdigest())
    with pytest.raises(OSError):
        objects.get(key, 100)
    assert not http.calls


def test_invalid_bytes_hash_and_metadata_bound_precede_requests(setup):
    objects, http, data, key, _, _, build = setup
    for content, digest in [(b"", sha256(b"").hexdigest()), (data, "0" * 64),
                            (b"raw file", sha256(b"raw file").hexdigest())]:
        with pytest.raises(OSError):
            objects.put_once(key, content, digest)
    small = build(StoragePolicy.model_validate(objects.policy.model_dump() | {
        "max_metadata_bytes": 20}))
    with pytest.raises(OSError):
        small.put_once(key, data, sha256(data).hexdigest())
    assert not http.calls


@pytest.mark.parametrize("value", [None, "false", "yes", "malformed"])
def test_background_metadata_configuration_required_before_any_sdk_call(setup, monkeypatch, value):
    objects, http, data, key, _, _, build = setup
    name = "DISABLE_GCS_PYTHON_CLIENT_OTEL_BUCKET_METADATA"
    if value is None:
        monkeypatch.delenv(name)
    else:
        monkeypatch.setenv(name, value)
    with pytest.raises(ValueError, match="background metadata"):
        build()
    with pytest.raises(OSError):
        objects.put_once(key, data, sha256(data).hexdigest())
    with pytest.raises(OSError):
        objects.get(key, len(data))
    assert not http.calls


def test_prewarmed_client_is_rejected_at_construction_and_each_call(setup):
    objects, http, data, key, *_ = setup
    client = http.client(objects.policy)
    client.get_bucket(objects.policy.bucket, timeout=0.25, retry=None)
    before = len(http.calls)
    with pytest.raises(ValueError, match="dedicated"):
        StorageObjects(client, objects.policy)
    assert len(http.calls) == before
    objects.client.get_bucket(objects.policy.bucket, timeout=0.25, retry=None)
    before = len(http.calls)
    with pytest.raises(OSError):
        objects.put_once(key, data, sha256(data).hexdigest())
    with pytest.raises(OSError):
        objects.get(key, len(data))
    assert len(http.calls) == before


@pytest.mark.parametrize("state", ["fetch", "check", "locked"])
def test_inflight_or_busy_client_cannot_start_object_operation(setup, state):
    objects, http, data, key, *_ = setup
    cache = objects.client._bucket_metadata_cache
    if state == "locked":
        cache._lock.acquire()
    else:
        getattr(cache, "_inflight_fetches" if state == "fetch" else "_inflight_checks").add(
            objects.policy.bucket)
    try:
        with pytest.raises(OSError):
            objects.put_once(key, data, sha256(data).hexdigest())
        assert not http.calls
    finally:
        if state == "locked":
            cache._lock.release()


def test_deleted_during_download_has_no_background_bucket_request(setup):
    objects, http, data, key, *_ = setup
    stored(setup)
    def remove(request):
        if "alt=media" in request["url"]:
            http.objects.clear()
    http.before = remove
    before = len(http.calls)
    with pytest.raises(OSError):
        objects.get(key, len(data))
    assert len(http.calls) == before + 2
    cache = objects.client._bucket_metadata_cache
    assert not cache._inflight_checks and not cache._inflight_fetches and not len(cache._cache)


@pytest.mark.parametrize("missing", [False, True])
def test_lost_upload_ack_reconciles_only_persisted_exact_bytes(setup, missing):
    objects, http, data, key, *_ = setup
    def lose(request, result):
        if request["method"] == "POST":
            if missing:
                http.objects.clear()
            raise Timeout("injected lost response")
        return result
    http.after = lose
    if missing:
        with pytest.raises(OSError):
            objects.put_once(key, data, sha256(data).hexdigest())
        assert len(http.calls) == 2
    else:
        objects.put_once(key, data, sha256(data).hexdigest())
        assert len(http.calls) == 3, [(c["method"], c["url"]) for c in http.calls]
    assert [c["method"] for c in http.calls].count("POST") == 1


def test_unavailable_reconciliation_never_retries_or_deletes(setup):
    objects, http, data, key, *_ = setup
    def fail(request, result):
        if request["method"] == "POST":
            raise Timeout("unknown write")
        return response(request["url"], 503, {"error": {"message": "unavailable"}})
    http.after = fail
    with pytest.raises(OSError, match="private image evidence unavailable"):
        objects.put_once(key, data, sha256(data).hexdigest())
    assert len(http.calls) == 2 and len(http.objects) == 1


@pytest.mark.parametrize("field,value", [
    ("size", "9999999"), ("contentType", "text/plain"), ("contentEncoding", "gzip"),
    ("cacheControl", "public"), ("generation", "0"), ("metageneration", "0"),
    ("crc32c", "bad"), ("metadata", {}),
])
def test_invalid_object_metadata_denied_before_body(setup, field, value):
    objects, http, _, key, *_ = setup
    meta, _ = stored(setup)
    meta[field] = value
    before = len(http.calls)
    with pytest.raises(OSError):
        objects.get(key, objects.policy.max_object_bytes)
    assert len(http.calls) == before + 1


def test_receipt_identity_duplicate_fields_and_hash_are_not_trusted(setup):
    objects, http, _, key, *_ = setup
    meta, _ = stored(setup)
    original = meta["metadata"]["batchbeacon"]
    variants = []
    for field, value in [("session_id", "f" * 32), ("byte_count", True),
                         ("writer_config_hash", "bad"), ("expires_at", "2026-10-20T00:00:00Z")]:
        variants.append(json.dumps(json.loads(original) | {field: value}))
    variants.append(original[:-1] + ',"schema_version":1}')
    for value in variants:
        meta["metadata"]["batchbeacon"] = value
        with pytest.raises(OSError):
            objects.get(key, objects.policy.max_object_bytes)
    assert len(http.objects) == 1


@pytest.mark.parametrize("kind", ["excess", "short", "corrupt", "changed_generation",
                                  "changed_metageneration"])
def test_body_and_revision_failures_never_return_image(setup, kind):
    objects, http, data, key, *_ = setup
    meta, _ = stored(setup)
    object_key = next(iter(http.objects))
    def change(request):
        if "alt=media" in request["url"]:
            if kind == "changed_generation":
                meta["generation"] = "2"
            elif kind == "changed_metageneration":
                meta["metageneration"] = "2"
            else:
                body = {"excess": data + b"x", "short": data[:-1],
                        "corrupt": data[:-1] + bytes([data[-1] ^ 1])}[kind]
                http.objects[object_key] = (meta, body)
    http.before = change
    before = len(http.calls)
    with pytest.raises(OSError):
        objects.get(key, len(data))
    assert len(http.calls) == before + 2, [
        (c["method"], c["url"], c.get("timeout")) for c in http.calls]


def test_existing_conflict_is_never_overwritten_and_media_link_is_ignored(setup):
    objects, http, data, key, *_ = setup
    meta, _ = stored(setup)
    meta["mediaLink"] = "http://external.invalid/private"
    assert objects.get(key, len(data)) == data
    assert all(c["url"].startswith(objects.policy.api_endpoint) for c in http.calls)
    object_key = next(iter(http.objects))
    http.objects[object_key] = (meta, data[:-1] + b"x")
    with pytest.raises(OSError):
        objects.put_once(key, data, sha256(data).hexdigest())
    assert http.objects[object_key][1] != data


def test_expired_existing_object_cannot_be_renewed(setup):
    objects, http, data, key, now, _, build = setup
    original = copy.deepcopy(stored(setup))
    now[0] += timedelta(seconds=objects.policy.retention_seconds)
    with pytest.raises(OSError):
        objects.get(key, len(data))
    with pytest.raises(OSError):
        objects.put_once(key, data, sha256(data).hexdigest())
    assert next(iter(http.objects.values())) == original
    longer = build(StoragePolicy.model_validate(objects.policy.model_dump() | {
        "retention_seconds": 172800}))
    with pytest.raises(OSError):
        longer.get(key, len(data))


@pytest.mark.parametrize("phase", ["upload", "metadata", "body"])
def test_deadline_denies_late_success_and_further_calls(setup, phase):
    objects, http, data, key, _, mono, _ = setup
    if phase != "upload":
        stored(setup)
        http.calls.clear()
    def delay(request, result):
        if (phase == "upload" and request["method"] == "POST") or \
            (phase == "metadata" and "alt=media" not in request["url"]) or \
            (phase == "body" and "alt=media" in request["url"]):
            mono[0] = objects.policy.operation_seconds
        return result
    http.after = delay
    with pytest.raises(OSError):
        if phase == "upload":
            objects.put_once(key, data, sha256(data).hexdigest())
        else:
            objects.get(key, len(data))
    assert len(http.calls) == (2 if phase == "body" else 1)
    assert len(http.objects) == 1


def test_sdk_checksum_exception_is_sanitized(setup):
    objects, http, data, key, *_ = setup
    stored(setup)
    def corrupt(request, result):
        raise DataCorruption(result, "private transport detail")
    http.after = corrupt
    with pytest.raises(OSError, match="^private image evidence unavailable$"):
        objects.get(key, len(data))


@pytest.mark.parametrize("failed_image", [1, 2])
def test_guest_pending_capture_retry_ownership_and_expiry(setup, failed_image):
    objects, http, data, _, now, _, _ = setup
    service = GuestService(GuestPolicy(origin=ORIGIN), MemoryRepository(), objects,
                           clock=lambda: now[0])
    capability, _ = service.issue()
    incident = service.create_incident(capability, "incident")
    images = sanitize_images((data, picture(size=(9, 6))), service.policy.uploads)
    def fail_image(request, result):
        if request["method"] == "POST" and len(http.objects) == failed_image:
            raise Timeout("unknown image write")
        if len(http.objects) == failed_image and request["method"] == "GET":
            return response(request["url"], 503, {"error": {"message": "unavailable"}})
        return result
    http.after = fail_image
    with pytest.raises(GuestDenied) as error:
        service.retain(capability, incident.id, "images", images)
    assert error.value.status == 503
    pending = service.incident(capability, incident.id).batches[0]
    assert not pending.ready and len(http.objects) == failed_image
    http.after = lambda request, result: result
    ready = service.retain(capability, incident.id, "images", images)
    assert ready.ready and ready.captures == pending.captures
    assert service.image(capability, incident.id, ready.captures[0].id) == images[0].data
    other, _ = service.issue()
    with pytest.raises(GuestDenied):
        service.image(other, incident.id, ready.captures[0].id)
    def expire(request, result):
        if "alt=media" in request["url"]:
            now[0] += timedelta(seconds=service.policy.retail.session_seconds)
        return result
    http.after = expire
    with pytest.raises(GuestDenied):
        service.image(capability, incident.id, ready.captures[0].id)


def test_consumer_size_and_metadata_bounds_reach_actual_read(setup):
    objects, http, data, key, _, _, build = setup
    small = build(StoragePolicy.model_validate(objects.policy.model_dump() | {
        "max_object_bytes": len(data) - 1}))
    with pytest.raises(OSError):
        small.put_once(key, data, sha256(data).hexdigest())
    assert not http.calls
    stored(setup)
    for maximum in (0, True, "100"):
        before = len(http.calls)
        with pytest.raises(OSError):
            objects.get(key, maximum)
        assert len(http.calls) == before
    before = len(http.calls)
    with pytest.raises(OSError):
        objects.get(key, len(data) - 1)
    assert len(http.calls) == before + 1
    with pytest.raises(OSError):
        small.get(key, len(data))
    restricted = build(StoragePolicy.model_validate(objects.policy.model_dump() | {
        "max_metadata_bytes": 20}))
    with pytest.raises(OSError):
        restricted.get(key, len(data))


def test_guest_expiry_during_upload_retains_pending_without_second_image(setup):
    objects, http, data, _, now, _, _ = setup
    service = GuestService(GuestPolicy(origin=ORIGIN), MemoryRepository(), objects,
                           clock=lambda: now[0])
    capability, issued = service.issue()
    incident = service.create_incident(capability, "incident")
    images = sanitize_images((data, picture(size=(9, 6))), service.policy.uploads)
    def expire(request, result):
        if request["method"] == "POST":
            now[0] = issued.scope.expires_at
        return result
    http.after = expire
    with pytest.raises(GuestDenied):
        service.retain(capability, incident.id, "images", images)
    saved = service.repository.get(issued.capability_hash).incidents[0].batches[0]
    assert not saved.ready and len(http.objects) == 1


def test_deeply_nested_receipt_is_sanitized(setup):
    objects, _, data, key, *_ = setup
    meta, _ = stored(setup)
    meta["metadata"]["batchbeacon"] = "[" * 2000 + "]" * 2000
    with pytest.raises(OSError, match="^private image evidence unavailable$"):
        objects.get(key, len(data))


@pytest.mark.parametrize("shape", ["structured_metadata", "large_json_string"])
def test_wire_metadata_recursion_maps_to_unavailable(setup, shape):
    objects, http, data, key, _, _, build = setup
    stored(setup)
    if shape == "large_json_string":
        objects = build(StoragePolicy.model_validate(objects.policy.model_dump() | {
            "max_metadata_bytes": 32768}))
    def malformed(request, result):
        if request["method"] == "GET" and "alt=media" not in request["url"]:
            # Raw wire replacement avoids a failure inside the fake's deepcopy.
            outer = result.json()
            outer.pop("metadata")
            depth = 600 if shape == "structured_metadata" else 11000
            value = "[" * depth + "0" + "]" * depth
            if shape == "large_json_string":
                value = json.dumps(value)
            result._content = (json.dumps(outer)[:-1] + ',"metadata":{"batchbeacon":' +
                               value + '}}').encode()
        return result
    http.after = malformed
    before = len(http.calls)
    with pytest.raises(OSError, match="^private image evidence unavailable$"):
        objects.get(key, len(data))
    assert len(http.calls) == before + 1
