"""Hash-bound review-only source-update preparation, outside database transactions.

This implements no fetch, guest replay, epoch mutation or trust promotion. Its
caller supplies operator-selected metadata and retained captures. A valid receipt
proves lineage, not predicate interpretation or permission to use a new notice.
"""

from datetime import date
from hashlib import sha256
from typing import Annotated, Literal, Self

from pydantic import Field, model_validator

from batchbeacon.contracts import Digest, Nonempty, Record

UKTerritory = Literal["GB-ENG", "GB-NIR", "GB-WLS", "GB-SCT"]


class SourceVersion(Record):
    family: Nonempty
    version: Nonempty
    content_hash: Digest
    published_at: date
    supersedes: Nonempty | None
    jurisdictions: tuple[UKTerritory, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def distinct_scope(self) -> Self:
        if len(set(self.jurisdictions)) != len(self.jurisdictions):
            raise ValueError("source_update_duplicate_territory")
        if self.supersedes == self.version:
            raise ValueError("source_update_self_supersedes")
        return self


class SourceUpdatePolicy(Record):
    version: Literal["review-only-source-update-1"] = "review-only-source-update-1"
    original: SourceVersion
    update: SourceVersion
    max_capture_bytes: Annotated[int, Field(gt=0)] = 2 * 1024 * 1024

    @model_validator(mode="after")
    def forward_pair(self) -> Self:
        a, b = self.original, self.update
        if a.family != b.family or b.supersedes != a.version or a.version == b.version \
                or a.supersedes == b.version or a.content_hash == b.content_hash \
                or b.published_at < a.published_at:
            raise ValueError("source_update_forward_lineage_required")
        return self


class ReviewOnlySourceUpdate(Record):
    policy: SourceUpdatePolicy
    policy_hash: Digest
    original: SourceVersion
    update: SourceVersion
    added_jurisdictions: tuple[UKTerritory, ...]
    removed_jurisdictions: tuple[UKTerritory, ...]
    human_review: Literal["PENDING"] = "PENDING"
    activation_allowed: Literal[False] = False

    @model_validator(mode="after")
    def bound_receipt(self) -> Self:
        a, b = self.policy.original, self.policy.update
        if self.policy_hash != self.policy.digest() or self.original != a or self.update != b \
                or self.added_jurisdictions != tuple(j for j in b.jurisdictions
                                                    if j not in a.jurisdictions) \
                or self.removed_jurisdictions != tuple(j for j in a.jurisdictions
                                                      if j not in b.jurisdictions):
            raise ValueError("source_update_receipt_binding_failed")
        return self


def prepare_source_update(original: bytes, update: bytes,
                          policy: SourceUpdatePolicy) -> ReviewOnlySourceUpdate:
    """Verify immutable original/update bytes; return a non-authorizing receipt."""
    for raw, version in ((original, policy.original), (update, policy.update)):
        if type(raw) is not bytes or not raw or len(raw) > policy.max_capture_bytes \
                or sha256(raw).hexdigest() != version.content_hash:
            raise ValueError("source_update_capture_binding_failed")
    return ReviewOnlySourceUpdate(
        policy=policy, policy_hash=policy.digest(), original=policy.original, update=policy.update,
        added_jurisdictions=tuple(j for j in policy.update.jurisdictions
                                 if j not in policy.original.jurisdictions),
        removed_jurisdictions=tuple(j for j in policy.original.jurisdictions
                                   if j not in policy.update.jurisdictions),
    )
