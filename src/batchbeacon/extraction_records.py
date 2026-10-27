"""Provider-neutral original-input lineage; never a guest authority assertion."""

from typing import Annotated, Literal

from pydantic import Field, model_serializer, model_validator

from batchbeacon.contracts import Digest, Nonempty, Record, SourceDependency
from batchbeacon.guest_service import Capture, RequestKey
from batchbeacon.source_view import SourceViewBinding

Positive = Annotated[int, Field(gt=0)]


class InputManifest(Record):
    version: Literal["original-input-1", "derived-input-1"] = "original-input-1"
    source: SourceDependency
    notice_digest: Digest
    source_bytes: Positive
    source_characters: Positive
    captures: tuple[Capture, ...] = Field(min_length=1, max_length=2)
    prompt_version: Nonempty
    prompt_hash: Digest
    schema_hash: Digest
    policy_hash: Digest
    source_view: SourceViewBinding | None = None

    @model_validator(mode='after')
    def view_version(self):
        if (self.source_view is None) != (self.version == 'original-input-1'):
            raise ValueError('source_view_version_mismatch')
        return self

    @model_serializer(mode='wrap')
    def original_compatible(self, handler):
        value = handler(self)
        if self.source_view is None:
            value.pop('source_view', None)
        return value



class RunBinding(Record):
    manifest: InputManifest
    expected_observation_revision: Annotated[int, Field(ge=0)]
    application_configuration_hash: Digest
    logical_operation: RequestKey
