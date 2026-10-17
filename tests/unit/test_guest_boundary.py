"""T09 requirements-first LOCAL adapter evidence. No real persistence/model claims."""

from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from io import BytesIO
from threading import RLock

import pytest
from fastapi.testclient import TestClient
from PIL import Image, PngImagePlugin
from pydantic import ValidationError

from batchbeacon.guest_api import create_guest_test_app
from batchbeacon.guest_service import GuestDenied, GuestPolicy, GuestService, GuestSession
from batchbeacon.retail_contracts import RetailPolicy
from batchbeacon.uploads import InvalidUpload, UploadPolicy, sanitize_images

ORIGIN = "https://batchbeacon.example"


class MemoryRepository:
    """Test fake: retries pure callbacks, serializes contracts, shares an atomic lock."""

    def __init__(self):
        self.data, self.lock = {}, RLock()
        self.fail_commit = False

    def create(self, session):
        with self.lock:
            assert session.capability_hash not in self.data
            self.data[session.capability_hash] = session.model_dump_json()

    def get(self, key):
        with self.lock:
            return GuestSession.model_validate_json(self.data[key]) if key in self.data else None

    def transact(self, key, change):
        with self.lock:
            stored = self.get(key)
            first, result = change(stored), change(stored)
            assert first == result  # Retry may not generate IDs, timestamps, side effects.
            if self.fail_commit:
                raise OSError("injected commit failure")
            self.data[key] = result.model_dump_json()
            return result


class MemoryObjects:
    def __init__(self):
        self.data, self.lock = {}, RLock()
        self.on_put = lambda: None

    def put_once(self, key, data, digest):
        with self.lock:
            assert sha256(data).hexdigest() == digest
            if key in self.data and self.data[key] != data:
                raise OSError("injected object conflict")
            self.data[key] = data
            self.on_put()

    def get(self, key, max_bytes):
        data = self.data[key]
        if len(data) > max_bytes:
            raise OSError("object too large")
        return data


def picture(fmt="PNG", size=(8, 6), **kwargs):
    out = BytesIO()
    Image.new("RGB", size, "orange").save(out, format=fmt, **kwargs)
    return out.getvalue()


@pytest.fixture
def boundary():
    clock = [datetime(2026, 10, 18, tzinfo=UTC)]
    repository, objects = MemoryRepository(), MemoryObjects()
    service = GuestService(GuestPolicy(origin=ORIGIN), repository, objects, clock=lambda: clock[0])
    return service, repository, objects, clock


def client(service):
    return TestClient(create_guest_test_app(service), base_url=service.policy.origin)


def guest(client):
    response = client.post("/api/guest", headers={"Origin": ORIGIN})
    assert response.status_code == 200
    return {
        "Origin": ORIGIN,
        "X-CSRF-Token": response.json()["csrf_token"],
        "Idempotency-Key": "one",
    }


def incident(client, headers):
    response = client.post("/api/incidents", headers=headers)
    assert response.status_code == 200, response.text
    return response.json()["incident_id"]


def upload(client, headers, incident_id, data=None, **kwargs):
    return client.post(
        f"/api/incidents/{incident_id}/captures",
        headers=headers,
        files=[("images", ("wrong.txt", data or picture(), "text/plain"))],
        **kwargs,
    )


def test_guest_cookie_server_scope_refresh_expiry_and_no_capability_in_body(boundary):
    service, repository, _, clock = boundary
    a, b = client(service), client(service)
    response = a.post("/api/guest", headers={"Origin": ORIGIN})
    guest(b)
    cookie = response.headers["set-cookie"]
    for part in ("__Host-bb_guest", "HttpOnly", "Secure", "SameSite=strict", "Path=/"):
        assert part in cookie
    token = a.cookies[service.policy.cookie_name]
    assert token not in response.text and "Domain=" not in cookie
    sessions = [GuestSession.model_validate_json(s) for s in repository.data.values()]
    assert len({s.scope.shop_id for s in sessions}) == 2
    assert len({s.scope.session_id for s in sessions}) == 2
    assert all(s.demo_manager for s in sessions)
    clock[0] += timedelta(hours=7)
    refreshed = a.post("/api/guest", headers={"Origin": ORIGIN})
    assert refreshed.json() == response.json()
    assert "Max-Age=3600" in refreshed.headers["set-cookie"]
    clock[0] += timedelta(hours=1)
    assert a.get("/api/incidents").status_code == 401
    assert a.post("/api/guest", headers={"Origin": ORIGIN}).status_code == 401
    assert len(repository.data) == 2


@pytest.mark.parametrize(
    "origin",
    [
        None,
        "null",
        "http://batchbeacon.example",
        "https://batchbeacon.example.evil",
        ORIGIN + ":443",
    ],
)
def test_bad_origin_cannot_issue_or_mutate(boundary, origin):
    service, repository, _, _ = boundary
    c = client(service)
    response = c.post("/api/guest", headers={} if origin is None else {"Origin": origin})
    assert response.status_code == 403 and not repository.data
    headers = guest(c)
    headers.pop("Origin")
    if origin is not None:
        headers["Origin"] = origin
    assert c.post("/api/incidents", headers=headers).status_code == 403
    assert c.get("/api/incidents").json() == {"incident_ids": []}


@pytest.mark.parametrize("csrf", [None, "wrong", "0" * 64, "é" * 64])
def test_bad_csrf_cannot_mutate(boundary, csrf):
    service, _, _, _ = boundary
    c = client(service)
    headers = guest(c)
    headers.pop("X-CSRF-Token")
    if csrf == "é" * 64:
        # HTTPX correctly refuses non-ASCII headers; direct guard still fails safely.
        with pytest.raises(GuestDenied):
            service.guard(ORIGIN, c.cookies[service.policy.cookie_name], csrf)
        return
    if csrf:
        headers["X-CSRF-Token"] = csrf
    assert c.post("/api/incidents", headers=headers).status_code == 403
    assert c.get("/api/incidents").json() == {"incident_ids": []}


def test_cross_session_nested_reads_lists_writes_and_expiry(boundary):
    service, _, objects, clock = boundary
    a, b = client(service), client(service)
    ha, hb = guest(a), guest(b)
    ia, ib = incident(a, ha), incident(b, hb)
    response = upload(a, ha, ia)
    assert response.status_code == 200
    capture = response.json()["captures"][0]
    path = f"/api/incidents/{ia}/captures/{capture['id']}"
    good = a.get(path)
    assert good.status_code == 200 and sha256(good.content).hexdigest() == capture["sha256"]
    assert good.headers["cache-control"] == "no-store, private"
    assert good.headers["x-content-type-options"] == "nosniff"
    assert b.get("/api/incidents").json() == {"incident_ids": [ib]}
    assert b.get(path).json() == b.get(path.replace(ia, "0" * 32)).json()
    assert b.get(path.replace(ia, ib)).status_code == 404
    assert upload(b, hb, ia).status_code == 404
    clock[0] += timedelta(hours=8)
    assert a.get(path).status_code == 401 and objects.data
    assert upload(a, ha, ia).status_code == 401


@pytest.mark.parametrize("authority", ["actor", "session_id", "shop_id", "pool", "reviewed"])
def test_body_authority_is_not_accepted(boundary, authority):
    service, _, _, _ = boundary
    c = client(service)
    headers = guest(c)
    assert c.post("/api/incidents", headers=headers, json={authority: True}).status_code == 422
    assert c.get("/api/incidents").json() == {"incident_ids": []}


@pytest.mark.parametrize("fmt", ["JPEG", "PNG", "WEBP"])
def test_supported_formats_retain_pixel_only_exact_png(fmt):
    exif = Image.Exif()
    exif[274], exif[315] = 6, "synthetic author"
    data = picture(fmt, exif=exif)
    (sanitized,) = sanitize_images((data,), UploadPolicy())
    assert (sanitized.width, sanitized.height) == (6, 8)
    with Image.open(BytesIO(sanitized.data)) as image:
        assert image.format == "PNG" and not image.info and not image.getexif()
        image.load()


def test_png_comments_removed():
    metadata = PngImagePlugin.PngInfo()
    metadata.add_text("private", "synthetic metadata")
    (output,) = sanitize_images((picture(pnginfo=metadata),), UploadPolicy())
    with Image.open(BytesIO(output.data)) as image:
        assert not image.info


@pytest.mark.parametrize(
    "inputs",
    [
        (),
        (b"",),
        (b"<svg/>",),
        (b"%PDF-1.0",),
        (picture("GIF"),),
        (picture()[:35],),
        (picture(),) * 3,
    ],
)
def test_reject_invalid_type_count_or_truncation(inputs):
    with pytest.raises(InvalidUpload):
        sanitize_images(inputs, UploadPolicy())


def test_animated_image_rejected():
    buf = BytesIO()
    Image.new("RGB", (2, 2), "red").save(
        buf, format="WEBP", save_all=True, append_images=[Image.new("RGB", (2, 2), "blue")]
    )
    with pytest.raises(InvalidUpload, match="still"):
        sanitize_images((buf.getvalue(),), UploadPolicy())


def test_individual_and_combined_pixel_bounds_inclusive():
    policy = UploadPolicy(max_image_pixels=48, max_combined_pixels=96)
    assert len(sanitize_images((picture(), picture()), policy)) == 2
    with pytest.raises(InvalidUpload, match="pixel"):
        sanitize_images((picture(size=(7, 7)),), policy)
    policy = UploadPolicy(max_image_pixels=48, max_combined_pixels=95)
    with pytest.raises(InvalidUpload, match="combined"):
        sanitize_images((picture(), picture()), policy)


def test_input_and_sanitized_output_bytes_bounded():
    data = picture()
    size = len(data)
    policy = UploadPolicy(max_image_bytes=size, spool_bytes=size)
    assert sanitize_images((data,), policy)
    with pytest.raises(InvalidUpload, match="byte"):
        sanitize_images((data + b"x",), policy)
    # Compressed WebP can expand to a larger PNG; bound the retained encoding too.
    data = picture("WEBP")
    policy = UploadPolicy(max_image_bytes=len(data), spool_bytes=len(data))
    with pytest.raises(InvalidUpload, match="sanitized"):
        sanitize_images((data,), policy)


def test_upload_controls_count_fields_incomplete_and_stream_bytes(boundary):
    service, _, objects, _ = boundary
    c = client(service)
    headers = guest(c)
    iid = incident(c, headers)
    path = f"/api/incidents/{iid}/captures"
    assert c.post(path, headers=headers, files=[("images", picture())] * 3).status_code == 422
    assert c.post(path, headers=headers, data={"url": "https://example.com"}).status_code == 415
    assert c.post(path, headers=headers, files={"actor": (None, "manager")}).status_code == 422
    incomplete = b'--x\r\nContent-Disposition: form-data; name="images"; filename="a"\r\n\r\nabc'
    multipart_headers = {**headers, "Content-Type": "multipart/form-data; boundary=x"}
    assert c.post(path, headers=multipart_headers, content=incomplete).status_code == 422
    assert not objects.data
    # No Content-Length is present: stream accounting still stops before parsing/retention.
    oversized = (b"x" * service.policy.uploads.max_request_bytes, b"x")
    assert c.post(path, headers=multipart_headers, content=iter(oversized)).status_code == 413
    assert not objects.data


def test_upload_retry_conflict_and_pending_commit_reconciliation(boundary):
    service, repository, objects, _ = boundary
    token, _ = service.issue()
    iid = service.create_incident(token, "i").id
    images = sanitize_images((picture(),), service.policy.uploads)
    objects.on_put = lambda: setattr(repository, "fail_commit", True)
    with pytest.raises(GuestDenied, match="temporarily_unavailable"):
        service.retain(token, iid, "u", images)
    pending = service.incident(token, iid).batches[0]
    assert not pending.ready and len(objects.data) == 1
    with pytest.raises(GuestDenied):
        service.image(token, iid, pending.captures[0].id)
    repository.fail_commit, objects.on_put = False, lambda: None
    ready = service.retain(token, iid, "u", images)
    assert ready.ready and ready.captures == pending.captures and len(objects.data) == 1
    # Simulate a fresh service instance sharing storage and a lost success response.
    fresh = GuestService(service.policy, repository, objects, clock=service.clock)
    assert fresh.retain(token, iid, "u", images) == ready
    assert fresh.image(token, iid, ready.captures[0].id) == images[0].data
    with pytest.raises(GuestDenied) as error:
        fresh.retain(
            token, iid, "u", sanitize_images((picture(size=(3, 3)),), service.policy.uploads)
        )
    assert error.value.status == 409


def test_corrupt_image_never_returned_and_slow_read_cannot_outlive_expiry(boundary):
    service, _, objects, clock = boundary
    token, _ = service.issue()
    iid = service.create_incident(token, "i").id
    images = sanitize_images((picture(),), service.policy.uploads)
    batch = service.retain(token, iid, "u", images)
    key = next(iter(objects.data))
    objects.data[key] = b"wrong"
    with pytest.raises(GuestDenied, match="evidence_unavailable"):
        service.image(token, iid, batch.captures[0].id)
    objects.data[key] = images[0].data
    original = objects.get

    def expire(key, max_bytes):
        clock[0] += timedelta(hours=8)
        return original(key, max_bytes)

    objects.get = expire
    with pytest.raises(GuestDenied, match="guest_expired"):
        service.image(token, iid, batch.captures[0].id)


def test_atomic_incident_allowance_across_services_and_retries(boundary):
    service, repository, objects, clock = boundary
    policy = GuestPolicy(origin=ORIGIN, retail=RetailPolicy(max_incidents=1, max_summary_rows=1))
    a = GuestService(policy, repository, objects, clock=lambda: clock[0])
    b = GuestService(policy, repository, objects, clock=lambda: clock[0])
    token, _ = a.issue()

    def attempt(item):
        adapter, key = item
        try:
            return adapter.create_incident(token, key)
        except GuestDenied:
            return None

    with ThreadPoolExecutor(2) as pool:
        results = list(pool.map(attempt, [(a, "a"), (b, "b")]))
    assert sum(r is not None for r in results) == 1
    winner = next(r for r in results if r)
    assert a.create_incident(token, winner.request_key) == winner
    assert len(a.resolve(token).incidents) == 1


@pytest.mark.parametrize(
    "override",
    [
        {"max_images": 3},
        {"max_image_bytes": True},
        {"max_image_pixels": "4"},
        {"max_combined_pixels": 0},
        {"read_deadline_seconds": -1},
        {"png_compress_level": 10},
        {"spool_bytes": 6 * 1024 * 1024},
        {"read_deadline_seconds": float("nan")},
    ],
)
def test_strict_upload_policy(override):
    with pytest.raises(ValidationError):
        UploadPolicy(**override)


@pytest.mark.parametrize(
    "override",
    [
        {"origin": ORIGIN + "/"},
        {"origin": "http://a"},
        {"origin": "https://user:pass@a"},
        {"origin": "https://a:wrong"},
        {"capability_bytes": 16},
        {"capability_bytes": True},
        {"mode": "local_test"},
    ],
)
def test_strict_guest_policy(override):
    with pytest.raises(ValidationError):
        GuestPolicy(**{"origin": ORIGIN, **override})


def test_policy_overrides_reach_http_expiry_and_upload_consumer(boundary):
    _, repository, objects, clock = boundary
    policy = GuestPolicy(
        origin=ORIGIN,
        retail=RetailPolicy(session_seconds=60),
        uploads=UploadPolicy(max_images=1, max_image_pixels=47, max_combined_pixels=47),
    )
    service = GuestService(policy, repository, objects, clock=lambda: clock[0])
    c = client(service)
    h = guest(c)
    iid = incident(c, h)
    assert upload(c, h, iid).status_code == 422
    assert not objects.data
    clock[0] += timedelta(seconds=60)
    assert c.get("/api/incidents").status_code == 401


def test_default_shell_never_mounts_guest_or_paid_routes(boundary):
    from batchbeacon.app import app

    assert TestClient(app).post("/api/guest").status_code == 404
    c = client(boundary[0])
    assert c.get("/healthz").json()["paid_admission"] == "closed"
    assert c.post("/api/extract").status_code == 404


def test_transparent_background_does_not_obscure_black_label_marks():
    source = Image.new("RGBA", (2, 1), (0, 0, 0, 0))
    source.putpixel((0, 0), (0, 0, 0, 255))
    raw = BytesIO()
    source.save(raw, format="PNG")
    (result,) = sanitize_images((raw.getvalue(),), UploadPolicy())
    with Image.open(BytesIO(result.data)) as image:
        assert image.getpixel((0, 0)) == (0, 0, 0)
        assert image.getpixel((1, 0)) == (255, 255, 255)


def test_missing_or_corrupt_storage_returns_useful_denial_without_fallback(boundary):
    service, repository, objects, _ = boundary
    c = client(service)
    headers = guest(c)
    iid = incident(c, headers)
    result = upload(c, headers, iid).json()
    capture = result["captures"][0]
    path = f"/api/incidents/{iid}/captures/{capture['id']}"
    objects.data.clear()
    response = c.get(path)
    assert response.status_code == 503
    assert response.json() == {"error": "evidence_temporarily_unavailable"}
    assert response.headers["cache-control"] == "no-store, private"
    key = next(iter(repository.data))
    repository.data[key] = '{"corrupt":"private record"}'
    response = c.get("/api/incidents")
    assert response.status_code == 503 and "private record" not in response.text
    assert repository.data[key] == '{"corrupt":"private record"}'
    with pytest.raises(ValueError, match="explicit"):
        GuestService(service.policy, None, objects)


def test_capture_storage_allowance_survives_retry_and_reopen(boundary):
    service, repository, objects, _ = boundary
    policy = GuestPolicy(origin=ORIGIN, max_capture_batches_per_incident=1)
    service = GuestService(policy, repository, objects, clock=service.clock)
    token, _ = service.issue()
    iid = service.create_incident(token, "i").id
    images = sanitize_images((picture(),), policy.uploads)
    first = service.retain(token, iid, "u", images)
    fresh = GuestService(policy, repository, objects, clock=service.clock)
    assert fresh.retain(token, iid, "u", images) == first
    with pytest.raises(GuestDenied, match="capture_allowance"):
        fresh.retain(token, iid, "another", images)
    assert len(objects.data) == 1


def test_expiry_during_upload_retains_pending_and_cannot_become_ready(boundary):
    service, _, objects, clock = boundary
    token, _ = service.issue()
    iid = service.create_incident(token, "i").id
    objects.on_put = lambda: clock.__setitem__(0, clock[0] + timedelta(hours=8))
    with pytest.raises(GuestDenied, match="guest_expired"):
        service.retain(token, iid, "u", sanitize_images((picture(),), service.policy.uploads))
    assert objects.data  # Bounded pending object, no invented cleanup or ready evidence.
    stored = service.repository.get(sha256(token.encode()).hexdigest())
    assert not stored.incidents[0].batches[0].ready


def test_alpha_matte_override_reaches_sanitizer():
    buf = BytesIO()
    Image.new("RGBA", (1, 1), (0, 0, 0, 0)).save(buf, format="PNG")
    (output,) = sanitize_images((buf.getvalue(),), UploadPolicy(alpha_matte=(200, 210, 220)))
    with Image.open(BytesIO(output.data)) as image:
        assert image.getpixel((0, 0)) == (200, 210, 220)
    with pytest.raises(ValidationError):
        UploadPolicy(alpha_matte=(256, 0, 0))


def test_unterminated_upload_closes_every_parser_temporary_file(boundary, monkeypatch):
    import asyncio

    import starlette.formparsers as parser_module
    from starlette.requests import Request

    from batchbeacon.guest_api import _images

    temporary_files = []
    original = parser_module.SpooledTemporaryFile

    def tracked(*args, **kwargs):
        file = original(*args, **kwargs)
        temporary_files.append(file)
        return file

    monkeypatch.setattr(parser_module, "SpooledTemporaryFile", tracked)
    payload = (
        b'--x\r\nContent-Disposition: form-data; name="images"; '
        b'filename="a.png"\r\n\r\n' + b"x" * 64
    )

    async def receive():
        return {"type": "http.request", "body": payload, "more_body": False}

    request = Request(
        {"type": "http", "headers": [(b"content-type", b"multipart/form-data; boundary=x")]},
        receive,
    )
    with pytest.raises(GuestDenied) as denied:
        asyncio.run(_images(request, UploadPolicy(spool_bytes=10)))
    assert denied.value.status == 422
    assert temporary_files and all(f.closed for f in temporary_files)


@pytest.mark.parametrize("operation", ["issue", "incident", "capture"])
def test_expiry_after_storage_commit_denies_success_response(boundary, operation, monkeypatch):
    service, repository, _, clock = boundary
    c = client(service)
    if operation == "issue":
        original = repository.create

        def delayed_create(session):
            original(session)
            clock[0] += timedelta(hours=8)

        monkeypatch.setattr(repository, "create", delayed_create)
        response = c.post("/api/guest", headers={"Origin": ORIGIN})
    else:
        headers = guest(c)
        iid = incident(c, headers) if operation == "capture" else None
        original = repository.transact

        def delayed_commit(key, change):
            result = original(key, change)
            if operation == "incident" or any(b.ready for i in result.incidents for b in i.batches):
                clock[0] += timedelta(hours=8)
            return result

        monkeypatch.setattr(repository, "transact", delayed_commit)
        response = (
            upload(c, headers, iid)
            if operation == "capture"
            else c.post("/api/incidents", headers=headers)
        )
    assert response.status_code == 401
    assert response.json() == {"error": "guest_expired_or_invalid"}
    assert repository.data  # Committed state retained; no false rollback after a lost response.
