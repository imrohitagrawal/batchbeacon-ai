"""Server-owned guest/capture boundary. No cloud initialization or paid admission.

Repository transactions must retry only the pure callback, atomically replacing a
session aggregate. Object writes happen outside transactions. No concrete cloud or
fallback store is selected here; local tests inject explicitly labelled fakes.
"""

import hmac
import re
import secrets
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from typing import Annotated, Literal, Protocol, Self
from urllib.parse import urlsplit
from uuid import uuid4

from pydantic import Field, ValidationError, model_validator

from batchbeacon.contracts import Digest, EvidenceKind, EvidenceRef, Record
from batchbeacon.retail_contracts import RetailPolicy, ShopScope
from batchbeacon.uploads import SanitizedImage, UploadPolicy

OpaqueId = Annotated[str, Field(pattern=r"^[a-f0-9]{32}$")]
RequestKey = Annotated[str, Field(pattern=r"^[A-Za-z0-9_-]{1,80}$")]


class GuestPolicy(Record):
    origin: str
    mode: Literal["local_test", "deployment"] = "deployment"
    retail: RetailPolicy = RetailPolicy()
    uploads: UploadPolicy = UploadPolicy()
    capability_bytes: Annotated[int, Field(ge=32, le=64)] = 32
    # A storage allowance only; does not authorize/reset AI acquisition counters.
    max_capture_batches_per_incident: Annotated[int, Field(gt=0)] = 3

    @model_validator(mode="after")
    def coherent(self) -> Self:
        origin = urlsplit(self.origin)
        if (
            origin.scheme not in {"http", "https"}
            or not origin.hostname
            or origin.username
            or origin.password
            or origin.path
            or origin.query
            or origin.fragment
            or self.origin != f"{origin.scheme}://{origin.netloc}"
        ):
            raise ValueError("origin must be an exact scheme/host/port origin")
        _ = origin.port  # Validate malformed ports, too.
        if self.mode == "deployment" and origin.scheme != "https":
            raise ValueError("deployment requires HTTPS")
        if self.mode == "local_test" and origin.hostname not in {"localhost", "127.0.0.1"}:
            raise ValueError("local test mode requires loopback")
        if self.uploads.read_deadline_seconds >= self.retail.session_seconds:
            raise ValueError("upload deadline must fit the session")
        return self

    @property
    def cookie_name(self) -> str:
        return "__Host-bb_guest" if self.mode == "deployment" else "bb_local_guest"


class GuestDenied(Exception):
    """Safe public denial: no client values or foreign-record details."""

    def __init__(self, status: int, code: str):
        self.status, self.code = status, code
        super().__init__(code)


class Capture(Record):
    id: OpaqueId
    sha256: Digest
    byte_count: Annotated[int, Field(gt=0)]
    width: Annotated[int, Field(gt=0)]
    height: Annotated[int, Field(gt=0)]
    mime_type: Literal["image/png"] = "image/png"

    def evidence(self) -> EvidenceRef:
        return EvidenceRef(
            kind=EvidenceKind.CAPTURE,
            artifact_id=self.id,
            sha256=self.sha256,
            locator="complete sanitized image",
        )


class CaptureBatch(Record):
    request_key: RequestKey
    captures: tuple[Capture, ...] = Field(min_length=1, max_length=2)
    ready: bool = False


class GuestIncident(Record):
    id: OpaqueId
    request_key: RequestKey
    batches: tuple[CaptureBatch, ...] = ()


class GuestSession(Record):
    capability_hash: Digest
    scope: ShopScope
    policy_hash: Digest
    demo_manager: Literal[True] = True
    incidents: tuple[GuestIncident, ...] = ()


class GuestRepository(Protocol):
    """Durable adapters must validate stored JSON and atomically run callbacks.

    Missing/corrupt data and infrastructure errors must not return a new empty
    store. Server-selected capability digest is the only aggregate lookup key.
    Callbacks may run more than once; no provider/object/network effects inside.
    """

    def create(self, session: GuestSession) -> None: ...
    def get(self, capability_hash: str) -> GuestSession | None: ...
    def transact(
        self, capability_hash: str, change: Callable[[GuestSession | None], GuestSession]
    ) -> GuestSession: ...


class PrivateObjects(Protocol):
    """Server-only create-if-absent objects; never return a public/signed URL.

    put_once must reconcile identical bytes and refuse conflicting existing data.
    get must bound downloaded bytes, and fail on absent/corrupt infrastructure.
    Pending references are retained for bounded retry/authorized orphan cleanup.
    """

    def put_once(self, key: str, data: bytes, digest: str) -> None: ...
    def get(self, key: str, max_bytes: int) -> bytes: ...


def csrf_for(capability: str) -> str:
    return hmac.new(capability.encode(), b"batchbeacon-csrf-v1", "sha256").hexdigest()


class GuestService:
    def __init__(
        self,
        policy: GuestPolicy,
        repository: GuestRepository,
        objects: PrivateObjects,
        *,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ):
        if repository is None or objects is None:
            raise ValueError("explicit repository and private-object adapters are required")
        self.policy, self.repository, self.objects, self.clock = policy, repository, objects, clock

    @staticmethod
    def _storage(call, *args):
        try:
            return call(*args)
        except (OSError, KeyError, ValidationError) as exc:
            # Keep pending outcomes for reconciliation; never invent an empty store.
            raise GuestDenied(503, "evidence_temporarily_unavailable") from exc

    def _now(self) -> datetime:
        now = self.clock()
        if now.tzinfo is None or now.utcoffset() is None:
            raise ValueError("server clock must be timezone-aware")
        return now

    def _key(self, capability: str | None) -> str:
        if not capability or not re.fullmatch(r"[A-Za-z0-9_-]{43,86}", capability):
            raise GuestDenied(401, "guest_expired_or_invalid")
        return sha256(capability.encode()).hexdigest()

    def _live(self, session: GuestSession | None, key: str) -> GuestSession:
        if (
            session is None
            or session.capability_hash != key
            or session.policy_hash != self.policy.digest()
            or not session.scope.issued_at <= self._now() < session.scope.expires_at
            or (session.scope.expires_at - session.scope.issued_at).total_seconds()
            != self.policy.retail.session_seconds
        ):
            raise GuestDenied(401, "guest_expired_or_invalid")
        return session

    def resolve(self, capability: str | None) -> GuestSession:
        key = self._key(capability)
        return self._live(self._storage(self.repository.get, key), key)

    def guard(
        self, origin: str | None, capability: str | None = None, csrf: str | None = None
    ) -> None:
        if origin != self.policy.origin:
            raise GuestDenied(403, "same_origin_required")
        if capability is not None:
            self.resolve(capability)
            if (
                not csrf
                or not re.fullmatch(r"[a-f0-9]{64}", csrf)
                or not hmac.compare_digest(csrf, csrf_for(capability))
            ):
                raise GuestDenied(403, "confirmation_token_required")

    def issue(self) -> tuple[str, GuestSession]:
        capability = secrets.token_urlsafe(self.policy.capability_bytes)
        now = self._now()
        session = GuestSession(
            capability_hash=self._key(capability),
            policy_hash=self.policy.digest(),
            scope=ShopScope(
                session_id=uuid4().hex,
                shop_id=uuid4().hex,
                issued_at=now,
                expires_at=now + timedelta(seconds=self.policy.retail.session_seconds),
            ),
        )
        self._storage(self.repository.create, session)
        return capability, self._live(session, session.capability_hash)

    def create_incident(self, capability: str, request_key: str) -> GuestIncident:
        key, incident = (
            self._key(capability),
            GuestIncident(id=uuid4().hex, request_key=request_key),
        )

        def change(stored):
            session = self._live(stored, key)
            if any(i.request_key == request_key for i in session.incidents):
                return session
            if len(session.incidents) >= self.policy.retail.max_incidents:
                raise GuestDenied(429, "incident_allowance_exhausted")
            return session.model_copy(update={"incidents": (*session.incidents, incident)})

        result = self._storage(self.repository.transact, key, change)
        self._live(result, key)
        return next(i for i in result.incidents if i.request_key == request_key)

    @staticmethod
    def _incident(session: GuestSession, incident_id: str) -> GuestIncident:
        incident = next((i for i in session.incidents if i.id == incident_id), None)
        if incident is None:
            raise GuestDenied(404, "evidence_unavailable")
        return incident

    def incident(self, capability: str, incident_id: str) -> GuestIncident:
        return self._incident(self.resolve(capability), incident_id)

    @staticmethod
    def _object_key(session: GuestSession, incident_id: str, capture: Capture) -> str:
        return f"{session.scope.session_id}/{incident_id}/{capture.id}/{capture.sha256}"

    def retain(
        self,
        capability: str,
        incident_id: str,
        request_key: str,
        images: tuple[SanitizedImage, ...],
    ) -> CaptureBatch:
        key = self._key(capability)
        policy = self.policy.uploads
        if (
            not 1 <= len(images) <= policy.max_images
            or any(
                len(i.data) > policy.max_image_bytes or i.width * i.height > policy.max_image_pixels
                for i in images
            )
            or sum(i.width * i.height for i in images) > policy.max_combined_pixels
        ):
            raise GuestDenied(422, "invalid_image")
        proposed = CaptureBatch(
            request_key=request_key,
            captures=tuple(
                Capture(
                    id=uuid4().hex,
                    sha256=sha256(i.data).hexdigest(),
                    byte_count=len(i.data),
                    width=i.width,
                    height=i.height,
                )
                for i in images
            ),
        )

        def reserve(stored):
            session = self._live(stored, key)
            incident = self._incident(session, incident_id)
            existing = next((b for b in incident.batches if b.request_key == request_key), None)
            if existing:
                if tuple(c.model_dump(exclude={"id"}) for c in existing.captures) != tuple(
                    c.model_dump(exclude={"id"}) for c in proposed.captures
                ):
                    raise GuestDenied(409, "capture_request_conflict")
                return session
            if len(incident.batches) >= self.policy.max_capture_batches_per_incident:
                raise GuestDenied(429, "capture_allowance_exhausted")
            updated = incident.model_copy(update={"batches": (*incident.batches, proposed)})
            return session.model_copy(
                update={
                    "incidents": tuple(
                        updated if i.id == incident_id else i for i in session.incidents
                    )
                }
            )

        session = self._storage(self.repository.transact, key, reserve)
        batch = next(
            b for b in self._incident(session, incident_id).batches if b.request_key == request_key
        )
        # Repeat even for ready retries: verify exact objects, without creating new identities.
        for capture, image in zip(batch.captures, images, strict=True):
            self.resolve(capability)
            object_key = self._object_key(session, incident_id, capture)
            self._storage(self.objects.put_once, object_key, image.data, capture.sha256)
            self._bytes(session, incident_id, capture)

        def finish(stored):
            current = self._live(stored, key)
            incident = self._incident(current, incident_id)
            updated = incident.model_copy(
                update={
                    "batches": tuple(
                        b.model_copy(update={"ready": True}) if b == batch else b
                        for b in incident.batches
                    )
                }
            )
            return current.model_copy(
                update={
                    "incidents": tuple(
                        updated if i.id == incident_id else i for i in current.incidents
                    )
                }
            )

        final = self._storage(self.repository.transact, key, finish)
        self._live(final, key)
        return next(
            b for b in self._incident(final, incident_id).batches if b.request_key == request_key
        )

    def _bytes(self, session: GuestSession, incident_id: str, capture: Capture) -> bytes:
        data = self._storage(
            self.objects.get,
            self._object_key(session, incident_id, capture),
            self.policy.uploads.max_image_bytes,
        )
        if len(data) != capture.byte_count or sha256(data).hexdigest() != capture.sha256:
            raise GuestDenied(503, "evidence_unavailable")
        return data

    def image(self, capability: str, incident_id: str, capture_id: str) -> bytes:
        session = self.resolve(capability)
        incident = self._incident(session, incident_id)
        capture = next(
            (c for b in incident.batches if b.ready for c in b.captures if c.id == capture_id), None
        )
        if capture is None:
            raise GuestDenied(404, "evidence_unavailable")
        data = self._bytes(session, incident_id, capture)
        self.resolve(capability)  # A slow object read must not outlive access expiry.
        return data
