# Actual Firestore and private Storage acceptance

Actual Google SDK execution passed eight bounded acceptance scenarios using two
independent clients, the existing project, a Native Standard Mumbai database and
its private Standard image bucket. Extraction/source fixtures in this test were
explicitly synthetic. This is real data-service evidence, not Gemini, deployed
runtime identity, Cloud Run topology or release approval.

Observed cases:

- Atomic guest/incident provisioning and cold-client owned reads.
- An actual committed write with an injected lost acknowledgement reconciled
  under the original request key without duplicate incidents.
- Sanitized PNG upload, exact SHA/CRC readback and duplicate-upload recovery;
  a foreign guest could not read its image, evidence or actions.
- Simultaneous confirmations through independent clients created one logical
  simulated action/event, visible in a cold retail queue read.
- An observation correction and source-epoch change invalidated currentness;
  a stale prepared confirmation was rejected and historical action retained.
- Unsigned requests to the exact newly created Storage object and Firestore
  document were denied.
- Injected clocks at session/object expiry denied access immediately while
  retained records remained. This does not prove delayed physical deletion.
- No model budget was initialized by this isolated data test.

The first attempt passed provisioning and lost-ack recovery, then failed during
image readback. Independent offline reproduction located the defect in the
private test harness: it consumed/closed the raw response before the installed
Storage SDK's RawDownload consumer. Exact bounded raw replay corrected it;
bounded plain/gzip metadata and oversized-response rejection were independently
checked. The second actual attempt passed. Original failed evidence and exact
created-object/document manifests remain private and unchanged.

Combined measured activity: 393 document reads, 55 writes, three Storage Class A
and 33 conservatively charged Class B requests, 1,598,548 downloaded response
bytes, with no unresolved response-byte reservation. Finite admission and actual
account-price basis remain in ignored local records, within the existing data
allocation. No free-tier assumption or budget increase was used.

The database has deletion protection. The bucket has uniform access, enforced
public-access prevention, a one-day live-object lifecycle target and seven-day
soft retention. No anonymous IAM member was present. Exact precondition-bound cleanup deleted the 22 manifest-listed test documents
and removed the two live object generations; subsequent reads confirmed absence.
The provider returned soft-delete and future hard-delete times for both objects.
Soft retention remains; no physical deletion, automatic Firestore TTL or
production-retention pass is claimed here.

Independent review checked actual receipts against executable assertions and
verified cumulative bounds. Remaining gates include attached runtime IAM,
deployed cross-instance isolation/admission, full real-model journey, public
security/cost checks, learning/operations coverage and release evidence.
