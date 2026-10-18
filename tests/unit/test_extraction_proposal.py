"""T10P01–11 pure synthetic proposals; no model output or source-review claims."""

import copy
import json
from hashlib import sha256

import pytest
from pydantic import ValidationError

from batchbeacon.contracts import (
    EvidenceKind,
    EvidenceRef,
    IdentifierKind,
    Operator,
    ValueState,
)
from batchbeacon.extraction_proposal import (
    ExtractionProposal,
    ProposalInvalid,
    ProposalPolicy,
    TranslationReport,
    translate_proposal,
)
from tests.unit.domain_fixtures import notice, revise


def known(value, *, kind="TEXT", panel=0):
    return {"raw": value, "state": "KNOWN", "value_type": kind, "value": value,
            "locations": [{"panel": panel, "box": [0.1, 0.2, 0.8, 0.4]}]}


def unknown(*, kind="DATE", ambiguous=False):
    return {"raw": "01/02/2026" if ambiguous else "", "state": "AMBIGUOUS" if ambiguous
            else "UNKNOWN", "value_type": kind, "value": None, "locations": []}


def location(value):
    return [{"quote": value, "occurrence": 0}]


def rig():
    reviewed = notice()
    source = json.dumps({"synthetic source": "SG", "products": [
        p.model_dump(mode="json") for p in reviewed.products]}, ensure_ascii=False).encode()
    # Test-only synthetic representation and corresponding references, not a new approval.
    reviewed = type(reviewed).model_validate_json(reviewed.model_dump_json().replace(
        reviewed.dependency.content_hash, sha256(source).hexdigest()))
    products = []
    for p in reviewed.products:
        products.append({"name": p.identity.canonical_name, "pack": p.identity.pack,
            "identifiers": [], "locations": location(p.identity.canonical_name),
            "predicates": [r.model_dump(mode="json", exclude={"evidence"}) |
                {"locations": location(r.values[0])} for r in p.predicates]})
    proposed = {"source": {"jurisdictions": ["SG"], "locations": location("SG"),
                           "products": products},
        "label": {"name": known(products[0]["name"]), "pack": known("250 g"),
                  "identifiers": [], "lot": known("232511"),
                  "best_before": known("2026-10-17", kind="DATE", panel=1),
                  "use_by": unknown()}}
    refs = tuple(EvidenceRef(kind=EvidenceKind.CAPTURE, artifact_id=f"server-panel-{i}",
        sha256=str(i + 1) * 64, locator="retained entire image") for i in range(2))
    return proposed, source, reviewed, refs


def run(proposed=None, *, policy=None, source=None, reviewed=None, captures=None, raw=None):
    p, s, n, c = rig()
    return translate_proposal(raw if raw is not None else json.dumps(
        p if proposed is None else proposed).encode(), source_bytes=s if source is None else source,
        notice=reviewed or n, captures=c if captures is None else captures,
        policy=policy or ProposalPolicy())


def test_complete_two_product_agreement_is_pure_deterministic_and_roundtrips(monkeypatch):
    import socket
    from pathlib import Path

    p, s, n, c = rig()
    originals = copy.deepcopy(p), n.model_dump_json(), tuple(r.model_dump_json() for r in c)

    def forbidden(*args, **kwargs):
        raise AssertionError("translation must be pure")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(Path, "write_text", forbidden)
    monkeypatch.setattr(Path, "write_bytes", forbidden)
    raw = json.dumps(p).encode()
    report = translate_proposal(raw, source_bytes=s, notice=n, captures=c, policy=ProposalPolicy())
    assert report == translate_proposal(raw, source_bytes=s, notice=n, captures=c,
                                       policy=ProposalPolicy())
    assert report.source_status == "AGREES_WITH_REVIEW" and not report.diagnostics
    assert len(report.proposal.source.products) == 2
    assert report.captures == c and report.proposal_hash == sha256(raw).hexdigest()
    assert report.notice_digest == n.digest()
    assert report.label_values.identity.name.evidence[0].artifact_id == c[0].artifact_id
    assert report.label_values.fields[1].observation.evidence[0].sha256 == c[1].sha256
    assert all(r.sha256 == n.dependency.content_hash for r in report.source_locations)
    for ref in report.source_locations:
        _, a, b = ref.locator.split(":")
        assert s.decode()[int(a):int(b)]
    assert TranslationReport.model_validate_json(report.model_dump_json()) == report
    assert originals == (p, n.model_dump_json(), tuple(r.model_dump_json() for r in c))
    assert not hasattr(report, "verdict") and not hasattr(report, "provenance")


@pytest.mark.parametrize("identity", ["Camembert Superieur Au Lait Cru",
    "Bertrand Pere & Fils Camembert au lait cru", "Meadow Vale Brie"])
def test_label_identity_never_infers_a_match_or_reviewed_resolution(identity):
    p, *_ = rig()
    p["label"]["name"] = known(identity)
    r = run(p)
    assert r.label_values.identity.name.value == identity
    assert r.label_values.fields[0].observation.value == "232511"
    assert "resolved_name" not in r.label_values.identity.model_dump()
    assert "verdict" not in r.model_dump()


@pytest.mark.parametrize("change", ["missing_product", "extra_product", "lot", "date",
                                    "geography", "pack", "code_type", "applicability"])
def test_source_disagreement_preserves_proposal_and_translated_label(change):
    p, *_ = rig()
    product = p["source"]["products"][1]
    if change == "missing_product":
        p["source"]["products"].pop()
    elif change == "extra_product":
        extra = copy.deepcopy(product)
        extra["name"] = "Another product"
        p["source"]["products"].append(extra)
    elif change in {"lot", "date"}:
        product["predicates"][change == "date"]["values"] = [
            "2026-10-18" if change == "date" else "0232511"]
    elif change == "geography":
        p["source"]["jurisdictions"] = ["UK-SCT"]
    elif change == "pack":
        product["pack"] = "200 g"
    elif change == "code_type":
        product["identifiers"] = [{"kind": "GTIN", "value": "319456",
                                   "locations": product["locations"]}]
    else:
        product["predicates"][0].update(applies=False, applicability_reason="model says absent")
    report = run(p)
    assert report.source_status == "DISAGREES" and report.diagnostics
    assert report.proposal.model_dump(mode="json") == p
    assert report.label_values.identity.name.value == p["label"]["name"]["value"]


def test_unknown_never_equals_unrestricted_and_range_inclusivity_is_material():
    p, s, n, c = rig()
    product = n.products[0]
    rule = revise(product.predicates[0], operator=Operator.ALL, values=())
    n = revise(n, products=(
        revise(product, predicates=(rule, product.predicates[1])), n.products[1]))
    candidate = p["source"]["products"][0]["predicates"][0]
    candidate.update(operator="UNKNOWN", values=[])
    assert run(p, source=s, reviewed=n, captures=c).source_status == "DISAGREES"
    candidate["operator"] = "ALL"
    assert run(p, source=s, reviewed=n, captures=c).source_status == "AGREES_WITH_REVIEW"
    candidate["operator"] = "NOT_SPECIFIED"
    assert run(p, source=s, reviewed=n, captures=c).source_status == "DISAGREES"
    p, s, n, c = rig()
    from batchbeacon.contracts import DateRange
    span = DateRange.model_validate_json(
        '{"lower":"2026-10-01","upper":"2026-10-31","lower_inclusive":true}')
    product = n.products[0]
    rule = revise(product.predicates[1], operator=Operator.RANGE, values=(), date_range=span)
    n = revise(n, products=(
        revise(product, predicates=(product.predicates[0], rule)), n.products[1]))
    p["source"]["products"][0]["predicates"][1].update(
        operator="RANGE", values=[], date_range=span.model_dump(mode="json"))
    assert run(p, source=s, reviewed=n, captures=c).source_status == "AGREES_WITH_REVIEW"
    p["source"]["products"][0]["predicates"][1]["date_range"]["lower_inclusive"] = False
    assert run(p, source=s, reviewed=n, captures=c).source_status == "DISAGREES"


@pytest.mark.parametrize("field,value", [("review", None), ("interpretation_complete", False)])
def test_missing_human_review_cannot_be_promoted_by_matching_values(field, value):
    p, s, n, c = rig()
    r = run(p, source=s, reviewed=revise(n, **{field: value}), captures=c)
    assert r.source_status == "REVIEW_MISSING" and "SOURCE_REVIEW_REQUIRED" in r.diagnostics


def test_lot_codes_ambiguity_and_missing_values_are_preserved_exactly():
    p, *_ = rig()
    p["label"]["lot"] = known("000aB")
    p["label"]["best_before"] = unknown(ambiguous=True)
    p["label"]["identifiers"] = [{"kind": "PRODUCT_CODE", "observation": known("319456")}]
    r = run(p)
    assert r.label_values.fields[0].observation.value == "000aB"
    assert r.label_values.fields[1].observation.state == ValueState.AMBIGUOUS
    assert r.label_values.fields[1].observation.raw == "01/02/2026"
    assert r.label_values.fields[1].observation.value is None
    assert r.label_values.fields[2].observation.state == ValueState.UNKNOWN
    assert r.label_values.identity.identifiers[0].kind == IdentifierKind.PRODUCT_CODE
    p["label"]["identifiers"][0]["observation"]["raw"] = "0319456"
    with pytest.raises(ProposalInvalid, match="normalization_forbidden"):
        run(p)


@pytest.mark.parametrize("field,raw,value", [
    ("name", "Meadow Vale Brie", "Camembert Superieur Au Lait Cru"),
    ("pack", "100 g", "250 g"),
    ("best_before", "01/02/2026", "2026-01-02"),
    ("use_by", "01/02/2026", "2026-02-01"),
])
def test_asserted_value_cannot_contradict_or_disambiguate_its_raw_field(field, raw, value):
    p, *_ = rig()
    p["label"][field] = known(value, kind="DATE" if field in {"best_before", "use_by"}
                              else "TEXT")
    p["label"][field]["raw"] = raw
    with pytest.raises(ProposalInvalid):
        run(p)


@pytest.mark.parametrize("raw,value,valid", [
    ("17/10/2026", "2026-10-17", True), ("10/17/2026", "2026-10-17", True),
    ("01/01/2026", "2026-01-01", True), ("29/02/2024", "2024-02-29", True),
    ("29/02/2026", "2026-02-28", False), ("31/04/2026", "2026-04-30", False),
    ("17/10/2026", "2026-10-18", False), ("17 Oct 2026", "2026-10-17", False),
    ("20261017", "2026-10-17", False),
])
def test_only_versioned_deterministic_date_normalization_is_admitted(raw, value, valid):
    p, *_ = rig()
    p["label"]["best_before"] = known(value, kind="DATE")
    p["label"]["best_before"]["raw"] = raw
    if valid:
        result = run(p).label_values.fields[1].observation
        assert result.raw == raw and result.value == value
    else:
        with pytest.raises(ProposalInvalid):
            run(p)


@pytest.mark.parametrize("scope,key", [("root", "provenance"), ("root", "session_id"),
    ("root", "budget"), ("root", "current"), ("source", "review"),
    ("source", "reviewed"), ("source", "recall_reason"), ("label", "resolved_name"),
    ("label", "verdict"), ("label", "action_eligible")])
def test_model_authority_and_separately_pending_context_are_rejected(scope, key):
    p, *_ = rig()
    (p if scope == "root" else p[scope])[key] = True
    with pytest.raises(ProposalInvalid):
        run(p)


@pytest.mark.parametrize("panel", [-1, True, 2, "0", 0.5])
def test_bad_panel_cannot_escape_server_selection(panel):
    p, *_ = rig()
    p["label"]["name"]["locations"][0]["panel"] = panel
    with pytest.raises(ProposalInvalid):
        run(p)


@pytest.mark.parametrize("box", [[0, 0, 0, 1], [1, 0, 0, 1], [0, -0.1, 1, 1],
                                 [0, 0, 1.1, 1], [False, 0, 1, 1], [0, 0, 1]])
def test_invalid_capture_location_is_rejected(box):
    p, *_ = rig()
    p["label"]["name"]["locations"][0]["box"] = box
    with pytest.raises(ProposalInvalid):
        run(p)


@pytest.mark.parametrize("change", ["foreign_capture_id", "foreign_source_hash", "missing_label",
    "missing_source", "absent_quote", "boolean_occurrence", "duplicate_product", "bad_operator",
    "bad_type", "boolean_applies", "known_without_value", "ambiguous_with_value", "duplicate_code"])
def test_structural_failures_are_sanitized_and_never_repaired(change):
    p, *_ = rig()
    source = p["source"]["products"][0]
    if change == "foreign_capture_id":
        p["label"]["name"]["locations"][0]["capture_id"] = "foreign"
    elif change == "foreign_source_hash":
        source["locations"][0]["sha256"] = "a" * 64
    elif change == "missing_label":
        p["label"]["name"]["locations"] = []
    elif change == "missing_source":
        source["predicates"][0]["locations"] = []
    elif change == "absent_quote":
        source["locations"] = location("not in the exact source")
    elif change == "boolean_occurrence":
        source["locations"][0]["occurrence"] = True
    elif change == "duplicate_product":
        p["source"]["products"].append(copy.deepcopy(source))
    elif change == "bad_operator":
        source["predicates"][0]["operator"] = "REGEX"
    elif change == "bad_type":
        p["label"]["lot"]["value_type"] = "DATE"
    elif change == "boolean_applies":
        source["predicates"][0]["applies"] = 1
    elif change == "known_without_value":
        p["label"]["lot"]["value"] = None
    elif change == "ambiguous_with_value":
        p["label"]["lot"]["state"] = "AMBIGUOUS"
    else:
        code = {"kind": "PRODUCT_CODE", "observation": known("319456")}
        p["label"]["identifiers"] = [code, code]
    with pytest.raises(ProposalInvalid) as caught:
        run(p)
    assert "Camembert" not in str(caught.value) and "foreign" not in str(caught.value)


@pytest.mark.parametrize("raw", [b'', b'{', b'[]', b'{"source":{},"source":{}}',
    b'[' * 11000 + b'0' + b']' * 11000, b'{"secret":"\xff"}'])
def test_malformed_duplicate_and_deep_json_fail_safely(raw):
    with pytest.raises(ProposalInvalid):
        run(raw=raw)


def test_standard_error_traceback_does_not_retain_untrusted_payload():
    import traceback

    p, *_ = rig()
    marker = "synthetic-private" + "-payload-marker-84291"
    p["label"]["name"]["state"] = {"untrusted": marker}
    with pytest.raises(ProposalInvalid) as caught:
        run(p)
    assert marker not in "".join(traceback.format_exception(caught.value))
    assert caught.value.__cause__ is None and caught.value.__context__ is None


def test_policy_exact_byte_boundary_override_and_one_over_are_effective():
    p, *_ = rig()
    raw = json.dumps(p).encode()
    policy = ProposalPolicy(max_proposal_bytes=len(raw), max_string_bytes=1024)
    report = run(raw=raw, policy=policy)
    assert report.policy_hash == policy.digest()
    with pytest.raises(ProposalInvalid, match="byte_limit"):
        run(raw=raw + b' ', policy=policy)
    with pytest.raises(ProposalInvalid, match="string_limit"):
        run(policy=ProposalPolicy(max_string_bytes=16, max_quote_bytes=16))
    with pytest.raises(ProposalInvalid, match="collection_limit"):
        run(policy=ProposalPolicy(max_collection_items=2))
    with pytest.raises(ProposalInvalid, match="nesting_limit"):
        run(policy=ProposalPolicy(max_nesting=2))
    with pytest.raises(ProposalInvalid, match="source_bytes"):
        run(policy=ProposalPolicy(max_source_bytes=1))
    with pytest.raises(ProposalInvalid, match="capture_selection"):
        run(policy=ProposalPolicy(max_captures=1))


def test_quote_limits_occurrences_and_source_hash_binding():
    p, s, n, c = rig()
    p["source"]["locations"] = [{"quote": "250 g", "occurrence": 1}]
    assert run(p).source_status == "AGREES_WITH_REVIEW"
    with pytest.raises(ProposalInvalid, match="location_limit"):
        run(p, policy=ProposalPolicy(max_quote_occurrence=0))
    p["source"]["locations"][0]["occurrence"] = 32
    with pytest.raises(ProposalInvalid, match="quote_unavailable"):
        run(p)
    with pytest.raises(ProposalInvalid, match="location_limit"):
        run(policy=ProposalPolicy(max_quote_bytes=1))
    with pytest.raises(ProposalInvalid, match="source_bytes"):
        run(source=s + b' ')
    changed = run(source=s, reviewed=revise(n, dependency=revise(n.dependency, epoch=2)),
                  captures=c)
    assert changed.notice_digest != run().notice_digest
    assert changed.source_dependency.epoch == 2
    assert run(policy=ProposalPolicy(max_quote_occurrence=3)).digest() != run().digest()
    altered = (revise(c[0], sha256="c" * 64), c[1])
    assert run(captures=altered).digest() != run().digest()


@pytest.mark.parametrize("policy", [{"max_proposal_bytes": True}, {"max_source_bytes": 0},
    {"max_quote_occurrence": -1}, {"max_captures": 3}, {"max_nesting": 0},
    {"max_quote_bytes": 5000}, {"max_proposal_bytes": 100}])
def test_invalid_configuration_rejected(policy):
    with pytest.raises(ValidationError):
        ProposalPolicy(**policy)


def test_closed_schema_and_product_order_independent_comparison():
    p, *_ = rig()
    p["source"]["products"].reverse()
    for product in p["source"]["products"]:
        product["predicates"].reverse()
    assert run(p).source_status == "AGREES_WITH_REVIEW"
    schema = ExtractionProposal.model_json_schema()
    assert schema["additionalProperties"] is False
    assert all(d.get("additionalProperties") is False for d in schema["$defs"].values()
               if d.get("type") == "object")


def test_fixed_label_types_are_declared_in_model_schema_even_for_unknown_dates():
    """The provider schema must describe the same fixed types the translator enforces."""
    from pydantic import ValidationError

    from batchbeacon.extraction_proposal import ExtractionProposal
    schema = ExtractionProposal.model_json_schema()
    fields = schema['$defs']['LabelProposal']['properties']
    for field in ('name', 'pack', 'lot', 'best_before', 'use_by'):
        definition = schema['$defs'][fields[field]['$ref'].split('/')[-1]]
        expected = 'DATE' if field in ('best_before', 'use_by') else 'TEXT'
        assert definition['properties']['value_type']['const'] == expected
    proposal, *_ = rig()
    proposal['label']['use_by'] = unknown(kind='TEXT')
    with pytest.raises(ValidationError):
        ExtractionProposal.model_validate_json(json.dumps(proposal))
