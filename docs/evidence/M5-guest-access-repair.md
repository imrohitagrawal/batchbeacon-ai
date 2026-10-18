# Public guest-access correction

Owner U23 authorizes this critical repair. The public application exhausted all
22 lifetime guest issuances. A fresh browser reproduced guest POST429 followed
by queue/learning GET401 without receiving a guest cookie. This is a required
judge-access correction under AC-26/29/31, not a mobile-specific defect. The
mobile-only “Choose an example” link is an intentional shortcut at widths up to
760px and does not require a layout change.

## Accepted correction and gates

- Require an explicit `max_issued_sessions` setting. `null` means no lifetime
  count ceiling; positive integers retain the earlier capped behavior. Missing
  or malformed settings fail validation. No arbitrary large replacement cap.
- Preserve cumulative issuance, finite admission dates, the existing burst-rate
  limit, eight-hour guest expiry, ownership, CSRF, per-shop limits and every model
  budget/counter. Guest creation does not call Gemini.
- Bind the changed admission policy into the runtime/configuration hashes. Migrate
  only the stored admission policy hash with an update-time precondition; preserve
  all counters and timestamps. Old and new policy hashes must not be mixed across
  revisions serving traffic. Preserve the submitted image and migration receipt.
- On failed admission, navigation keeps the access explanation and avoids
  protected queue/guidance requests. The tour and previews remain available.
  Navigation during pending admission loads the selected view after success.
- Verify local unit/browser/edge checks, exact hosted push/PR commands and bootstrap,
  independent technical review, bounded image build and exact deployed readback.
  Verify fresh desktop/mobile shops and session isolation without paid model calls.

## Execution evidence

U23 is deployed and superseded by the UI-only U24 image below. Independent review
verified the smallest admission/configuration boundary, counter-preserving migration
and no model-policy change. U23 source `ec77b7e986879aae602e3ffa66bd78268d6ef97d`
passed 1,340 unit, 83 browser and 29 edge checks locally and in both
[hosted push](https://github.com/imrohitagrawal/batchbeacon-ai/actions/runs/39162623896)
and [hosted PR](https://github.com/imrohitagrawal/batchbeacon-ai/actions/runs/39162638109)
environments. [PR4](https://github.com/imrohitagrawal/batchbeacon-ai/pull/4) merged.
Fresh desktop/custom-host, phone/custom-host and phone/fallback shops succeeded
beyond the old 22 ceiling. Owned reads200, foreign reads404, guestless queue401,
secure cookie properties, queue/guidance loading and phone cookie reuse passed.
One synthetic incident was created; no extraction/model call was made.

Two initial image-packaging attempts failed because stale context/upload
allowlists omitted runtime configuration. Both failures are preserved. The
correction generates packaging boundaries from the final manifest, verifies the
actual gcloud upload selection, and performs the real Docker build plus both
unmounted/network-disabled image smokes before dispatch. The corrected U23 build
passed; these guards were reused and independently checked for U24. The bounded
repair build reserves total INR28 from existing contingency, not additional budget
or a claim of actual billed cost.

## U24 expiry and guidance clarity

The clock-only guest expiry now shows its local date, clock time and timezone;
eight-hour server expiry is unchanged. Explicit Refresh guidance records performs
one GET and reports completion after rendering. Failure retains its error and
historical-record notice. The page explains its purpose and workflow prerequisites.
It does not generate guidance or run an evaluation merely by refreshing.

Source `3dbb220b5263dc69dedb838872c04e029cc25639` is merged in
[PR6](https://github.com/imrohitagrawal/batchbeacon-ai/pull/6). Both exact
[push](https://github.com/imrohitagrawal/batchbeacon-ai/actions/runs/39164585032)
and [PR](https://github.com/imrohitagrawal/batchbeacon-ai/actions/runs/39164589588)
workflows passed 1,340 unit, 86 browser and 29 edge checks, including locked bootstrap,
checkout topology and actual hosted commands. Independent focused review verified
date rollover/timezones and refresh success/failure behaviour.

Local verification: 1,340 unit and 29 edge passed. The full local browser run had
73 passes and 13 setup errors because the internal disk could not create Chrome
temporary profiles. Exactly those 13 cases passed using an isolated external-drive
temporary directory; the original failure remains preserved. A new refresh test
initially hit the existing throttle because its fake clock had not advanced;
advancing by the configured interval fixed the test precondition and independent
rerun passed. Neither incident required weakening a product control.

The exact 61-file uploaded build archive matched the manifest and generation-bound
hash. The bounded cloud build and both image smokes passed. Current image:
`sha256:e66037177f71400e4c976383d1020dccb84bd760c986ea81d10c8ce12a7f25cc`.
Deployment retained the complete runtime unchanged from U23, including IAM,
resource limits, namespace, session duration and every ledger policy. U24 needed
no Firestore migration. Exact ready revision was promoted to 100% traffic.

Live U24 desktop/custom-host, phone/custom-host and phone/fallback checks reused
all three earlier cookies: date/timezone formatting, queue/guidance load, successful
refresh feedback, exact served HTML/JS, no horizontal overflow and no browser
errors passed. Expiry is visibly verified on desktop; the phone assertions inspect
DOM text because existing narrow-screen CSS hides the session label. Mobile expiry
visibility remains an explicit U25 usability item. Zero new guests, feature writes or model calls were made. Independent
cloud readback observed 25 cumulative guests, 14 model attempts and zero model
reservations, unchanged across this UI correction. These observations do not
attribute unrelated historical public sessions to our tests.

## Scope and outstanding work

A full usability audit was not completed by these functional and clarity repairs.
The owner's clutter report is captured in the separate
[focused audit and layout correction](../UI_USABILITY_PLAN.md). Expert inspection,
automated checks and actual human usability testing must remain distinct claims.
No new full real-AI journey, protected evaluation or Operations completion is
claimed; the unrelated U18 limits in STATE remain open.

Original live diagnosis, screenshots, failed checks, private configuration,
source/build/deployment receipts and independent readbacks remain in ignored
`.local/mobile-guest-diagnosis/` and `.local/guest-access-repair/`.
