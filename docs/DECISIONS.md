# Actual implementation decisions

This log supplements SOURCES DEC-01–14 and OWNER_DECISIONS; originals remain unchanged.

| ID | Decision and evidence | Boundary |
| --- | --- | --- |
| LOCAL-01 | Owner explicitly approved initializing a dedicated Git repository in the current batchbeacon-ai folder after discovery found unrelated home Git. Actual root now matches cwd. | Preserve existing files/home repository; no home staging or publication. |
| LOCAL-02 | Preserve recommended FastAPI/Jinja/native JS single-service architecture. Available Python 3.12.13 is the initial dependency compatibility target. | Exact package compatibility and pins still require verification. |
| LOCAL-03 | Existing global Impeccable 4.1.1 differs from selected pinned 4.6.0 source. Stage exact pins and review before local admission. | No implicit use of global copy, installers/hooks or downloaded executables. |
| LOCAL-04 | Current client permissions were already Full Access/never; no setting changed. Native goal still requires useful canary and private finite admission. | CLI capability is not liveness proof; external grants remain bounded. |

Actual current source/trust/design decisions stay pending until their named gates pass.

## LOCAL-05 — completed SFA slice human review
Rohit explicitly confirmed the concrete SFA first-slice packet as written: source
facts, D01/D02 positive, D07 third-identity scoped-negative, synthetic images and
limited factual reuse. Approval is bound to pre-review artifact hashes in
`fixtures/sources/sfa-reviewed.json`. This does not approve UK sources, all D gold,
H custody, final visuals or submission.

## LOCAL-06 — adapted design references
Admit only explicit text-only Impeccable 4.6.0 / Emil pinned derivatives. No upstream
engine, hook, nested writer or publisher request. Unique local names avoid shadowing.
Malformed adaptation diff was reproduced as REQUIRED_CONTRACT, regenerated and
independently verified closed. The original guidance bytes were unaffected.
