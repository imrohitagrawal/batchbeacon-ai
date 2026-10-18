"""Synthetic inputs and wire evidence for shared-record tests; no provider calls."""

import json
from hashlib import sha256

from batchbeacon.extraction_input import prepare_input
from batchbeacon.extraction_records import RunBinding
from batchbeacon.uploads import sanitize_images
from tests.unit.test_extraction_input import inputs
from tests.unit.test_guest_boundary import picture


def run_binding(guests, token, incident_id, configuration_hash="a" * 64):
    key = sha256(token.encode()).hexdigest()
    session = guests.repository.get(key)
    incident = next(i for i in session.incidents if i.id == incident_id)
    if not incident.batches:
        guests.retain(token, incident_id, "binding-upload",
                      sanitize_images((picture(),), guests.policy.uploads))
        incident = next(i for i in guests.repository.get(key).incidents if i.id == incident_id)
    capture = incident.batches[0].captures[0]
    _, args = inputs()
    # Synthetic metadata lineage suffices here; preparation independently tests bytes.
    from batchbeacon.extraction_records import InputManifest
    manifest = InputManifest(source=args["notice"].dependency,
        notice_digest=args["notice"].digest(), source_bytes=len(args["source_bytes"]),
        source_characters=len(args["source_bytes"].decode()), captures=(capture,),
        prompt_version=args["prompt_version"],
        prompt_hash=sha256(args["instruction"].encode()).hexdigest(),
        schema_hash=prepare_input(**args).manifest.schema_hash, policy_hash=args["policy"].digest())
    return RunBinding(manifest=manifest, expected_observation_revision=0,
                      application_configuration_hash=configuration_hash,
                      logical_operation="extract")


def wire_response(input_tokens=100, output_tokens=50, thought_tokens=0, **extra):
    counts = [input_tokens, output_tokens, thought_tokens]
    total = sum(counts) if all(type(n) is int for n in counts) else 0
    return json.dumps({"usageMetadata": {"promptTokenCount": input_tokens,
        "candidatesTokenCount": output_tokens, "thoughtsTokenCount": thought_tokens,
        "totalTokenCount": total}, **extra}).encode()


def record_wire(service, attempt, raw=None, **kwargs):
    raw = wire_response() if raw is None else raw
    return service.record_response(attempt.id, attempt.request_hash, raw,
        status_code=kwargs.get("status_code", 200), complete=kwargs.get("complete", True),
        observed_bytes=kwargs.get("observed_bytes", len(raw)))
