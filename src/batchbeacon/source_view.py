"""Deterministic, original-hash-bound raw-span input; never source review authority."""

from dataclasses import dataclass, field
from hashlib import sha256
from typing import Annotated, Literal, Self

from pydantic import Field, model_validator

from batchbeacon.contracts import Digest, Record


class RawSpan(Record):
    start: Annotated[int, Field(ge=0)]
    end: Annotated[int, Field(gt=0)]

    @model_validator(mode='after')
    def nonempty(self) -> Self:
        if self.start >= self.end:
            raise ValueError('source_span_empty')
        return self


class SourceViewPolicy(Record):
    version: Literal['raw-source-spans-1'] = 'raw-source-spans-1'
    original_hash: Digest
    derived_hash: Digest
    # Each span is reviewed source configuration, never selected from a label.
    max_spans: Annotated[int, Field(gt=0)] = 128
    spans: tuple[RawSpan, ...] = Field(min_length=1)

    @model_validator(mode='after')
    def ordered(self) -> Self:
        if len(self.spans) > self.max_spans:
            raise ValueError('source_span_limit')
        if any(a.end >= b.start for a, b in zip(self.spans[:-1], self.spans[1:], strict=True)):
            raise ValueError('source_spans_must_be_ordered_separated')
        return self


class SourceViewBinding(Record):
    policy: SourceViewPolicy
    byte_count: Annotated[int, Field(gt=0)]
    character_count: Annotated[int, Field(gt=0)]


@dataclass(frozen=True)
class SourceView:
    binding: SourceViewBinding
    text: str = field(repr=False)

    def original_range(self, quote: str, occurrence: int) -> tuple[int, int]:
        """Resolve occurrence in shown bytes, rejecting synthetic cut-boundary quotes."""
        start = -1
        for _ in range(occurrence + 1):
            start = self.text.find(quote, start + 1)
            if start < 0:
                raise ValueError('source_quote_unavailable')
        offset = 0
        for span in self.binding.policy.spans:
            length = span.end - span.start
            if offset <= start < offset + length:
                if start + len(quote) > offset + length:
                    raise ValueError('source_quote_crosses_cut')
                original = span.start + start - offset
                return original, original + len(quote)
            offset += length
        raise ValueError('source_quote_unavailable')


def derive_source(original: bytes, policy: SourceViewPolicy) -> SourceView:
    if type(original) is not bytes or sha256(original).hexdigest() != policy.original_hash:
        raise ValueError('source_derivation_original_changed')
    text = original.decode('utf-8', errors='strict')
    if policy.spans[-1].end > len(text):
        raise ValueError('source_derivation_span_unavailable')
    shown = ''.join(text[s.start:s.end] for s in policy.spans)
    encoded = shown.encode('utf-8')
    if sha256(encoded).hexdigest() != policy.derived_hash:
        raise ValueError('source_derivation_changed')
    return SourceView(SourceViewBinding(policy=policy, byte_count=len(encoded),
                                       character_count=len(shown)), shown)
