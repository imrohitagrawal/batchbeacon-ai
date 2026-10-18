"""Cited notice context for preview/reporting, separate from matching predicates.

Draft context cannot create an AuthorityNotice or authorize an action. Missing
extraction is UNKNOWN; NOT_STATED requires review of the bound notice itself.
"""

from datetime import date
from typing import Literal
from urllib.parse import urlsplit

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


class RelatedDocument(Record):
    title: Nonempty
    url: Nonempty
    kind: Literal["COMPANY_CUSTOMER_NOTICE"]
    format: Literal["PDF"]
    locator: Nonempty
    link_observed_on: date
    link_basis: Literal["OBSERVED_ON_PARENT_PAGE"]
    # This observes a link, not the attachment's bytes, contents or reuse rights.
    contents_reviewed: Literal[False]

    @model_validator(mode="after")
    def external_url(self):
        url = urlsplit(self.url)
        if url.scheme != "https" or not url.hostname or url.username or url.password \
                or any(c.isspace() for c in self.url):
            raise ValueError("Related documents require a public HTTPS link")
        return self


class RelatedDocuments(Record):
    state: Literal["PRESENT", "NONE_STATED", "UNKNOWN"]
    documents: tuple[RelatedDocument, ...]
    locator: Nonempty

    @model_validator(mode="after")
    def coherent(self):
        if (self.state == "PRESENT") != bool(self.documents) \
                or len({d.url for d in self.documents}) != len(self.documents):
            raise ValueError("Document presence and distinct links must agree")
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
    related_documents: RelatedDocuments
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
