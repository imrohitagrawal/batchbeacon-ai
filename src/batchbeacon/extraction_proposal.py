"""Pure validation of UNTRUSTED model proposals, not extraction or publication.

Locations are structurally checked, not evidence of accurate visual reading.
The caller must retain the original response and later enforce owned inputs,
actual ADK provenance, source currentness and paid admission before publication.
"""

import json
import re
from datetime import date
from hashlib import sha256
from typing import Annotated, Literal, Self

from pydantic import Field, model_validator

from batchbeacon.contracts import (
    AuthorityNotice,
    DateRange,
    Digest,
    EvidenceKind,
    EvidenceRef,
    IdentifierKind,
    Nonempty,
    ObservedIdentifier,
    ObservedPredicate,
    ObservedValue,
    Operator,
    PredicateField,
    PredicateRule,
    Record,
    SourceDependency,
    ValueState,
    ValueType,
)
from batchbeacon.evidence_service import ExtractedIdentity, ExtractedValues

Positive = Annotated[int, Field(gt=0)]
Index = Annotated[int, Field(ge=0)]
Coordinate = Annotated[float, Field(ge=0, le=1, allow_inf_nan=False)]
TRANSLATOR_VERSION = "proposal-translation-2"


class ProposalPolicy(Record):
    max_proposal_bytes: Positive = 32768
    max_source_bytes: Positive = 100000
    max_string_bytes: Positive = 4096
    max_collection_items: Positive = 32
    max_nesting: Positive = 16
    max_quote_bytes: Positive = 1024
    max_quote_occurrence: Index = 32
    # NF-01's two images per acquisition is a stable application ceiling.
    max_captures: Annotated[int, Field(ge=1, le=2)] = 2

    @model_validator(mode="after")
    def coherent(self) -> Self:
        if not self.max_quote_bytes <= self.max_string_bytes <= self.max_proposal_bytes:
            raise ValueError("quote/string bounds must fit the proposal")
        return self


class ProposalInvalid(ValueError):
    """Sanitized diagnostic only. No source, label or raw response in the error."""


class SourceLocation(Record):
    quote: Nonempty
    occurrence: Index


class CaptureLocation(Record):
    panel: Index
    box: tuple[Coordinate, Coordinate, Coordinate, Coordinate]

    @model_validator(mode="after")
    def nonempty_box(self) -> Self:
        left, top, right, bottom = self.box
        if left >= right or top >= bottom:
            raise ValueError("capture box must have positive area")
        return self


class ProposedValue(Record):
    raw: str
    state: ValueState
    value: str | None
    locations: tuple[CaptureLocation, ...]


class ProposedCode(Record):
    kind: Literal[IdentifierKind.PRODUCT_CODE, IdentifierKind.GTIN]
    observation: ProposedValue


class LabelProposal(Record):
    name: ProposedValue
    pack: ProposedValue
    identifiers: tuple[ProposedCode, ...]
    lot: ProposedValue
    best_before: ProposedValue
    use_by: ProposedValue


class SourceCode(Record):
    kind: Literal[IdentifierKind.PRODUCT_CODE, IdentifierKind.GTIN]
    value: Nonempty
    locations: tuple[SourceLocation, ...] = Field(min_length=1)


class SourcePredicate(Record):
    field: PredicateField
    operator: Operator
    value_type: ValueType
    values: tuple[Nonempty, ...]
    date_range: DateRange | None
    applies: bool
    applicability_reason: str | None
    locations: tuple[SourceLocation, ...] = Field(min_length=1)


class SourceProduct(Record):
    name: Nonempty
    pack: Nonempty | None
    identifiers: tuple[SourceCode, ...]
    locations: tuple[SourceLocation, ...] = Field(min_length=1)
    predicates: tuple[SourcePredicate, ...]


class SourceProposal(Record):
    jurisdictions: tuple[Nonempty, ...] = Field(min_length=1)
    locations: tuple[SourceLocation, ...] = Field(min_length=1)
    products: tuple[SourceProduct, ...] = Field(min_length=1)


class ExtractionProposal(Record):
    """No authority fields: IDs, hashes, review and provenance come from the server."""
    source: SourceProposal
    label: LabelProposal


class TranslationReport(Record):
    """Not a publish command. Consumers must retain and enforce the disposition."""
    translator_version: Literal["proposal-translation-2"] = TRANSLATOR_VERSION
    source_status: Literal["AGREES_WITH_REVIEW", "DISAGREES", "REVIEW_MISSING"]
    diagnostics: tuple[Nonempty, ...]
    proposal: ExtractionProposal
    label_values: ExtractedValues
    source_locations: tuple[EvidenceRef, ...]
    source_dependency: SourceDependency
    notice_digest: Digest
    captures: tuple[EvidenceRef, ...]
    proposal_hash: Digest
    schema_hash: Digest
    policy_hash: Digest

    @model_validator(mode="after")
    def coherent(self) -> Self:
        if (self.source_status == "AGREES_WITH_REVIEW") != (not self.diagnostics):
            raise ValueError("source disposition requires matching diagnostics")
        return self


def _unique(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ProposalInvalid("duplicate_json_key")
        value[key] = item
    return value


def _bounded(value, policy):
    pending = [(value, 0)]
    while pending:
        item, depth = pending.pop()
        if depth > policy.max_nesting:
            raise ProposalInvalid("proposal_nesting_limit")
        if isinstance(item, str) and len(item.encode()) > policy.max_string_bytes:
            raise ProposalInvalid("proposal_string_limit")
        if isinstance(item, (dict, list)):
            if len(item) > policy.max_collection_items:
                raise ProposalInvalid("proposal_collection_limit")
            if isinstance(item, dict):
                pending.extend((key, depth + 1) for key in item)
                item = item.values()
            pending.extend((child, depth + 1) for child in item)


def _source_ref(location, text, notice, policy):
    if not location.quote.strip() or len(location.quote.encode()) > policy.max_quote_bytes \
            or location.occurrence > policy.max_quote_occurrence:
        raise ProposalInvalid("source_location_limit")
    start = -1
    for _ in range(location.occurrence + 1):
        start = text.find(location.quote, start + 1)
        if start < 0:
            raise ProposalInvalid("source_quote_unavailable")
    return EvidenceRef(kind=EvidenceKind.SOURCE, artifact_id=notice.dependency.version,
        sha256=notice.dependency.content_hash,
        locator=f"characters:{start}:{start + len(location.quote)}")


def _date_value(raw):
    # Translator v1 admits only ISO and a unique interpretation of numeric slash
    # dates. No locale guessing, fuzzy parsing or model-selected disambiguation.
    if re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", raw):
        return date.fromisoformat(raw).isoformat()
    match = re.fullmatch(r"([0-9]{2})/([0-9]{2})/([0-9]{4})", raw)
    candidates = set()
    if match:
        first, second, year = map(int, match.groups())
        for month, day in ((first, second), (second, first)):
            try:
                candidates.add(date(year, month, day).isoformat())
            except ValueError:
                pass
    if len(candidates) != 1:
        raise ProposalInvalid("date_normalization_unavailable")
    return candidates.pop()


def _label_value(value, expected, captures):
    # Label field types are fixed protocol semantics, never an AI-selected value.
    refs = []
    for location in value.locations:
        if location.panel >= len(captures):
            raise ProposalInvalid("capture_panel_unavailable")
        ref = captures[location.panel]
        box = ",".join(format(x, ".17g") for x in location.box)
        refs.append(EvidenceRef(kind=EvidenceKind.CAPTURE, artifact_id=ref.artifact_id,
                               sha256=ref.sha256, locator=f"normalized_box:{box}"))
    translated = ObservedValue(raw=value.raw, state=value.state, value_type=expected,
                              value=value.value, evidence=tuple(refs))
    if value.state == ValueState.KNOWN:
        expected_value = _date_value(value.raw) if expected == ValueType.DATE else value.raw
        if value.value != expected_value:
            raise ProposalInvalid("value_normalization_forbidden")
    return translated


def _predicates(items):
    # Evidence locations are compared separately; order is not a restriction.
    values = []
    for item in items:
        data = item.model_dump(mode="json", exclude={"evidence"})
        data["values"] = sorted(data["values"])
        values.append(data)
    return sorted(values, key=lambda item: item["field"])


def _signature(name, pack, codes, predicates):
    # Exact extraction fidelity; do not silently normalize aliases or code types.
    return json.dumps({"name": name, "pack": pack,
        "codes": sorted((c.kind.value, c.value) for c in codes),
        "predicates": _predicates(predicates)}, sort_keys=True, separators=(",", ":"))


def translate_proposal(
    raw: bytes, *, source_bytes: bytes, notice: AuthorityNotice,
    captures: tuple[EvidenceRef, ...], policy: ProposalPolicy,
) -> TranslationReport:
    """Validate exact source bytes and report agreement; perform no I/O or publishing.

    Source bytes must be the exact UTF-8 representation identified by the notice
    content hash. Extracted/normalized source text needs separately established
    lineage and cannot be substituted here. Capture ownership/bytes are NOT proven.
    """
    try:
        if type(raw) is not bytes or not raw or len(raw) > policy.max_proposal_bytes:
            raise ProposalInvalid("proposal_byte_limit")
        if type(source_bytes) is not bytes or not source_bytes \
                or len(source_bytes) > policy.max_source_bytes \
                or sha256(source_bytes).hexdigest() != notice.dependency.content_hash:
            raise ProposalInvalid("source_bytes_unavailable")
        if type(captures) is not tuple or not 0 < len(captures) <= policy.max_captures \
                or any(r.kind != EvidenceKind.CAPTURE for r in captures) \
                or len({r.artifact_id for r in captures}) != len(captures):
            raise ProposalInvalid("capture_selection_invalid")
        text = source_bytes.decode("utf-8", errors="strict")
        parsed = json.loads(raw, object_pairs_hook=_unique)
        _bounded(parsed, policy)
        proposal = ExtractionProposal.model_validate_json(raw)
        label = proposal.label
        if len({c.kind for c in label.identifiers}) != len(label.identifiers):
            raise ProposalInvalid("duplicate_label_identifier_kind")
        values = ExtractedValues(identity=ExtractedIdentity(
            name=_label_value(label.name, ValueType.TEXT, captures),
            pack=_label_value(label.pack, ValueType.TEXT, captures),
            identifiers=tuple(ObservedIdentifier(kind=c.kind, observation=_label_value(
                c.observation, ValueType.TEXT, captures))
                for c in label.identifiers)),
            fields=tuple(ObservedPredicate(field=field, observation=_label_value(
                value, value_type, captures))
                for field, value, value_type in (
                    (PredicateField.LOT, label.lot, ValueType.TEXT),
                    (PredicateField.BEST_BEFORE, label.best_before, ValueType.DATE),
                    (PredicateField.USE_BY, label.use_by, ValueType.DATE))))
        source, locations, proposed = proposal.source, [], []

        def resolve(items):
            refs = tuple(_source_ref(item, text, notice, policy) for item in items)
            locations.extend(refs)
            return refs

        resolve(source.locations)
        if len(set(source.jurisdictions)) != len(source.jurisdictions):
            raise ProposalInvalid("duplicate_jurisdiction")
        for product in source.products:
            resolve(product.locations)
            for code in product.identifiers:
                resolve(code.locations)
            if len({c.kind for c in product.identifiers}) != len(product.identifiers) \
                    or len({p.field for p in product.predicates}) != len(product.predicates):
                raise ProposalInvalid("duplicate_source_field")
            rules = tuple(PredicateRule(**p.model_dump(exclude={"locations"}),
                          evidence=resolve(p.locations)) for p in product.predicates)
            proposed.append(_signature(product.name, product.pack, product.identifiers, rules))
        if len(set(proposed)) != len(proposed):
            raise ProposalInvalid("duplicate_source_product")
        expected = [_signature(p.identity.canonical_name, p.identity.pack,
                               p.identity.identifiers, p.predicates) for p in notice.products]
        diagnostics = []
        if sorted(source.jurisdictions) != sorted(notice.jurisdictions):
            diagnostics.append("SOURCE_JURISDICTIONS_DIFFER")
        if sorted(proposed) != sorted(expected):
            diagnostics.append("SOURCE_PRODUCTS_OR_RESTRICTIONS_DIFFER")
        reviewed = notice.review is not None and notice.interpretation_complete
        if not reviewed:
            diagnostics.append("SOURCE_REVIEW_REQUIRED")
        status = "REVIEW_MISSING" if not reviewed else "DISAGREES" if diagnostics \
            else "AGREES_WITH_REVIEW"
        schema = json.dumps(ExtractionProposal.model_json_schema(), sort_keys=True,
                            separators=(",", ":")).encode()
        return TranslationReport(source_status=status, diagnostics=tuple(diagnostics),
            proposal=proposal, label_values=values, source_locations=tuple(locations),
            source_dependency=notice.dependency, notice_digest=notice.digest(), captures=captures,
            proposal_hash=sha256(raw).hexdigest(), schema_hash=sha256(schema).hexdigest(),
            policy_hash=policy.digest())
    except ProposalInvalid:
        raise
    except (ValueError, TypeError, KeyError, AttributeError, OverflowError, RecursionError):
        # Validation exceptions can embed rejected source/label text. Exit the
        # handler before raising so standard tracebacks retain neither cause nor
        # context. Original output retention belongs to the private caller.
        pass
    raise ProposalInvalid("proposal_schema_or_input_invalid")
