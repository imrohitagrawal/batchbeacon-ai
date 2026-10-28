"""Review-only update lineage; fixtures confer no human source approval."""

import json
from datetime import date
from hashlib import sha256
from pathlib import Path

import pytest
from pydantic import ValidationError

from batchbeacon.contracts import AuthorityNotice
from batchbeacon.source_update import SourceUpdatePolicy, SourceVersion, prepare_source_update


def version(identifier, content, *, supersedes=None, jurisdictions=("GB-ENG", "GB-NIR")):
    return SourceVersion(
        family="FSA-PRIN-47-2026", version=identifier,
        content_hash=sha256(content).hexdigest(), supersedes=supersedes,
        published_at=date(2026, 9, 25) if supersedes else date(2026, 9, 24),
        jurisdictions=jurisdictions,
    )


@pytest.fixture
def policy():
    return SourceUpdatePolicy(
        original=version("original", b"original"),
        update=version("update", b"update", supersedes="original",
                       jurisdictions=("GB-ENG", "GB-NIR", "GB-WLS", "GB-SCT")),
    )


def changed(record, **values):
    return type(record).model_validate(record.model_dump() | values)


def test_forward_pair_is_bound_review_only_and_cannot_authorize(policy):
    before = policy.model_dump_json()
    result = prepare_source_update(b"original", b"update", policy)
    assert result.original == policy.original and result.update == policy.update
    assert result.added_jurisdictions == ("GB-WLS", "GB-SCT")
    assert result.removed_jurisdictions == ()
    assert result.policy_hash == policy.digest()
    assert result.human_review == "PENDING" and result.activation_allowed is False
    assert result == prepare_source_update(b"original", b"update", policy)
    assert policy.model_dump_json() == before
    with pytest.raises(ValidationError):
        AuthorityNotice.model_validate(result.model_dump())
    with pytest.raises(ValidationError):
        changed(result, activation_allowed=True)


@pytest.mark.parametrize("values", [
    {"version": "original"}, {"supersedes": "unrelated"},
    {"family": "different-family"}, {"content_hash": sha256(b"original").hexdigest()},
    {"published_at": date(2026, 9, 23)},
])
def test_invalid_or_backward_lineage_denied(policy, values):
    with pytest.raises(ValidationError):
        changed(policy, update=changed(policy.update, **values))


def test_reverse_pair_cannot_prepare(policy):
    with pytest.raises(ValidationError):
        changed(policy, original=policy.update, update=policy.original)


def test_cyclic_supersession_denied(policy):
    with pytest.raises(ValidationError):
        changed(policy, original=changed(policy.original, supersedes="update"))


@pytest.mark.parametrize("values", [
    {"policy_hash": "0" * 64}, {"added_jurisdictions": ()},
    {"removed_jurisdictions": ("GB-ENG",)}, {"human_review": "APPROVED"},
])
def test_receipt_cannot_forge_policy_scope_or_review(policy, values):
    receipt = prepare_source_update(b"original", b"update", policy)
    with pytest.raises(ValidationError):
        changed(receipt, **values)


@pytest.mark.parametrize("field,value", [
    ("jurisdictions", ()), ("jurisdictions", ("GB-ENG", "GB-ENG")),
    ("jurisdictions", ("ALL",)), ("jurisdictions", ("GB",)),
    ("jurisdictions", ("GB-ENG", "SG")),
    ("version", ""), ("content_hash", "bad"),
])
def test_invalid_version_metadata_denied(policy, field, value):
    with pytest.raises(ValidationError):
        changed(policy.original, **{field: value})


@pytest.mark.parametrize("original,update", [
    (b"changed", b"update"), (b"original", b"changed"),
    (b"", b"update"), (b"original", b""),
    (bytearray(b"original"), b"update"), ("original", b"update"),
])
def test_unbound_or_nonbytes_captures_denied(policy, original, update):
    with pytest.raises(ValueError, match="source_update_capture"):
        prepare_source_update(original, update, policy)


@pytest.mark.parametrize("limit", [0, -1, True, "100", float("inf"), float("nan")])
def test_invalid_byte_policy_denied(policy, limit):
    with pytest.raises(ValidationError):
        changed(policy, max_capture_bytes=limit)


def test_effective_byte_limit_defaults_overrides_and_boundary(policy):
    assert policy.max_capture_bytes > len(b"original")
    exact = changed(policy, max_capture_bytes=len(b"original"))
    assert prepare_source_update(b"original", b"update", exact).policy_hash == exact.digest()
    short = changed(policy, max_capture_bytes=len(b"original") - 1)
    with pytest.raises(ValueError, match="source_update_capture"):
        prepare_source_update(b"original", b"update", short)


def test_changed_scope_can_remove_territory_without_becoming_clearance(policy):
    update = changed(policy.update, jurisdictions=("GB-ENG",))
    result = prepare_source_update(b"original", b"update", changed(policy, update=update))
    assert result.removed_jurisdictions == ("GB-NIR",)
    assert not result.activation_allowed and result.human_review == "PENDING"


def test_exact_genuine_pair_metadata_is_preserved_without_promoting_draft_predicates():
    rows = json.loads(Path("fixtures/sources/manifest.draft.json").read_text())["sources"][1:]
    versions = tuple(SourceVersion(
        family=r["family"], version=r["id"], content_hash=r["capture_sha256"],
        supersedes=r["supersedes"], published_at=date.fromisoformat(r["published_date"]),
        jurisdictions=tuple(r["jurisdictions"]),
    ) for r in rows)
    admitted = SourceUpdatePolicy(original=versions[0], update=versions[1])
    assert admitted.update.supersedes == admitted.original.version
    assert versions[0].content_hash == (
        "eaa2d450ea8297d41f262fe87ee09f249693b986a610056ed9f6c23c314eee41")
    assert versions[1].content_hash == (
        "30323780ab5676ad9960ec0760e8c728577e5ac08ac2e6f798579f3691324043")
    # Metadata-only public fixture test; exact captured bytes are checked privately.
    assert all(r["human_review"] == "PENDING" for r in rows)
    assert all([p["codes"][0]["value"] for p in r["products"]] == ["319456", "318591"]
               for r in rows)
