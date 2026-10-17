"""Reviewed SFA facts with manually constructed observations, never model evidence."""

import json
from datetime import UTC, date, datetime
from pathlib import Path

from batchbeacon.contracts import (
    AffectedProductRule,
    AuthorityNotice,
    EvidenceKind,
    EvidenceRef,
    HumanReview,
    IdentityRule,
    ObservedPredicate,
    ObservedValue,
    Operator,
    PredicateField,
    PredicateRule,
    ProductIdentity,
    ProductObservation,
    SourceDependency,
    SourceMode,
    ValueState,
    ValueType,
    VerificationContext,
)

NOW = datetime(2026, 10, 18, 1, tzinfo=UTC)


def revise(record, **updates):
    return type(record).model_validate(record.model_dump() | updates)


def source_ref(version="sfa-cheese-2026-10-09", digest=None):
    if digest is None:
        digest = json.loads(Path("fixtures/sources/sfa-reviewed.json").read_text())["source"][
            "capture_sha256"
        ]
    return EvidenceRef(kind=EvidenceKind.SOURCE, artifact_id=version, sha256=digest,
                       locator="notice product table")


def capture_ref(name=None):
    fixtures = json.loads(Path("fixtures/synthetic/manifest.json").read_text())["fixtures"]
    fixture = next((row for row in fixtures if row["identity"] == name), fixtures[0])
    return EvidenceRef(kind=EvidenceKind.CAPTURE, artifact_id=Path(fixture["path"]).stem,
                       sha256=fixture["sha256"], locator="label full image")


def known(value, value_type=ValueType.TEXT, *, evidence=None):
    return ObservedValue(raw=value, state=ValueState.KNOWN, value=value,
                         value_type=value_type, evidence=(evidence or capture_ref(),))


def unknown(ambiguous=False, value_type=ValueType.TEXT):
    return ObservedValue(raw="unreadable", state=ValueState.AMBIGUOUS if ambiguous
                         else ValueState.UNKNOWN, value_type=value_type)


def notice():
    document = json.loads(Path("fixtures/sources/sfa-reviewed.json").read_text())
    source = document["source"]
    assert source["human_review"] == "APPROVED"
    review = document["human_review"]
    products = []
    for index, product in enumerate(source["products"]):
        products.append(AffectedProductRule(
            id=f"sfa-{index}",
            identity=IdentityRule(canonical_name=product["name"], pack="250 g",
                                  evidence=(source_ref(),)),
            predicates=(
                PredicateRule(field=PredicateField.LOT, operator=Operator.EXACT,
                              value_type=ValueType.TEXT, values=(product["codes"][0]["value"],),
                              evidence=(source_ref(),)),
                PredicateRule(field=PredicateField.BEST_BEFORE, operator=Operator.EXACT,
                              value_type=ValueType.DATE,
                              values=tuple(product["best_before"]["values"]),
                              evidence=(source_ref(),)),
            ),
        ))
    return AuthorityNotice(
        dependency=SourceDependency(family=source["family"], version=source["id"],
                                    content_hash=source["capture_sha256"], epoch=1,
                                    review_revision=1),
        authority="SFA", original_url=source["url"], final_url=source["url"],
        published_at=date.fromisoformat(source["published_date"]), retrieved_at=NOW,
        jurisdictions=("SG",),
        review=HumanReview(revision=1, reviewer=review["reviewer"],
                           reviewed_at=datetime.fromisoformat(review["reviewed_at"]),
                           record_hash=review["reviewed_manifest_sha256"],
                           rights_basis=review["scope"]),
        interpretation_complete=True, source_available=True,
        source_proposal_agrees=True,  # Test assumption, not actual extraction evidence.
        products=tuple(products),
    )


def observation(name="Camembert Superieur Au Lait Cru", lot="232511"):
    catalog = json.loads(Path("fixtures/synthetic/manifest.json").read_text())
    approved_names = {row["identity"] for row in catalog["fixtures"]}
    resolved = name if name in approved_names else None
    capture = capture_ref(name)
    return ProductObservation(
        session_id="unit-session", incident_id="unit-incident", revision=1,
        captures=(capture,), identity=ProductIdentity(
            name=known(name, evidence=capture), pack=known("250 g", evidence=capture),
            resolved_name=resolved,
            resolution_review_hash=catalog["human_review"]["reviewed_label_manifest_sha256"]
            if resolved else None,
        ),
        fields=(ObservedPredicate(field=PredicateField.LOT,
                                  observation=known(lot, evidence=capture)),
                ObservedPredicate(field=PredicateField.BEST_BEFORE,
                                  observation=known("2026-10-17", ValueType.DATE,
                                                    evidence=capture))),
        model_id="manually-constructed-unit-fixture", prompt_version="no-model-call",
    )


def context(source=None):
    source = source or notice()
    return VerificationContext(
        jurisdiction="SG", mode=SourceMode.HISTORICAL_DEMO,
        historical_selected_at=NOW, current_sources=(source.dependency,),
        result_revision=1, computed_at=NOW,
    )
