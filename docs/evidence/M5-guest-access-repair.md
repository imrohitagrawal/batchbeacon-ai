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

Implementation and verification are in progress; no repaired deployment is claimed
yet. Original live diagnosis and private repair receipts are retained in ignored
`.local/mobile-guest-diagnosis/` and `.local/guest-access-repair/`. Failed checks
remain preserved. This repair does not complete the unrelated evaluation,
source-review or Operations gates disclosed in STATE.
