"""Operator-only refresh coordination. Never mounted on the public application.

A source attempt blocks historical eligibility before external I/O. The durable
per-family journal owner and retained hash survive failure, overlap and expiry.
No model or network operation occurs in a retryable transaction callback.
"""

from datetime import UTC, datetime, timedelta
from hashlib import sha256
from typing import Annotated, Literal, Self

import httpcore
from pydantic import AwareDatetime, Field, TypeAdapter, model_validator

from batchbeacon.contracts import Digest, Nonempty, Record
from batchbeacon.evidence_service import canonical, replace
from batchbeacon.guest_service import RequestKey
from batchbeacon.source_fetch import SourceFetchPolicy, fetch_source
from batchbeacon.source_state import FamilyRefresh, SourceRefreshIntent


class TrustedRefreshPolicy(Record):
    policy_version: Literal["trusted-source-refresh-policy-1"] = "trusted-source-refresh-policy-1"
    family: Nonempty
    version: Nonempty
    expected_hash: Digest
    catalog_hash: Digest
    fetch: SourceFetchPolicy
    operation_seconds: Annotated[float, Field(gt=0, allow_inf_nan=False)] = 90.0
    freshness_seconds: Annotated[int, Field(gt=0)] = 86400
    not_before: AwareDatetime
    expires_at: AwareDatetime

    @model_validator(mode="after")
    def finite(self) -> Self:
        if (
            self.expires_at <= self.not_before
            or self.operation_seconds <= self.fetch.network_seconds
        ):
            raise ValueError("trusted_refresh_policy_horizon")
        return self


class RefreshDenied(ValueError):
    pass


class TrustedRefresh:
    def __init__(
        self,
        stores,
        policy: TrustedRefreshPolicy,
        *,
        fetcher=fetch_source,
        clock=lambda: datetime.now(UTC),
    ):
        if (
            stores.source_runtime is None
            or stores.source_runtime.catalog_hash != policy.catalog_hash
        ):
            raise ValueError("trusted_refresh_requires_admitted_registry")
        if (
            policy.operation_seconds
            < policy.fetch.network_seconds + 3 * stores.policy.operation_seconds
        ):
            raise ValueError("complete_refresh_operation_horizon_required")
        self.store, self.policy, self.fetcher, self.clock = stores, policy, fetcher, clock

    def _active(self, horizon=0):
        now = self.clock()
        if (
            not self.policy.not_before <= now
            or now + timedelta(seconds=horizon) >= self.policy.expires_at
        ):
            raise RefreshDenied("trusted_refresh_admission_expired")
        return now

    def _registry(self, tx):
        registry = self.store.source_registry(tx)
        matches = [
            c.environment
            for c in registry.catalog.choices
            if c.capture_kind == "RAW_HTTP_BODY"
            for n in c.environment.notices
            if (n.dependency.family, n.dependency.version, n.dependency.content_hash, n.final_url)
            == (
                self.policy.family,
                self.policy.version,
                self.policy.expected_hash,
                self.policy.fetch.url,
            )
        ]
        if not matches:
            raise RefreshDenied("comparable_raw_authority_capture_required")
        if any(
            self.policy.freshness_seconds > e.verifier_policy.live_freshness_seconds
            for e in matches
        ):
            raise RefreshDenied("source_refresh_freshness_exceeds_verifier")
        return registry

    def _name(self, key):
        TypeAdapter(RequestKey).validate_python(key)
        return self.store.name("source_refresh", canonical({"request_key": key}))

    def _check_intent(self, intent, key):
        if intent is not None and (
            intent.key_hash,
            intent.policy_hash,
            intent.catalog_hash,
            intent.family,
        ) != (
            canonical({"request_key": key}),
            self.policy.digest(),
            self.policy.catalog_hash,
            self.policy.family,
        ):
            raise RefreshDenied("source_refresh_request_conflict")

    def reconcile(self, key):
        def read(tx):
            name = self._name(key)
            intent = tx.read({name: "source_refresh"})[name]
            self._check_intent(intent, key)
            return intent

        return self.store.run(read)

    def _pending(self, intent):
        previous = intent.previous
        baseline = previous.last_known_hash or previous.observed_hash
        if baseline is None:
            if previous.status != "NEVER_REQUESTED":
                raise RefreshDenied("source_refresh_baseline_unavailable")
            baseline = self.policy.expected_hash
        return FamilyRefresh(
            family=previous.family,
            epoch=previous.epoch,
            status="UNAVAILABLE",
            last_known_hash=baseline,
            pending_refresh=intent.key_hash,
            checked_at=intent.started_at,
            valid_until=intent.deadline,
        )

    def begin(self, key):
        now = self._active(self.policy.operation_seconds)
        created = []

        def begin(tx):
            registry = self._registry(tx)
            name = self._name(key)
            prior = tx.read({name: "source_refresh"})[name]
            self._check_intent(prior, key)
            if prior is not None:
                created[:] = [False]
                return prior
            state = next(f for f in registry.families if f.family == self.policy.family)
            if state.pending_refresh is not None:
                old_name = self.store.name("source_refresh", state.pending_refresh)
                old = tx.read({old_name: "source_refresh"})[old_name]
                if (
                    old is None
                    or old.key_hash != state.pending_refresh
                    or old.family != state.family
                    or old.result is not None
                    or old.deadline != state.valid_until
                    or old.started_at != state.checked_at
                    or old.catalog_hash != registry.catalog.digest()
                    or state != self._pending(old)
                    or self.clock() < old.deadline
                ):
                    raise RefreshDenied("source_refresh_pending")
                # Expired pending work is not repeated; its baseline is preserved.
            intent = SourceRefreshIntent(
                key_hash=canonical({"request_key": key}),
                policy_hash=self.policy.digest(),
                catalog_hash=self.policy.catalog_hash,
                family=self.policy.family,
                previous=state,
                started_at=now,
                deadline=now + timedelta(seconds=self.policy.operation_seconds),
            )
            pending = self._pending(intent)
            updated = replace(
                registry,
                families=tuple(
                    pending if f.family == pending.family else f for f in registry.families
                ),
            )
            tx.limit_to(intent.deadline)
            tx.write(name, "source_refresh", intent, create=True)
            tx.write(self.store.name("source_registry"), "source_registry", updated)
            created[:] = [True]
            return intent

        intent = self.store.run(begin)
        return intent, created[0]

    def publish(self, key, observed_hash):
        now = self._active()

        def publish(tx):
            registry = self._registry(tx)
            name = self._name(key)
            intent = tx.read({name: "source_refresh"})[name]
            self._check_intent(intent, key)
            if intent is None:
                raise RefreshDenied("source_refresh_intent_required")
            if intent.result is not None:
                return intent
            if not intent.started_at <= self.clock() < intent.deadline:
                raise RefreshDenied("source_refresh_deadline_elapsed")
            pending = self._pending(intent)
            current = next(f for f in registry.families if f.family == self.policy.family)
            if current != pending:
                raise RefreshDenied("source_refresh_owner_changed")
            baseline = pending.last_known_hash
            status = (
                "UNAVAILABLE"
                if observed_hash is None
                else "UNCHANGED"
                if observed_hash == self.policy.expected_hash
                else "CHANGED"
            )
            epoch = pending.epoch + int(observed_hash is not None and observed_hash != baseline)
            result = FamilyRefresh(
                family=current.family,
                epoch=epoch,
                status=status,
                observed_hash=observed_hash,
                last_known_hash=observed_hash or baseline,
                checked_at=now,
                valid_until=now + timedelta(seconds=self.policy.freshness_seconds),
            )
            done = replace(intent, result=result, reason=status)
            updated = replace(
                registry,
                families=tuple(
                    result if f.family == result.family else f for f in registry.families
                ),
            )
            tx.limit_to(intent.deadline)
            tx.write(name, "source_refresh", done)
            tx.write(self.store.name("source_registry"), "source_registry", updated)
            return done

        return self.store.run(publish)

    def execute(self, key):
        intent, created = self.begin(key)
        if not created:
            # This is reconciliation, not permission to repeat an uncertain fetch.
            return intent
        try:
            result = self.fetcher(
                self.policy.fetch, horizon_seconds=(intent.deadline - self.clock()).total_seconds()
            )
            observed = sha256(result.raw).hexdigest()
        except (
            OSError,
            ValueError,
            httpcore.NetworkError,
            httpcore.TimeoutException,
            httpcore.RemoteProtocolError,
        ):
            observed = None
        return self.publish(key, observed)
