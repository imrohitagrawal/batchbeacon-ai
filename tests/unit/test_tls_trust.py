"""Installed HTTPS consumers must not trust the root removed by GHSA-6q48-6c7w-9gw2."""

import asyncio
import ssl
from hashlib import sha256

import certifi
import httpx
import requests
from google.auth.credentials import AnonymousCredentials
from google.cloud import storage

# Stable fingerprint of the revoked-chain trust anchor, not operational policy.
COMPROMISED_ROOT = "86a1ecba089c4a8d3bbe2734c612ba341d813e043cf9e8a862cd5c57a36bbe6b"


def assert_trust(context):
    assert context.verify_mode == ssl.CERT_REQUIRED and context.check_hostname
    roots = {sha256(der).hexdigest() for der in context.get_ca_certs(binary_form=True)}
    assert roots and COMPROMISED_ROOT not in roots


def test_model_http_transport_excludes_compromised_anchor(monkeypatch):
    monkeypatch.delenv("SSL_CERT_FILE", raising=False)
    monkeypatch.delenv("SSL_CERT_DIR", raising=False)
    # The actual installed transport used by model_runtime when no test transport is injected.
    transport = httpx.AsyncHTTPTransport(retries=0)
    try:
        assert_trust(transport._pool._ssl_context)
    finally:
        asyncio.run(transport.aclose())


def test_storage_requests_uses_verified_patched_bundle(monkeypatch):
    monkeypatch.setenv("DISABLE_GCS_PYTHON_CLIENT_OTEL_BUCKET_METADATA", "true")
    client = storage.Client(project="synthetic-project", credentials=AnonymousCredentials())
    try:
        assert client._http.verify is True
        assert requests.adapters.DEFAULT_CA_BUNDLE_PATH == certifi.where()
        assert_trust(ssl.create_default_context(cafile=requests.adapters.DEFAULT_CA_BUNDLE_PATH))
    finally:
        client.close()
