# Unified Firestore persistence — local checkpoint

Status: LOCAL/PARTIAL. One SDK adapter now supplies the guest, shared admission,
evidence and action protocols. Creating a guest atomically provisions its usage;
creating an incident atomically provisions its usage, evidence and action records.
Reads never repair missing records. The default application remains unchanged.

## Transaction boundary

The explicitly injected generated Firestore client uses bounded begin, read,
commit and cleanup calls. One validated configuration controls endpoint, database,
namespace, deadlines, retry count and data limits. No constructor discovers
credentials, creates resources or initializes a paid budget. Effective writer
configuration is bound into each stored envelope alongside domain policy hashes.

Every participating document is read before writes. Action transactions include
the server-owned source environment and evidence in their conflict set. Bounded
retries reread the complete snapshot only after a known aborted transaction;
callbacks have no provider or object-storage side effects. Unknown acknowledgments
retain uncertainty and require reconciliation. A failed rollback never proves
that the commit failed or frees a paid reservation.

Strict envelopes preserve typed values and immutable histories. Missing, corrupt,
foreign, partial or oversized state returns unavailable, rather than an empty
success. Database response order is not used to associate records. First-slice
environment selection remains server-owned; mixed-authority selection and genuine
UK update replay are separate work.

## Executed verification

Independent P01–P18 acceptance was recorded before implementation. A separate
read-only reviewer inspected the adapter and reran all **42 offline SDK tests**,
Ruff and whitespace checks. Additional fault probes exercised lost acknowledgments,
retained liabilities, exhausted retries, expired streams and late commits. No
reproduced blocker remains in this bounded checkpoint.

The cached Firestore emulator 1.22.0 was admitted against the
[pinned official distribution metadata](https://github.com/firebase/firebase-tools/blob/6349281b6c1abfd63debf1a4490ce57b484b6a61/src/emulator/downloadableEmulatorInfo.json).
Its size and hashes were checked, and every listener was verified as loopback
before synthetic test data was sent. This verifies the packaged distribution,
not a reproduced build. The owned process was stopped and its listeners closed.

**Four actual local emulator tests passed**, and an independent reviewer reran
all four with fresh namespaces:

- Two separate SDK clients concurrently create one logical incident with coherent
  child state; a newly constructed client reopens retained history.
- Two clients confirm one logical simulated action; a correction preserves its
  history and makes renewed review necessary.
- A source update and confirmation scheduled concurrently leave old evidence
  noncurrent; subsequent preparation of the old hold is denied.
- An exception injected after an actual commit leaves the incident readable and
  reconcilable from another client without duplication.

The source race does not force or assert a server-side abort. Cold reconstruction
reopens clients, not the emulator process. The clients run in one test process;
image objects and the clock are shared test fakes. Lost-acknowledgment emulator
coverage is for incident creation. These limits are retained as explicit follow-up
coverage, not represented as production evidence.

Full locked local checks passed: **519 unit and 48 Chrome browser tests**, plus
lock validation and Ruff. Focused counts overlap with the full suite. Emulator
tests are separately opt-in and are not part of the existing hosted workflow.
Raw logs, source hashes, acceptance and independent review receipts are private.

[Hosted run 39086202851](https://github.com/imrohitagrawal/batchbeacon-ai/actions/runs/39086202851)
passed at `c6ac23be6b50f1c0dce4a491c0b45261451b9be3`: locked wheel bootstrap,
browser installation, lock/Ruff, **519 unit and 48 Chromium browser tests**.
The exact checkout and complete logs were inspected; remote main was verified.
The hosted workflow does not run the emulator or a deployed product journey.

## Remaining gates

Actual Firestore identity/IAM, production transactions and process restart,
private Storage, real bounded extraction, connected UI and deployment remain
unverified. T08 paid admission is closed. No real paid allocation, cloud resource,
stock action, source approval, task completion or release freeze follows from
this local checkpoint. Human UK/new-context review and final submission remain
separate gates.
