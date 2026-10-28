"""One fixed authority URL with pinned public peers, verified TLS and finite I/O.

Source bytes are untrusted. This module hashes raw HTTP bodies only; rendered
browser text is not a comparable representation. It performs no database write.
"""

import ipaddress
import math
import ssl
import time
from dataclasses import dataclass
from typing import Annotated, Literal, Self
from urllib.parse import urlsplit

import httpcore
from pydantic import Field, model_validator

from batchbeacon.contracts import Nonempty, Record


class SourceFetchPolicy(Record):
    policy_version: Literal["bounded-source-fetch-1"] = "bounded-source-fetch-1"
    url: Nonempty
    allowed_hosts: tuple[Nonempty, ...] = Field(min_length=1)
    public_addresses: tuple[Nonempty, ...] = Field(min_length=1)
    network_seconds: Annotated[float, Field(gt=0, allow_inf_nan=False)] = 20.0
    max_body_bytes: Annotated[int, Field(gt=0)] = 2097152
    max_wire_bytes: Annotated[int, Field(gt=0)] = 4194304
    read_chunk_bytes: Annotated[int, Field(gt=0)] = 65536
    max_attempts: Annotated[int, Field(ge=1, le=2)] = 1
    retry_delay_seconds: Annotated[float, Field(ge=0, allow_inf_nan=False)] = 0.0
    content_types: tuple[Nonempty, ...] = ("text/html", "text/plain", "application/pdf")

    @model_validator(mode="after")
    def bounded(self) -> Self:
        try:
            self.url.encode("ascii")
        except UnicodeEncodeError as error:
            raise ValueError("source_url_ascii_required") from error
        parsed = urlsplit(self.url)
        if (
            any(ord(c) < 32 or ord(c) == 127 for c in self.url)
            or parsed.scheme != "https"
            or parsed.hostname not in self.allowed_hosts
            or parsed.port not in (None, 443)
            or parsed.username is not None
            or parsed.password is not None
            or parsed.fragment
        ):
            raise ValueError("source_url_not_allowlisted")
        try:
            ipaddress.ip_address(parsed.hostname)
        except ValueError:
            pass
        else:
            raise ValueError("authority_hostname_required")
        if any(
            "%" in address
            or not ipaddress.ip_address(address).is_global
            or ipaddress.ip_address(address).is_multicast
            or ipaddress.ip_address(address).is_reserved
            for address in self.public_addresses
        ):
            raise ValueError("source_private_peer_refused")
        if (
            self.max_body_bytes > self.max_wire_bytes
            or self.read_chunk_bytes > self.max_wire_bytes
            or self.retry_delay_seconds * (self.max_attempts - 1) >= self.network_seconds
        ):
            raise ValueError("source_fetch_policy_bounds")
        return self


class SourceFetchRefused(ValueError):
    """Permanent refusal; never follows a redirect or retries a forbidden target."""


class _Stream(httpcore.NetworkStream):
    def __init__(self, stream, owner):
        self.stream, self.owner = stream, owner

    def read(self, max_bytes, timeout=None):
        left = self.owner.policy.max_wire_bytes - self.owner.received
        if left <= 0:
            raise SourceFetchRefused("source_wire_limit")
        raw = self.stream.read(
            min(max_bytes, left, self.owner.policy.read_chunk_bytes), timeout=self.owner.remaining()
        )
        self.owner.received += len(raw)
        self.owner.remaining()
        return raw

    def write(self, buffer, timeout=None):
        sock = self.stream.get_extra_info("socket")
        if sock is None:
            raise SourceFetchRefused("source_socket_unavailable")
        sock.settimeout(self.owner.remaining())
        # Python sendall applies one total timeout across partial writes.
        sock.sendall(buffer)
        self.owner.remaining()

    def close(self):
        self.stream.close()

    def start_tls(self, ssl_context, server_hostname=None, timeout=None):
        if (
            server_hostname != self.owner.host
            or not ssl_context.check_hostname
            or ssl_context.verify_mode != ssl.CERT_REQUIRED
        ):
            raise SourceFetchRefused("source_tls_identity_required")
        wrapped = self.stream.start_tls(
            ssl_context, server_hostname=server_hostname, timeout=self.owner.remaining()
        )
        self.owner.remaining()
        return _Stream(wrapped, self.owner)

    def get_extra_info(self, info):
        return self.stream.get_extra_info(info)


class _PinnedBackend(httpcore.NetworkBackend):
    def __init__(self, policy, address, deadline, monotonic):
        self.policy, self.address, self.deadline = policy, address, deadline
        self.monotonic, self.received = monotonic, 0
        self.host = urlsplit(policy.url).hostname

    def remaining(self):
        value = self.deadline - self.monotonic()
        if value <= 0:
            raise TimeoutError("source_fetch_deadline")
        return value

    def connect_tcp(self, host, port, timeout=None, local_address=None, socket_options=None):
        if host != self.host or port != 443 or local_address is not None:
            raise SourceFetchRefused("source_connection_target_changed")
        # A literal public peer avoids a second, potentially rebinding DNS lookup.
        stream = httpcore.SyncBackend().connect_tcp(
            self.address, 443, timeout=self.remaining(), socket_options=socket_options
        )
        peer = stream.get_extra_info("server_addr")
        if peer is None or ipaddress.ip_address(peer[0]) != ipaddress.ip_address(self.address):
            stream.close()
            raise SourceFetchRefused("source_peer_changed")
        return _Stream(stream, self)


@dataclass(frozen=True)
class FetchedSource:
    raw: bytes
    attempts: int


def fetch_source(
    policy: SourceFetchPolicy, *, horizon_seconds=None, monotonic=time.monotonic, sleeper=time.sleep
) -> FetchedSource:
    """No redirect/proxy/SDK retry. Explicit retries share one absolute deadline."""
    if horizon_seconds is not None and (
        type(horizon_seconds) not in (int, float) or not math.isfinite(horizon_seconds)
    ):
        raise ValueError("source_fetch_horizon_invalid")
    horizon = (
        policy.network_seconds
        if horizon_seconds is None
        else min(policy.network_seconds, horizon_seconds)
    )
    if horizon <= 0:
        raise TimeoutError("source_fetch_deadline")
    deadline = monotonic() + horizon
    for attempt in range(policy.max_attempts):
        backend = _PinnedBackend(
            policy,
            policy.public_addresses[attempt % len(policy.public_addresses)],
            deadline,
            monotonic,
        )
        try:
            # A single logical request has one active connection and no keepalive.
            with httpcore.ConnectionPool(
                ssl_context=ssl.create_default_context(),
                max_connections=1,
                max_keepalive_connections=0,
                retries=0,
                network_backend=backend,
            ) as pool:
                with pool.stream(
                    "GET",
                    policy.url,
                    headers={"Accept-Encoding": "identity"},
                    extensions={
                        "timeout": {
                            k: backend.remaining() for k in ("connect", "read", "write", "pool")
                        }
                    },
                ) as response:
                    if response.status != 200:
                        raise SourceFetchRefused("source_http_status_refused")
                    headers = [(k.lower(), v) for k, v in response.headers]
                    encoding = [v for k, v in headers if k == b"content-encoding"]
                    types = [
                        v.split(b";", 1)[0].strip().decode("ascii")
                        for k, v in headers
                        if k == b"content-type"
                    ]
                    if (
                        encoding not in ([], [b"identity"])
                        or len(types) != 1
                        or types[0] not in policy.content_types
                    ):
                        raise SourceFetchRefused("source_response_format_refused")
                    body = bytearray()
                    for chunk in response.iter_stream():
                        backend.remaining()
                        body.extend(chunk)
                        if len(body) > policy.max_body_bytes:
                            raise SourceFetchRefused("source_body_limit")
                    backend.remaining()
                    if not body:
                        raise SourceFetchRefused("source_empty_body")
                    return FetchedSource(bytes(body), attempt + 1)
        except SourceFetchRefused:
            raise
        except (httpcore.NetworkError, httpcore.TimeoutException, OSError):
            if attempt + 1 == policy.max_attempts:
                raise
            remaining = deadline - monotonic()
            if remaining <= policy.retry_delay_seconds:
                raise TimeoutError("source_fetch_deadline") from None
            sleeper(policy.retry_delay_seconds)
    raise AssertionError("bounded_source_attempts_exhausted")
