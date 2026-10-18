"""Immutable acquisition completion payload and store-owned timestamp evidence."""

from dataclasses import dataclass
from datetime import datetime

from pydantic import AwareDatetime

from batchbeacon.contracts import Digest, Record, Revision
from batchbeacon.guest_service import OpaqueId, RequestKey


class AcquisitionCompletion(Record):
    run_id: OpaqueId
    session_id: OpaqueId
    incident_id: OpaqueId
    binding_hash: Digest
    deadline: AwareDatetime
    extraction_key: RequestKey
    extraction_revision: Revision
    extraction_hash: Digest
    observation_revision: Revision
    observation_hash: Digest
    verification_key: RequestKey
    result_revision: Revision
    result_hash: Digest


@dataclass(frozen=True)
class StoredCompletion:
    """Timestamps come from storage metadata, never the domain payload or caller."""
    record: AcquisitionCompletion
    created_at: datetime
    updated_at: datetime

    def timely(self) -> bool:
        return bool(self.created_at.tzinfo is not None and self.updated_at.tzinfo is not None
                    and self.created_at == self.updated_at
                    and self.created_at < self.record.deadline)
