"""Cited notice context for preview/reporting, separate from matching predicates.

Draft context cannot create an AuthorityNotice or authorize an action. Missing
extraction is UNKNOWN; NOT_STATED requires review of the bound notice itself.
"""

from typing import Literal

from pydantic import Field, model_validator

from batchbeacon.contracts import Digest, Nonempty, Record


class ContextFact(Record):
    state: Literal["STATED", "NOT_STATED", "UNKNOWN"]
    text: Nonempty | None
    locator: Nonempty

    @model_validator(mode="after")
    def stated_text(self):
        if (self.state == "STATED") != (self.text is not None):
            raise ValueError("Only STATED facts carry source-derived text")
        return self


class RecallContext(Record):
    source_id: Nonempty
    source_url: Nonempty
    capture_sha256: Digest
    citation_label: Nonempty
    human_review: Literal["PENDING"]
    reason: ContextFact
    basis: ContextFact
    health_risks: ContextFact
    affected_products: ContextFact
    total_quantity: ContextFact
    businesses: ContextFact
    company_action: ContextFact
    regulatory_action: ContextFact
    legal_action: ContextFact
    consumer_advice: ContextFact
    geography: ContextFact
    attribution: Nonempty


class ContextManifest(Record):
    version: Literal["recall-context-draft-1"]
    status: Literal["HUMAN_REVIEW_PENDING"]
    notices: tuple[RecallContext, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def distinct_versions(self):
        ids = [notice.source_id for notice in self.notices]
        if len(ids) != len(set(ids)):
            raise ValueError("Notice context must have distinct source version IDs")
        return self
