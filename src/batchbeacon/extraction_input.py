"""Pure original-input preparation; no ownership, dispatch or model authority.

The server must select owned retained captures before calling this boundary.
Prepared identity is distinct from token accounting and final ADK wire identity.
"""

import json
from dataclasses import dataclass, field
from hashlib import sha256
from io import BytesIO
from typing import Annotated, Self

from google.genai import types
from PIL import Image
from pydantic import Field, model_serializer, model_validator

from batchbeacon.contracts import AuthorityNotice, Record
from batchbeacon.extraction_proposal import (
    ExtractionProposal,
    ProposalPolicy,
    TranslationReport,
    translate_proposal,
)
from batchbeacon.extraction_records import InputManifest
from batchbeacon.guest_service import Capture
from batchbeacon.source_view import SourceViewPolicy, derive_source
from batchbeacon.uploads import UploadPolicy

Positive = Annotated[int, Field(gt=0)]


def _schema_bytes() -> bytes:
    return json.dumps(ExtractionProposal.model_json_schema(), sort_keys=True,
                      separators=(",", ":")).encode()


class PreparationPolicy(Record):
    proposal: ProposalPolicy = ProposalPolicy()
    upload: UploadPolicy = UploadPolicy()
    max_prompt_bytes: Positive = 16384
    max_schema_bytes: Positive = 65536
    source_view: SourceViewPolicy | None = None

    @model_serializer(mode='wrap')
    def original_compatible(self, handler):
        value = handler(self)
        if self.source_view is None:
            value.pop('source_view', None)
        return value

    @model_validator(mode="after")
    def coherent(self) -> Self:
        if self.proposal.max_captures != self.upload.max_images:
            raise ValueError("preparation capture limits must agree")
        return self


class InputInvalid(ValueError):
    """Sanitized diagnostic, without source, image or validation payload."""


@dataclass(frozen=True)
class PreparedInput:
    """Server-local output, not an accepted public request or dispatch receipt."""

    manifest: InputManifest
    policy: PreparationPolicy
    source_bytes: bytes = field(repr=False)
    image_bytes: tuple[bytes, ...] = field(repr=False)
    instruction: str = field(repr=False)

    def _check_binding(self) -> None:
        if self.policy.digest() != self.manifest.policy_hash \
                or sha256(_schema_bytes()).hexdigest() != self.manifest.schema_hash \
                or sha256(self.source_bytes).hexdigest() != self.manifest.source.content_hash \
                or len(self.source_bytes) != self.manifest.source_bytes \
                or sha256(self.instruction.encode()).hexdigest() != self.manifest.prompt_hash \
                or len(self.image_bytes) != len(self.manifest.captures) \
                or any(len(data) != capture.byte_count
                       or sha256(data).hexdigest() != capture.sha256
                       for capture, data in zip(self.manifest.captures, self.image_bytes,
                                                strict=True)):
            raise InputInvalid("prepared_binding_changed")

    def model_source(self) -> str:
        self._check_binding()
        if self.policy.source_view is None:
            if self.manifest.source_view is not None:
                raise InputInvalid('prepared_source_view_changed')
            return self.source_bytes.decode()
        try:
            view = derive_source(self.source_bytes, self.policy.source_view)
            if view.binding != self.manifest.source_view:
                raise InputInvalid('prepared_source_view_changed')
            return view.text
        except ValueError:
            raise InputInvalid('prepared_source_view_changed') from None

    def user_content(self) -> types.Content:
        self._check_binding()
        # No reviewed rules, expected result, ownership or review marker is sent.
        return types.Content(role="user", parts=[types.Part(text=self.model_source())] + [
            types.Part.from_bytes(data=data, mime_type=capture.mime_type)
            for capture, data in zip(self.manifest.captures, self.image_bytes, strict=True)])

    def translate(self, raw: bytes, notice: AuthorityNotice) -> TranslationReport:
        self.model_source()
        if notice.digest() != self.manifest.notice_digest:
            raise InputInvalid("prepared_notice_changed")
        return translate_proposal(raw, source_bytes=self.source_bytes, notice=notice,
            captures=tuple(c.evidence() for c in self.manifest.captures),
            policy=self.policy.proposal, source_view=(derive_source(self.source_bytes,
                self.policy.source_view) if self.policy.source_view is not None else None))


def prepare_input(*, source_bytes: bytes, notice: AuthorityNotice,
                  captures: tuple[tuple[Capture, bytes], ...], instruction: str,
                  prompt_version: str, policy: PreparationPolicy) -> PreparedInput:
    """Preserve original bytes and validate a bounded selection without I/O.

    Image structure/hash checks do not prove ownership, retention or sanitization
    history. A configured reviewed raw-span view is separately bound; original bytes remain intact.
    No HTML normalization or image re-encoding is performed.
    """
    try:
        if type(source_bytes) is not bytes or not source_bytes \
                or len(source_bytes) > policy.proposal.max_source_bytes \
                or sha256(source_bytes).hexdigest() != notice.dependency.content_hash:
            raise InputInvalid("original_source_invalid")
        text = source_bytes.decode("utf-8", errors="strict")
        if type(instruction) is not str or not instruction.strip() \
                or len(instruction.encode()) > policy.max_prompt_bytes \
                or type(prompt_version) is not str or not prompt_version.strip() \
                or len(prompt_version.encode()) > policy.proposal.max_string_bytes:
            raise InputInvalid("prompt_identity_invalid")
        schema = _schema_bytes()
        if len(schema) > policy.max_schema_bytes:
            raise InputInvalid("schema_byte_limit")
        if type(captures) is not tuple or not 0 < len(captures) <= policy.upload.max_images:
            raise InputInvalid("capture_selection_invalid")
        ids, images, metadata, pixels = set(), [], [], 0
        for pair in captures:
            if type(pair) is not tuple or len(pair) != 2:
                raise InputInvalid("capture_selection_invalid")
            capture, data = pair
            if not isinstance(capture, Capture) or capture.id in ids \
                    or type(data) is not bytes or not data \
                    or len(data) != capture.byte_count \
                    or len(data) > policy.upload.max_image_bytes \
                    or sha256(data).hexdigest() != capture.sha256:
                raise InputInvalid("retained_capture_invalid")
            with Image.open(BytesIO(data), formats=("PNG",)) as image:
                if image.size != (capture.width, capture.height) \
                        or image.width * image.height > policy.upload.max_image_pixels \
                        or getattr(image, "n_frames", 1) != 1:
                    raise InputInvalid("retained_capture_dimensions_invalid")
                image.verify()
            pixels += capture.width * capture.height
            ids.add(capture.id)
            metadata.append(capture)
            images.append(data)
        if pixels > policy.upload.max_combined_pixels:
            raise InputInvalid("combined_capture_pixel_limit")
        for data in images:
            with Image.open(BytesIO(data), formats=("PNG",)) as image:
                image.load()  # Verify actual pixel decoding after all dimension bounds.
        view = (derive_source(source_bytes, policy.source_view)
                if policy.source_view is not None else None)
        manifest = InputManifest(version="derived-input-1" if view else "original-input-1",
            source=notice.dependency, notice_digest=notice.digest(),
            source_bytes=len(source_bytes), source_characters=len(text), captures=tuple(metadata),
            prompt_version=prompt_version, prompt_hash=sha256(instruction.encode()).hexdigest(),
            schema_hash=sha256(schema).hexdigest(), policy_hash=policy.digest(),
            source_view=view.binding if view else None)
        return PreparedInput(manifest=manifest, policy=policy, source_bytes=source_bytes,
                             image_bytes=tuple(images), instruction=instruction)
    except InputInvalid:
        raise
    except (ValueError, TypeError, AttributeError, OSError, SyntaxError,
            OverflowError, RecursionError, Image.DecompressionBombError):
        pass
    # Raise outside the handler: validation exceptions can retain sensitive text.
    raise InputInvalid("input_preparation_invalid")
