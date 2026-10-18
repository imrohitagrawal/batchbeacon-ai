# First real ADK/Gemini development extraction

One bounded real ADK request used the approved original SFA source bytes and an
approved synthetic label with `gemini-3.8-flash` at the global Vertex endpoint.
The provider returned HTTP 200, one STOP candidate and valid transcription/title
JSON. This proves this small actual extraction, not the full product coordinator,
model-quality denominator, real cloud journey or release acceptance.

## Admission and accounting

The owner's clarified no-prior-spending attestation was corroborated by retained
local attempt, inventory and billing observations. Exact account/run evidence is
private. The operation used an explicit development-extraction grant from the
existing ₹1,250 development pool, with one attempt and no automatic retry. It did
not use or enlarge the ₹150 daily-probe pool or protected reserve.

A ₹250 reservation covered a conservative tax-inclusive full-model envelope.
The primary accepted the documented cross-source inference that the published
1,048,576 input / 65,536 output maxima and the same-model response-plus-reasoning
output price define the conservative reservation. The requested 4,096 output cap
was not treated as the full billable ceiling. Sources: [model limits](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/gemini/3-8-flash),
[pricing](https://cloud.google.com/gemini-enterprise-agent-platform/generative-ai/pricing).
Verified account INR rates were conservatively adjusted for the applicable 18%
India tax case; the ₹1,200 tax/reporting buffer remains intact. [Tax basis](https://docs.cloud.google.com/billing/docs/resources/vat-overview).

CountTokens estimated 30,310; returned billable input was 30,390. This observed
80-token difference reinforces that counting is an estimate, not the reservation
ceiling. Complete usage was 30,390 input, 110 candidate output, zero thoughts,
30,500 total. The original attempt was reconciled once at **₹5.256708708** using
conservative tax-inclusive rates, not a claim about a finalized invoice. One paid
attempt remains recorded; no unknown reservation or second paid call was needed.

## Real-service compatibility correction

The initial local parser classified the successful response as invalid and kept
the full reservation. It required an explicit zero thoughts count and rejected an
opaque signature alongside text. The exact original response, initial failure and
ledger snapshot remain private and unchanged.

Vertex defines the thoughts counter as an implicit-presence proto3 integer;
zero-valued fields may be omitted. Only omitted thoughts can default to zero, and
only with an exact total equation. Explicit null/bool/string/negative values,
nonzero residuals, cache/tool use and unknown usage remain rejected. Sources:
[Vertex usage schema](https://github.com/googleapis/googleapis/blob/master/google/cloud/aiplatform/v1/usage_metadata.proto),
[ProtoJSON presence](https://protobuf.dev/programming-guides/json/#presence-and-default-values).

The text reader now permits a validated opaque base64 `thoughtSignature` alongside
text. It never interprets, displays or forwards that signature. Reasoning/tool/
unknown part fields remain rejected. [Content Part definition](https://docs.cloud.google.com/gemini-enterprise-agent-platform/reference/rest/v1/Content#Part).

Independent replay of the actual retained bytes reproduced the old failure,
verified the correction and checked malformed-usage/signature denials. The primary
then reconciled the same attempt and saved a separate recovery receipt. The actual
application parser received the same correction, but its real end-to-end journey
still requires separate execution. Explicit ADK telemetry suppresses message
content; raw provider evidence remains in the private receipt store.
