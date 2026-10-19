# Evaluation workspace wording and guest admission rate

U26 approves clearer interface terminology: Evaluation workspace, Non-production
data and ordinary action labels. Sample labels and inventory are disclosed; AI
analysis and saved workflows are functional. Confirmation and completion make
clear that no live inventory is updated. Backend action identifiers, explicit
consent and unresolved-review semantics remain unchanged. Historical sample
artifacts and source evidence are preserved.

U27 corrects the requested new-session burst rate to 30 per 60-second window,
superseding both the deployed 4 and the intermediate request for 10. The lifetime
ceiling remains explicitly null, existing access lasts eight hours, and all other
runtime fields are unchanged. A conditional policy-hash-only migration preserves
issuance counts, the current window and existing sessions. This is not persistent
account implementation or an increase in model budgets.

## Verification

Source `f0d9c0f974baf5e68992d274d48c8bddcc59fba1` is merged in
[PR7](https://github.com/imrohitagrawal/batchbeacon-ai/pull/7). Exact
[hosted push](https://github.com/imrohitagrawal/batchbeacon-ai/actions/runs/39289689576)
and [hosted PR](https://github.com/imrohitagrawal/batchbeacon-ai/actions/runs/39289698513)
checks each passed 1,341 unit, 86 browser and 29 edge checks, including locked
bootstrap and actual checkout environments. Initial local checks found
stale loading/header expectations after the approved wording change. Those tests
were updated without changing behavior or weakening assertions; failed logs are
retained. Local corrected unit suite passed 1,340 before the new rate test; all 21
admission tests including the new rate case passed afterward. Local full browser
suite had 85 passes/1 stale-label failure; the corrected focused tutorial case passed
both primary and independent reruns. Local 29 edge checks passed.

The new admission test proves 30 allowances, rejection of the 31st before 60 seconds,
exact reset at 60 seconds, preserved lifetime counts and continued access for
an existing session across the policy-hash transition. Independent review verified
this test and the typed runtime diff. This is contract verification, not a live
30-user concurrency/load test.

Exact image packaging uses one 61-file manifest, actual upload selection, an
unmounted Docker build and network-disabled image checks. Those checks assert
30/60 in the packaged runtime. The actual generation-bound uploaded archive matched
all 61 manifest files. The bounded cloud build and all four steps passed. Image:
`sha256:2d37f9156cf91b5c9c3197b5cd1fc1a169912ca20d5a10933ac348be54db9c47`.
Runtime hash:
`0b5394085b81b862a815da89cd054f42838f25043922c75dd4786341138f16e4`.

The ready candidate was held without traffic while its exact configuration and
unchanged resource/IAM controls were verified. The admission document changed
only its policy hash using an update-time precondition; counts and timestamps were
preserved. The exact revision then received 100% traffic. No session, shop, model
ledger or namespace was reset. One bounded build reserved INR7 from existing
contingency, without increasing the overall budget; this is not actual billed cost.

Live custom-host/mobile and fallback/desktop checks passed 28 assertions: fresh
access, secure cookies, workspace/non-production disclosure, real-AI mode label,
queue/guidance loads, absence of replaced labels in rendered UI, no horizontal
overflow, exact HTML/JS and same-cookie reload. Two new workspaces were issued;
no feature writes or model calls were made. Screenshots were visually inspected.
The action confirmation disclosure was checked in the served DOM and through the
local/hosted confirmed-hold browser journey; no new live stock-action journey or
real-model extraction is claimed. Desktop expiry is visibly
checked; the existing hidden mobile expiry is still an open usability item.

The broader UI audit/layout correction remains open. This increment does not
claim a full usability study, persistent accounts, live inventory integrations,
new model-quality evidence or closure of the U18 limitations.

Private source/configuration, failed checks, runtime/archive/build and live browser
receipts are retained in ignored `.local/evaluation-workspace-copy/`. The earlier
wording-only preparation was preserved when the owner added the rate change; it
was not deployed. Independent final cloud readback confirmed the exact source/image at 100% traffic,
the sole 4-to-30 runtime change and unchanged IAM/resources. The migration retained
29 cumulative sessions and every window field; 31 were observed after the two
fresh browser workspaces. Model accounting remained 16 attempts and zero reserved
before/after this release. The independent reviewer created no sessions, feature
records or model calls.
