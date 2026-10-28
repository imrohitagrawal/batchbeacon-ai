"""Content-free runtime signals for the existing private admission alert.

Emit only after a transaction outcome is acknowledged, never in its callback.
The event vocabulary is the stable monitoring protocol; thresholds remain in
the operator's alert policy. Logging is observational and confers no authority.
"""

import json
import logging
from typing import Literal

from batchbeacon.contracts import Digest, Record


class AdmissionEvent(Record):
    application: Literal['batchbeacon'] = 'batchbeacon'
    origin: Literal['runtime'] = 'runtime'
    event: Literal['allowance_exhausted', 'cost_circuit_open']
    policy_hash: Digest
    grant_hash: Digest


_logger = logging.getLogger(__name__)
_logger.setLevel(logging.INFO)
_logger.propagate = False
if not _logger.handlers:
    _logger.addHandler(logging.StreamHandler())


def emit(event, policy_hash, grant_hash):
    try:
        record = AdmissionEvent(event=event, policy_hash=policy_hash, grant_hash=grant_hash)
        _logger.info(json.dumps(record.model_dump(), separators=(',', ':')))
    except Exception:
        # Telemetry must never change admission, accounting or recovery outcomes.
        pass
