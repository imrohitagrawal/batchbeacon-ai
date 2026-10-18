"""Original-input lineage; synthetic records only, no provider or source approval."""

import json
import socket
import traceback
from dataclasses import FrozenInstanceError, replace
from hashlib import sha256
from io import BytesIO
from pathlib import Path

import pytest
from PIL import Image
from pydantic import ValidationError

from batchbeacon.extraction_input import InputInvalid, PreparationPolicy, prepare_input
from batchbeacon.extraction_proposal import ProposalPolicy
from batchbeacon.guest_service import Capture
from batchbeacon.uploads import UploadPolicy, sanitize_images
from tests.unit.domain_fixtures import revise
from tests.unit.test_extraction_proposal import rig


def inputs():
    p, source, notice, _ = rig()
    pairs = []
    for i, color in enumerate(("white", "blue")):
        output = BytesIO()
        Image.new("RGB", (16, 12), color).save(output, format="PNG")
        data = output.getvalue()
        pairs.append((Capture(id=str(i + 1) * 32, sha256=sha256(data).hexdigest(),
            byte_count=len(data), width=16, height=12), data))
    return p, dict(source_bytes=source, notice=notice, captures=tuple(pairs),
                  instruction="Synthetic compatibility instruction only.",
                  prompt_version="test-only-v1", policy=PreparationPolicy())


def bind_source(args, source):
    old = args["notice"]
    args["source_bytes"] = source
    args["notice"] = type(old).model_validate_json(old.model_dump_json().replace(
        old.dependency.content_hash, sha256(source).hexdigest()))


def test_preparation_is_pure_immutable_and_contains_only_original_model_data(monkeypatch):
    proposal, args = inputs()

    def forbidden(*a, **kw):
        raise AssertionError("preparation must not perform external I/O")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(Path, "write_text", forbidden)
    monkeypatch.setattr(Path, "write_bytes", forbidden)
    prepared = prepare_input(**args)
    assert prepared == prepare_input(**args)
    assert prepared.manifest.policy_hash == args["policy"].digest()
    assert prepared.manifest.source == args["notice"].dependency
    content = prepared.user_content()
    assert content.role == "user" and len(content.parts) == 3
    assert content.parts[0].text.encode() == args["source_bytes"]
    for part, (capture, data) in zip(content.parts[1:], args["captures"], strict=True):
        assert part.inline_data.data == data
        assert part.inline_data.mime_type == capture.mime_type
    report = prepared.translate(json.dumps(proposal).encode(), args["notice"])
    assert report.source_status == "AGREES_WITH_REVIEW"
    assert report.policy_hash == args["policy"].proposal.digest()
    assert report.schema_hash == prepared.manifest.schema_hash
    assert report.captures == tuple(c.evidence() for c, _ in args["captures"])
    assert "instruction" not in prepared.manifest.model_dump()
    assert args["instruction"] not in repr(prepared)
    with pytest.raises(FrozenInstanceError):
        prepared.source_bytes = b"changed"


def test_source_limit_is_effective_for_preparation_and_translation_without_truncation():
    proposal, args = inputs()
    original = args["source_bytes"]
    bind_source(args, original + b" " * (109097 - len(original)))
    with pytest.raises(InputInvalid, match="original_source"):
        prepare_input(**args)
    args["policy"] = PreparationPolicy(proposal=ProposalPolicy(max_source_bytes=109097))
    prepared = prepare_input(**args)
    assert len(prepared.user_content().parts[0].text.encode()) == 109097
    assert prepared.translate(json.dumps(proposal).encode(), args["notice"]).policy_hash \
        == args["policy"].proposal.digest()
    bind_source(args, args["source_bytes"] + b" ")
    with pytest.raises(InputInvalid, match="original_source"):
        prepare_input(**args)


def test_multibyte_repeated_quote_offsets_are_original_characters():
    proposal, args = inputs()
    bind_source(args, "é🍊 SG SG\n".encode() + args["source_bytes"])
    proposal["source"]["locations"] = [{"quote": "SG", "occurrence": 1}]
    prepared = prepare_input(**args)
    assert prepared.manifest.source_bytes > prepared.manifest.source_characters
    report = prepared.translate(json.dumps(proposal).encode(), args["notice"])
    assert report.source_locations[0].locator == "characters:6:8"
    assert args["source_bytes"].decode()[6:8] == "SG"


@pytest.mark.parametrize("change", ["source", "policy", "image", "instruction"])
def test_changed_prepared_material_denied_before_content_or_translation(change):
    proposal, args = inputs()
    prepared = prepare_input(**args)
    changes = {"source": {"source_bytes": prepared.source_bytes + b" "},
        "policy": {"policy": PreparationPolicy(max_prompt_bytes=100)},
        "image": {"image_bytes": tuple(reversed(prepared.image_bytes))},
        "instruction": {"instruction": "Changed instruction"}}
    changed = replace(prepared, **changes[change])
    with pytest.raises(InputInvalid, match="binding_changed"):
        changed.user_content()
    with pytest.raises(InputInvalid, match="binding_changed"):
        changed.translate(json.dumps(proposal).encode(), args["notice"])


def test_notice_review_change_denies_prepared_translation():
    proposal, args = inputs()
    prepared = prepare_input(**args)
    with pytest.raises(InputInvalid, match="notice_changed"):
        prepared.translate(json.dumps(proposal).encode(), revise(args["notice"], review=None))


def test_changed_schema_denies_prepared_content_and_translation(monkeypatch):
    import batchbeacon.extraction_input as module

    proposal, args = inputs()
    prepared = prepare_input(**args)
    monkeypatch.setattr(module, "_schema_bytes", lambda: b'{"changed":"schema"}')
    with pytest.raises(InputInvalid, match="binding_changed"):
        prepared.user_content()
    with pytest.raises(InputInvalid, match="binding_changed"):
        prepared.translate(json.dumps(proposal).encode(), args["notice"])


@pytest.mark.parametrize("change", ["empty", "three", "duplicate", "bytearray", "hash",
    "size", "dimensions", "not_png", "truncated", "source_hash", "source_encoding"])
def test_invalid_inputs_fail_with_sanitized_unchained_errors(change):
    _, args = inputs()
    capture, data = args["captures"][0]
    if change == "empty":
        args["captures"] = ()
    elif change == "three":
        args["captures"] += (args["captures"][0],)
    elif change == "duplicate":
        args["captures"] = (args["captures"][0],) * 2
    elif change == "source_hash":
        args["source_bytes"] += b" "
    elif change == "source_encoding":
        bind_source(args, b"\xffprivate_source_payload")
    else:
        if change == "bytearray":
            data = bytearray(data)
        elif change == "hash":
            capture = revise(capture, sha256="f" * 64)
        elif change == "size":
            capture = revise(capture, byte_count=len(data) + 1)
        elif change == "dimensions":
            capture = revise(capture, width=17)
        else:
            data = b"private_source_payload" if change == "not_png" else data[:40]
            capture = revise(capture, byte_count=len(data), sha256=sha256(data).hexdigest())
        args["captures"] = ((capture, data),)
    with pytest.raises(InputInvalid) as error:
        prepare_input(**args)
    assert error.value.__context__ is None and error.value.__cause__ is None
    assert "private_source_payload" not in "".join(traceback.format_exception(error.value))


def test_sanitized_asset_hash_is_distinct_and_retained_bytes_are_used():
    _, args = inputs()
    capture, original = args["captures"][0]
    image, = sanitize_images((original,), UploadPolicy(png_compress_level=0))
    assert image.data != original
    args["captures"] = ((capture, image.data),)
    with pytest.raises(InputInvalid):
        prepare_input(**args)
    capture = revise(capture, sha256=sha256(image.data).hexdigest(), byte_count=len(image.data))
    args["captures"] = ((capture, image.data),)
    assert prepare_input(**args).user_content().parts[1].inline_data.data == image.data


@pytest.mark.parametrize("override", [dict(max_prompt_bytes=0), dict(max_schema_bytes=True),
    dict(max_prompt_bytes=float("inf")), dict(proposal=ProposalPolicy(max_captures=1))])
def test_invalid_configuration_denied(override):
    with pytest.raises(ValidationError):
        PreparationPolicy(**override)


@pytest.mark.parametrize("limit", ["prompt", "schema", "pixels", "combined", "bytes"])
def test_effective_resource_overrides_reach_actual_preparation(limit):
    _, args = inputs()
    if limit == "prompt":
        args["policy"] = PreparationPolicy(max_prompt_bytes=1)
    elif limit == "schema":
        args["policy"] = PreparationPolicy(max_schema_bytes=1)
    else:
        upload = {"pixels": dict(max_image_pixels=100, max_combined_pixels=200),
                  "combined": dict(max_image_pixels=200, max_combined_pixels=200),
                  "bytes": dict(max_image_bytes=10, spool_bytes=10)}[limit]
        args["policy"] = PreparationPolicy(upload=UploadPolicy(**upload))
    with pytest.raises(InputInvalid):
        prepare_input(**args)


def test_order_prompt_version_and_effective_policy_change_prepared_identity():
    _, args = inputs()
    baseline = prepare_input(**args).manifest.digest()
    variants = [dict(captures=tuple(reversed(args["captures"]))),
                dict(prompt_version="test-only-v2"), dict(instruction="Another test instruction"),
                dict(policy=PreparationPolicy(max_schema_bytes=70000))]
    assert len({baseline, *(prepare_input(**(args | v)).manifest.digest() for v in variants)}) == 5
