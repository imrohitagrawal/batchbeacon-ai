# Untrusted extraction proposals — local preparation

Status: LOCAL/PREPARATION. This is a pure schema and translation boundary for the
later T10 workflow. No model, network, store, ledger, observation publication or
action is invoked. The existing operator probe and default application are unchanged.

## Behavior

The model-facing schema contains proposed source restrictions and label values.
It accepts no ownership IDs, hashes, approval, reviewed identity resolution,
provenance, currentness, verdict, action or budget authority. A strict policy
controls proposal/source bytes, string and collection sizes, nesting, quotes,
quote occurrences and capture count. Duplicate JSON keys and malformed inputs
fail with sanitized diagnostics; no field is silently repaired or truncated.

Source quotes resolve to character spans in the exact UTF-8 source representation
bound by the selected notice hash. A separately extracted/normalized representation
cannot stand in for those bytes without its own established lineage. Capture
indices and normalized boxes resolve only onto the server-selected capture tuple;
the original capture references and hashes remain in the report. This establishes
structural locations, not semantic support or proof of retained/owned image bytes.

Every proposed source product, typed identifier, predicate, applicability and
jurisdiction is compared with the reviewed manifest. Missing/extra products,
changed restrictions or geography, and UNKNOWN versus ALL/NOT_SPECIFIED remain
explicit disagreements. Product/predicate ordering does not change the comparison.
The candidate remains separate; reviewed values never replace bad inference.
Missing review or incomplete interpretation cannot yield reviewed agreement.
Recall-context review remains separate from existing predicate approval.

An immutable report keeps the proposal, translated label values, mandatory source
disposition/diagnostics, exact notice/review dependency, captures, schema, translator
and policy hashes together. Label transcription can succeed while source agreement
fails; consumers must retain that distinction and enforce it before publication.
The report is not an observation, approval, live extraction receipt or publish command.

Known text values must equal their raw transcription, preserving lot case, leading
zeros and typed product codes. Translator v1 permits only exact ISO dates or an
anchored two-digit numeric slash date with one unique valid interpretation across
DD/MM/YYYY and MM/DD/YYYY. The supplied ISO value must equal that interpretation.
Ambiguous, invalid-calendar, unsupported-format and contradictory known dates deny;
explicit UNKNOWN/AMBIGUOUS fields preserve raw text with no normalized value.
No locale, alias or fuzzy parsing is inferred.

The supported subset permits one identifier per kind on a source product or label.
The wider domain permits some additional combinations; those are not silently
claimed as supported here. Exact source-name/pack comparison is deliberately
conservative. The reviewed SFA first slice fits this subset.

## Independent acceptance and correction

T10P01–11 were derived independently before implementation. The following findings
were reproduced and corrected:

| Finding | Impact and classification | Correction and verification |
| --- | --- | --- |
| T10P-R01 | A proposal could claim a known normalized value contradicting its own raw text, including choosing an ambiguous date; REQUIRED_CONTRACT | Literal known text and versioned deterministic date normalization. All four regressions failed before correction and fail when the prior behavior is restored in memory. |
| T10P-R02 | Chained validation exceptions retained rejected input in standard tracebacks, contradicting the sanitized-exception contract; REQUIRED_CONTRACT | Raise the sanitized diagnostic after leaving the validation handler, retaining neither cause nor context. The payload-traceback regression failed before correction. |

Both failures were local. No real model, runtime false verdict or actual disclosure
was observed. The error-chain finding was initially advisory because no public
sink exists; primary classified the reproduced documented exception-contract
violation separately. Original failed outputs are preserved. Independent review
passed **80 focused cases and Ruff**; the separate reviewer performed 33 synthetic
adversarial probes before the final exception correction and independently
verified that correction and its negative control. Counts overlap. No remaining
reproduced blocker was found in this bounded preparation.

Final corrected local checks passed: lock/Ruff, **659 unit and 48 Chrome browser
tests**. [Hosted run 39088574766](https://github.com/imrohitagrawal/batchbeacon-ai/actions/runs/39088574766)
passed at `b011615474ba0207163a93ebb1bf54605fa5f288`: locked bootstrap, browser
installation, lock/Ruff, 659 unit and 48 Chromium checks. Complete logs and exact
checkout were inspected, and remote main was verified.
Acceptance, source hashes, original failures, negative controls and complete logs
remain in ignored local evidence. Counts overlap; focused cases are not additive
to the complete suite.

## Installed ADK compatibility follow-up

A separate test-local harness exercises the installed `LlmAgent → Gemini → Runner`
with mandatory mock HTTP transport and synthetic credentials. Socket connections
and credential discovery are forbidden. No production runner, agent/client factory,
request builder, endpoint or runtime prompt was added; the instruction is test-only.

Ten focused cases and Ruff passed independently. The actual HTTP request preserves
the exact UTF-8 source and both ordered PNG byte sequences/hashes. Effective endpoint/model,
timeout, output/thinking configuration and the closed proposal schema are checked
at that boundary. Logical and wire-schema hashes are equal for this installed SDK.
Instruction-like source stays in user data, with the system instruction, schema
and absent tools/cache unchanged. A mock cannot prove prompt-injection resistance.

Actual ADK events feed the synthetic proposal into the pure translator: complete
agreement, source disagreement and invalid output keep their respective outcomes.
Mock 429/503, MAX_TOKENS and token-bearing CONTINUATION responses cause at most
one generation request. Constructed clients close on the exercised success and
provider-failure paths; constructor-failure cleanup is not demonstrated. Truncated
responses check continuation behavior; this harness does not publish or accept
them as a runtime result. Full local lock/Ruff, **669 unit and 48 Chrome browser
tests** passed. [Hosted run 39089108195](https://github.com/imrohitagrawal/batchbeacon-ai/actions/runs/39089108195)
passed at `da0d3418a0d1c445eca508b9f8141221b16d1cd2`: locked bootstrap,
browser installation, lock/Ruff, 669 unit and 48 Chromium checks. Complete log
and exact checkout were inspected. This is the same bounded mock-transport scope.

Independent review reproduced **AW-R01 / REQUIRED_CONTRACT** in the initial test:
MAX_TOKENS alone did not exercise continuation, so enabling continuation still
passed that case. The corrected first response carries a continuation token and
then stops. Its independent negative control sends two requests and fails with
continuation enabled; current configuration sends one. This corrects test evidence;
no production defect was observed. Earlier outputs and the control log are retained.

These are SDK compatibility tests, not real inference, provider-side schema
acceptance, shared admission, durable output or owned evidence publication. A pure
application request builder and its prepared-input digest remain deferred; such a
digest must not be confused with the future final-wire dispatch binding.

## Original-source input preparation

Read-only discovery verified the approved SFA raw HTML capture against its
manifest hash. Its 109,097 UTF-8 bytes exceed the translator's local default
100,000-byte source ceiling. This is a fail-closed configuration mismatch for
that future input, not permission to truncate or rewrite the reviewed source.
All three approved synthetic label asset hashes match and fit the existing image
byte ceiling; at most two selected panels remain permitted per acquisition.

Independent acceptance review recommends a pure original-input preflight next,
before adding a callable application runner. Preparation must:

- Verify the exact original source bytes/hash and preserve the review revision.
  Select and bind one finite effective source limit consistently across input
  preparation, translation and its eventual consumer; test the exact limit and
  one byte over it. Never truncate to meet a byte or token limit.
- Keep source quote offsets relative to the exact decoded original, with repeated
  quotes and multibyte characters covered. Character and byte offsets differ.
- Supply source material independently of the reviewed product rules/expected
  verdicts; those remain the server's comparison authority after generation.
- Bind the ordered permitted capture IDs, actual retained bytes/hashes, media
  types and sizes. Sanitized bytes may differ from the approved asset; an asset
  hash cannot be reused for changed bytes. Reject duplicate/mismatched inputs.
- Bind source dependency, prompt/schema versions and effective non-secret policy
  in a prepared-input digest distinct from the eventual final-wire digest.
  Preparation alone establishes no dispatch, ownership or live provenance.
- Account for the complete eventual request, including instructions, schema,
  source, images and any history/tools. A byte ceiling is not a token or cost
  ceiling; counted and generated semantic content must agree.

Derived-text extraction is deferred unless necessary. It would require its own
original/derived hashes, derivation version/configuration, completeness evidence
and locator mapping. The present translator accepts original-source locations;
derived text cannot replace the original hash or impersonate its offsets.
No input-preflight implementation or real-model request is claimed by this plan.

## Remaining integration gates

T10 still requires the application-integrated ADK workflow with this schema and
effective configuration, then separately authorized real-provider evidence. Its
consumer must
bind the final wire source/image/configuration, shared reservation and single-use
dispatch claim; retain bounded original/redacted output and failed diagnostics;
enforce deadlines and usage reconciliation; check owned retained inputs and current
source dependencies; and apply source disagreement before evidence publication.

Quotes and boxes still require substantive source/visual support evaluation. No
actual-model extraction accuracy, real-service sign-off, T08 admission, human UK/
new-context review, protected validation, runtime UI or release completion follows.
