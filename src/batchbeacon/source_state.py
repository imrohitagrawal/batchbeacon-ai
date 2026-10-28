"""Compatible source-state reader contracts. No fetch, writer or trust promotion.

Selection is anchored in owned evidence and its atomic retail derivative. The
trusted registry is required whenever its admission is configured; absence is
never permission to recover an earlier historical result.
"""

from datetime import datetime
from typing import Annotated, Literal, Self

from pydantic import AwareDatetime, Field, model_validator

from batchbeacon.contracts import (
    AuthorityNotice,
    Digest,
    LiveStatus,
    Nonempty,
    Record,
    Revision,
    SourceMode,
    VerificationContext,
    VerifierPolicy,
)
from batchbeacon.source_update import ReviewOnlySourceUpdate


def changed(record, **updates):
    return type(record).model_validate(record.model_dump() | updates)


class EvidenceEnvironment(Record):
    context: VerificationContext
    notices: tuple[AuthorityNotice, ...]
    verifier_policy: VerifierPolicy
    source_valid_until: AwareDatetime | None = Field(
        default=None, exclude_if=lambda value: value is None
    )

    def at(self, now: datetime, result_revision: int) -> VerificationContext:
        context = self.context
        if self.source_valid_until is not None and now >= self.source_valid_until:
            context = changed(context, live_status=LiveStatus.EXPIRED)
        return changed(context, computed_at=now, result_revision=result_revision)


class SelectionReceipt(Record):
    key: Annotated[str, Field(pattern=r"^[A-Za-z0-9_-]{1,80}$")]
    payload_hash: Digest
    revision: Revision


class SourceSelection(Record):
    version: Literal["incident-source-1"] = "incident-source-1"
    catalog_hash: Digest
    choice: Nonempty
    environment_hash: Digest
    revision: Revision
    selected_at: AwareDatetime
    receipts: tuple[SelectionReceipt, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def history(self) -> Self:
        if len({r.key for r in self.receipts}) != len(self.receipts) or any(
            r.revision > self.revision for r in self.receipts
        ):
            raise ValueError("invalid_source_selection_receipts")
        if {r.revision for r in self.receipts} != set(range(1, self.revision + 1)):
            raise ValueError("source_selection_history_required")
        return self


class SourceChoice(Record):
    key: Nonempty
    environment: EvidenceEnvironment


class SourceCatalog(Record):
    version: Literal["source-catalog-1"] = "source-catalog-1"
    default_choice: Nonempty
    choices: tuple[SourceChoice, ...] = Field(min_length=1)
    update: ReviewOnlySourceUpdate | None = None
    original_choice: Nonempty | None = None
    update_choice: Nonempty | None = None

    @model_validator(mode="after")
    def bound(self) -> Self:
        choices = {c.key: c.environment for c in self.choices}
        if len(choices) != len(self.choices) or self.default_choice not in choices:
            raise ValueError("invalid_source_catalog_choices")
        for env in choices.values():
            if env.source_valid_until is not None:
                raise ValueError("catalog_cannot_supply_refresh_validity")
            if (
                not env.notices
                or tuple(n.dependency for n in env.notices) != env.context.current_sources
            ):
                raise ValueError("source_catalog_dependency_mismatch")
        if self.update is None:
            if self.original_choice is not None or self.update_choice is not None:
                raise ValueError("source_update_receipt_required")
        else:
            if self.original_choice == self.update_choice:
                raise ValueError("distinct_source_choices_required")
            for key, version in (
                (self.original_choice, self.update.original),
                (self.update_choice, self.update.update),
            ):
                env = choices.get(key)
                if env is None or len(env.notices) != 1:
                    raise ValueError("source_update_choice_missing")
                notice = env.notices[0]
                if (
                    notice.dependency.family,
                    notice.dependency.version,
                    notice.dependency.content_hash,
                    notice.published_at,
                    notice.jurisdictions,
                ) != (
                    version.family,
                    version.version,
                    version.content_hash,
                    version.published_at,
                    version.jurisdictions,
                ):
                    raise ValueError("source_update_choice_unbound")
                if notice.review is not None or notice.interpretation_complete:
                    raise ValueError("pending_UK_update_must_remain_review_only")
        return self

    def environment(self, selection):
        key = self.default_choice if selection is None else selection.choice
        env = next((c.environment for c in self.choices if c.key == key), None)
        if (
            env is None
            or selection is not None
            and (
                selection.catalog_hash != self.digest()
                or selection.environment_hash != env.digest()
            )
        ):
            raise ValueError("source_selection_not_admitted")
        return env


class FamilyRefresh(Record):
    family: Nonempty
    epoch: Revision
    status: Literal["NEVER_REQUESTED", "UNCHANGED", "CHANGED", "UNAVAILABLE"]
    observed_hash: Digest | None = None
    checked_at: AwareDatetime | None = None
    valid_until: AwareDatetime | None = None

    @model_validator(mode="after")
    def coherent(self) -> Self:
        if self.status == "NEVER_REQUESTED":
            if any(v is not None for v in (self.observed_hash, self.checked_at, self.valid_until)):
                raise ValueError("unrequested_refresh_has_no_observation")
        elif (
            self.checked_at is None
            or self.valid_until is None
            or self.valid_until <= self.checked_at
        ):
            raise ValueError("finite_source_refresh_validity_required")
        if (self.status in {"UNCHANGED", "CHANGED"}) != (self.observed_hash is not None):
            raise ValueError("source_refresh_hash_required")
        return self


class SourceRegistry(Record):
    version: Literal["trusted-source-registry-1"] = "trusted-source-registry-1"
    catalog: SourceCatalog
    families: tuple[FamilyRefresh, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def complete(self) -> Self:
        families = {f.family: f for f in self.families}
        deps = tuple(n.dependency for c in self.catalog.choices for n in c.environment.notices)
        if len(families) != len(self.families) or set(families) != {d.family for d in deps}:
            raise ValueError("source_registry_coverage_mismatch")
        if any(families[d.family].epoch < d.epoch for d in deps):
            raise ValueError("source_registry_epoch_precedes_catalog")
        return self

    def resolve(self, selection, now):
        env = self.catalog.environment(selection)
        if selection is not None and selection.selected_at > now:
            raise ValueError("source_selection_in_future")
        current = {f.family: f for f in self.families}
        notices, deps, attempted = [], [], []
        for notice in env.notices:
            state = current[notice.dependency.family]
            deps.append(changed(notice.dependency, epoch=state.epoch))
            if state.status != "NEVER_REQUESTED":
                if state.checked_at > now:
                    raise ValueError("source_refresh_in_future")
                attempted.append(state)
            available = state.status == "NEVER_REQUESTED" or (
                state.status == "UNCHANGED"
                and state.observed_hash == notice.dependency.content_hash
                and now < state.valid_until
            )
            notices.append(changed(notice, source_available=notice.source_available and available))
        context = changed(env.context, current_sources=tuple(deps))
        if attempted:
            failed = any(
                s.status != "UNCHANGED" or s.observed_hash != n.dependency.content_hash
                for n in env.notices
                for s in attempted
                if s.family == n.dependency.family
            )
            expired = any(now >= s.valid_until for s in attempted)
            context = changed(
                context,
                mode=SourceMode.LIVE,
                historical_selected_at=None,
                live_status=LiveStatus.EXPIRED
                if expired
                else LiveStatus.FAILED
                if failed
                else LiveStatus.VALIDATED,
                live_validated_at=min(s.checked_at for s in attempted),
            )
        return changed(
            env,
            context=context,
            notices=tuple(notices),
            source_valid_until=min(s.valid_until for s in attempted) if attempted else None,
        )


class SourceRuntimeAdmission(Record):
    version: Literal["source-runtime-admission-1"] = "source-runtime-admission-1"
    catalog_hash: Digest
    # This is a persistence admission, not guest authority or network permission.
    registry_required: Literal[True] = True
    replay_enabled: bool = False
    max_selection_receipts: Annotated[int, Field(gt=0)] = 40


class SourceRefreshIntent(Record):
    """Trusted operation journal; a guest cannot create or publish it."""

    version: Literal["trusted-source-refresh-1"] = "trusted-source-refresh-1"
    key_hash: Digest
    policy_hash: Digest
    catalog_hash: Digest
    family: Nonempty
    previous: FamilyRefresh
    started_at: AwareDatetime
    deadline: AwareDatetime
    result: FamilyRefresh | None = None
    reason: Literal["UNCHANGED", "CHANGED", "UNAVAILABLE"] | None = None

    @model_validator(mode="after")
    def bound(self) -> Self:
        if self.previous.family != self.family or self.deadline <= self.started_at:
            raise ValueError("source_refresh_intent_binding_failed")
        if (self.result is None) != (self.reason is None):
            raise ValueError("source_refresh_publication_incomplete")
        if self.result is not None and (
            self.result.family != self.family
            or self.result.epoch < self.previous.epoch
            or self.result.status != self.reason
            or self.result.checked_at is None
            or not self.started_at <= self.result.checked_at < self.deadline
            or self.result.epoch > self.previous.epoch + 1
        ):
            raise ValueError("source_refresh_result_binding_failed")
        return self
