"""Provider-neutral original-input lineage; never a guest authority assertion."""

from typing import Annotated, Literal

from pydantic import Field

from batchbeacon.contracts import Digest, Nonempty, Record, SourceDependency
from batchbeacon.guest_service import Capture, RequestKey

Positive = Annotated[int, Field(gt=0)]


class InputManifest(Record):
    version: Literal["original-input-1"] = "original-input-1"
    source: SourceDependency
    notice_digest: Digest
    source_bytes: Positive
    source_characters: Positive
    captures: tuple[Capture, ...] = Field(min_length=1, max_length=2)
    prompt_version: Nonempty
    prompt_hash: Digest
    schema_hash: Digest
    policy_hash: Digest



class RunBinding(Record):
    manifest: InputManifest
    expected_observation_revision: Annotated[int, Field(ge=0)]
    application_configuration_hash: Digest
    logical_operation: RequestKey
