"""Private sanitized images through an explicitly injected Storage SDK client.

No bucket, credential, URL, lifecycle or background worker is created here.
Requests timeouts bound inactivity, not total in-flight cancellation. Deadline
checks prevent late acceptance/new calls; runtime cancellation remains a gate.
"""

import base64
import json
import os
import re
import time
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from io import BytesIO
from typing import Annotated, Literal, Self
from urllib.parse import urlsplit

import google_crc32c
from google.api_core.exceptions import GoogleAPICallError
from google.cloud import storage
from google.cloud.storage.exceptions import DataCorruption, InvalidResponse
from pydantic import Field, TypeAdapter, model_validator
from requests.exceptions import RequestException

from batchbeacon.cloud_policy import ProjectId
from batchbeacon.contracts import Digest, Record
from batchbeacon.guest_service import OpaqueId

Seconds = Annotated[float, Field(gt=0, allow_inf_nan=False)]
Positive = Annotated[int, Field(gt=0)]
# NF-01's stable application ceiling also excludes the SDK's resumable upload
# path, whose corruption cleanup has separate default retries and timeouts.
ObjectBytes = Annotated[int, Field(gt=0, le=5 * 1024 * 1024)]
_SDK_ERRORS = (GoogleAPICallError, RequestException, DataCorruption, InvalidResponse, OSError)
_DATA_ERRORS = (ValueError, TypeError, KeyError, OverflowError, RecursionError)
_CACHE = "private, no-store"
_DISABLE_METADATA = "DISABLE_GCS_PYTHON_CLIENT_OTEL_BUCKET_METADATA"


def _unavailable():
    return OSError("private image evidence unavailable")


class StoragePolicy(Record):
    project_id: ProjectId
    bucket: Annotated[str, Field(pattern=r"^[a-z0-9][a-z0-9_-]{1,61}[a-z0-9]$")]
    namespace: Annotated[str, Field(pattern=r"^[a-z][a-z0-9_-]{0,63}$")]
    mode: Literal["production", "offline_test"]
    api_endpoint: str
    max_object_bytes: ObjectBytes = 5 * 1024 * 1024
    max_metadata_bytes: Positive = 4096
    operation_seconds: Seconds = 15.0
    rpc_seconds: Seconds = 5.0
    max_sdk_calls: Annotated[int, Field(ge=3)] = 3
    retention_seconds: Positive = 86400
    background_metadata: Literal["disabled"] = "disabled"

    @model_validator(mode="after")
    def coherent(self) -> Self:
        url = urlsplit(self.api_endpoint)
        if self.mode == "production":
            valid = re.fullmatch(r"https://(?:[a-z0-9-]+\.)*storage\.googleapis\.com",
                                self.api_endpoint)
        else:
            valid = url.scheme == "http" and url.hostname in {"localhost", "127.0.0.1"} \
                and url.port is not None and 1 <= url.port <= 65535 \
                and self.api_endpoint == f"http://{url.hostname}:{url.port}"
        if not valid or self.rpc_seconds > self.operation_seconds:
            raise ValueError("explicit endpoint and coherent deadlines required")
        timedelta(seconds=self.retention_seconds)
        return self


class _Receipt(Record):
    schema_version: Literal[1] = 1
    session_id: OpaqueId
    incident_id: OpaqueId
    capture_id: OpaqueId
    sha256: Digest
    byte_count: ObjectBytes
    created_at: datetime
    expires_at: datetime
    retention_seconds: Positive
    writer_config_hash: Digest

    @property
    def key(self):
        return f"{self.session_id}/{self.incident_id}/{self.capture_id}/{self.sha256}"

    @model_validator(mode="after")
    def coherent(self) -> Self:
        if self.created_at.tzinfo is None or self.expires_at.tzinfo is None \
                or self.expires_at != self.created_at + timedelta(seconds=self.retention_seconds):
            raise ValueError("invalid object retention evidence")
        return self


class _Operation:
    def __init__(self, owner):
        self.owner, self.calls = owner, 0
        self.deadline = owner.monotonic() + owner.policy.operation_seconds

    def remaining(self):
        remaining = self.deadline - self.owner.monotonic()
        if remaining <= 0:
            raise _unavailable()
        return min(remaining, self.owner.policy.rpc_seconds)

    def call(self, method, *args, **kwargs):
        self.owner._environment()
        if self.calls >= self.owner.policy.max_sdk_calls:
            raise _unavailable()
        timeout = self.remaining()
        self.calls += 1
        result = method(*args, **kwargs, timeout=timeout, retry=None)
        self.remaining()
        return result


class _Sink(BytesIO):
    def __init__(self, limit, operation):
        super().__init__()
        self.limit, self.operation = limit, operation

    def write(self, value):
        self.operation.remaining()
        if self.tell() + len(value) > self.limit:
            raise _unavailable()
        return super().write(value)


def _unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise _unavailable()
        result[key] = value
    return result


class StorageObjects:
    def __init__(self, client: storage.Client, policy: StoragePolicy,
                 *, clock=lambda: datetime.now(UTC), monotonic=time.monotonic):
        if not isinstance(client, storage.Client) or client.project != policy.project_id \
                or client.api_endpoint != policy.api_endpoint:
            raise ValueError("explicit Storage client and matching configuration required")
        self.client, self.policy = client, policy
        self.clock, self.monotonic = clock, monotonic
        self._environment()
        self.bucket = client.bucket(policy.bucket)  # Public no-I/O factory.

    def _environment(self):
        # The pinned SDK otherwise queues bucket-metadata background requests
        # with independent default deadlines/retries, even with tracing disabled.
        # Require its supported process configuration; never mutate global state.
        if os.environ.get(_DISABLE_METADATA) != "true":
            raise ValueError("Storage background metadata must be explicitly disabled")
        # Pinned SDK 3.17.1's 404 helper ignores the flag for cached buckets.
        # Admit only a dedicated, unused/quiescent client, and reject subsequent
        # bucket-info use. Read-only private inspection is deliberately coupled
        # to the locked SDK; no cache clearing or SDK monkeypatch is performed.
        cache = getattr(self.client, "_bucket_metadata_cache", None)
        lock = getattr(cache, "_lock", None)
        if lock is None or not lock.acquire(blocking=False):
            raise ValueError("dedicated quiescent Storage client required")
        try:
            if not all(hasattr(cache, k) for k in
                       ("_cache", "_inflight_fetches", "_inflight_checks")) \
                    or len(cache._cache) or cache._inflight_fetches or cache._inflight_checks:
                raise ValueError("dedicated unused Storage client required")
        finally:
            lock.release()

    def _now(self):
        now = self.clock()
        if now.tzinfo is None or now.utcoffset() is None:
            raise _unavailable()
        return now.astimezone(UTC)

    def _name(self, key):
        if not isinstance(key, str) or len(key.split("/")) != 4:
            raise _unavailable()
        *ids, digest = key.split("/")
        for value in ids:
            TypeAdapter(OpaqueId).validate_python(value)
        TypeAdapter(Digest).validate_python(digest)
        return f"{self.policy.namespace}/{key}"

    def _metadata_size(self, value):
        if len(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()) \
                > self.policy.max_metadata_bytes:
            raise _unavailable()

    def _live(self, receipt):
        # A stricter later retention policy can shorten access, never extend it.
        expiry = min(receipt.expires_at, receipt.created_at +
                     timedelta(seconds=self.policy.retention_seconds))
        if not receipt.created_at <= self._now() < expiry:
            raise _unavailable()

    def _read(self, key, maximum, operation):
        name = self._name(key)
        if type(maximum) is not int or maximum <= 0:
            raise _unavailable()
        limit = min(maximum, self.policy.max_object_bytes)
        metadata = self.bucket.blob(name)
        operation.call(metadata.reload)
        fields = metadata.metadata
        self._metadata_size(fields)
        if not isinstance(fields, dict) or set(fields) != {"batchbeacon"} \
                or not isinstance(fields["batchbeacon"], str):
            raise _unavailable()
        json.loads(fields["batchbeacon"], object_pairs_hook=_unique_pairs)
        receipt = _Receipt.model_validate_json(fields["batchbeacon"])
        generation, metageneration = metadata.generation, metadata.metageneration
        if receipt.key != key or receipt.byte_count > limit \
                or metadata.size != receipt.byte_count \
                or metadata.content_type != "image/png" or metadata.content_encoding is not None \
                or metadata.cache_control != _CACHE \
                or type(generation) is not int or generation <= 0 \
                or type(metageneration) is not int or metageneration <= 0:
            raise _unavailable()
        crc = base64.b64decode(metadata.crc32c, validate=True)
        if len(crc) != 4:
            raise _unavailable()
        self._live(receipt)
        # Never follow a server-returned mediaLink. Construct from this endpoint
        # and bind both object and metadata revisions on a fresh public blob.
        blob = self.bucket.blob(name, generation=generation)
        with _Sink(receipt.byte_count, operation) as sink:
            operation.call(blob.download_to_file, sink, raw_download=True,
                if_generation_match=generation, if_metageneration_match=metageneration,
                checksum="crc32c", single_shot_download=False)
            data = sink.getvalue()
        if len(data) != receipt.byte_count or sha256(data).hexdigest() != receipt.sha256 \
                or google_crc32c.Checksum(data).digest() != crc:
            raise _unavailable()
        self._live(receipt)
        operation.remaining()
        return data

    def put_once(self, key: str, data: bytes, digest: str) -> None:
        try:
            name = self._name(key)
            if type(data) is not bytes or not data.startswith(b"\x89PNG\r\n\x1a\n") \
                    or len(data) > self.policy.max_object_bytes \
                    or sha256(data).hexdigest() != digest or key.split("/")[-1] != digest:
                raise _unavailable()
            now = self._now()
            session, incident, capture, _ = key.split("/")
            receipt = _Receipt(session_id=session, incident_id=incident, capture_id=capture,
                sha256=digest, byte_count=len(data), created_at=now,
                expires_at=now + timedelta(seconds=self.policy.retention_seconds),
                retention_seconds=self.policy.retention_seconds,
                writer_config_hash=self.policy.digest())
            fields = {"batchbeacon": receipt.model_dump_json()}
            self._metadata_size(fields)
            operation = _Operation(self)
            blob = self.bucket.blob(name)
            blob.metadata, blob.cache_control = fields, _CACHE
            try:
                with BytesIO(data) as stream:
                    operation.call(blob.upload_from_file, stream, size=len(data),
                        content_type="image/png", if_generation_match=0, checksum="crc32c")
            except (*_SDK_ERRORS, *_DATA_ERRORS):
                # The create-only write may have committed. Reconcile exactly
                # once; absence or failed reads preserve an unavailable outcome.
                pass
            if self._read(key, len(data), operation) != data:
                raise _unavailable()
        except (*_SDK_ERRORS, *_DATA_ERRORS) as exc:
            raise _unavailable() from exc

    def get(self, key: str, max_bytes: int) -> bytes:
        try:
            return self._read(key, max_bytes, _Operation(self))
        except (*_SDK_ERRORS, *_DATA_ERRORS) as exc:
            raise _unavailable() from exc
