# BatchBeacon AI: competitive narration v4

Packaging draft. The public prototype and real-AI journey are verified; final exported video and media link remain pending. Actual label → Gemini/ADK → deterministic check → explicit simulated hold → Firestore queue narrative preserved. Original v3c source and audio are unchanged.

## Submission — 230 seconds

### 0–20s: The retail problem

Official recall notices describe products, batches, dates and markets. A retail worker still has to connect those conditions to the package in hand. BatchBeacon makes that investigation inspectable, from the label photo to a deliberate simulated action that the next person can resume.

### 20–50s: Actual AI extraction

We begin with a synthetic Singapore example. The application runs on Google Cloud Run. One bounded Google ADK workflow asks Gemini to read the label and propose structured fields. The label remains visible beside the result, so the person can inspect what the model read. This is actual model extraction, not a fixture response.

### 50–80s: Deterministic comparison

The server checks product identity before lot, date and jurisdiction. A familiar lot number cannot override a different product. The comparison keeps the selected source conditions visible. Missing, stale or unsupported evidence stays in review. A recall match does not establish whether a product is safe to consume, and a negative does not grant permission to sell.

### 80–110s: Explicit action and persistence

The historical SFA conditions support this demonstrated match. The person reviews the evidence, checks the confirmation and chooses a simulated hold. Firestore saves the action. We refresh and reopen the same case in the owned queue. The evidence and decision remain connected. No real inventory changes, and the model cannot approve that action on its own.

### 110–135s: Two workspaces

The retail console serves staff and demo managers with owned status counts, missing evidence, resumable cases, actions and capture guidance. Private BatchBeacon Operations serves the operator with verified deployment resources, monitoring configuration, alert policies and bounded cost oversight. Technical privileges stay outside guest access. A future public Recall Explorer serves consumers; business insights remain permissioned.

### 135–160s: Source uncertainty

When source conditions change, the decision needs renewed review. The UK FSA parent notice and its company attachment remain separate because their conditions differ. UK matching stays review-only. This keeps the disagreement visible instead of turning an uncertain interpretation into a confident action. Attachment extraction is future work.

### 160–185s: Bounded adaptation

Guidance adaptation changes only allowlisted wording. Six cases and nine variants support fixed evaluation. Actual deployed activation and rollback have now been verified. A person confirms activation, and rollback restores earlier content at a newer revision. This improves capture guidance without changing deterministic decision rules.

### 185–210s: Technical evidence

One Cloud Run application connects managed Gemini through ADK with Firestore and private image storage. The demonstrated SFA journey includes actual extraction, confirmation and persistence. Engineering coverage includes thirteen hundred and thirty-five unit checks and seventy hosted browser checks. These checks are not model-accuracy percentages or a completed protected quality evaluation.

### 210–230s: Vision and pilot

Retail workflow comes first. A public Consumer Recall Explorer, product images from official notices, and permissioned business insights remain future work. A proposed pilot measures review time, unsupported actions and evidence completeness. Clearer information connects producers, sellers, authorities and citizens, with sources and human decisions visible.

## Alternative — 160 seconds

### 0–15s: Retail problem

A recall notice describes affected products and conditions. Retail staff must connect those details to the exact package in hand. BatchBeacon makes that investigation visible and resumable, using synthetic labels and simulated actions.

### 15–40s: Actual AI

Here, one bounded Google ADK workflow asks Gemini to read the label. The Cloud Run application retains the image beside the proposed fields. Deterministic server rules compare identity before lot, date and jurisdiction. Missing or unsupported evidence stays in review. The model does not decide that a product is safe.

### 40–65s: Human action and queue

The historical SFA conditions support this match. The person inspects the comparison, explicitly confirms and records a simulated hold. Firestore saves the action. After refresh, we reopen the same investigation in the owned queue. No real stock changes, and the model cannot approve an action on its own.

### 65–85s: Two workspaces

Retail staff and demo managers use the owned queue, status counts, evidence and guidance. Private Operations gives the operator verified deployment, monitoring and cost oversight. Technical privileges remain outside guest access. A public consumer Explorer and permissioned business insights are future work.

### 85–105s: Uncertainty

Changed source conditions require renewed review. The UK FSA notice and company attachment remain separate, and UK matching stays review-only. A scoped no-match is never food-safety clearance. Attachment extraction remains future work.

### 105–125s: Guidance and evidence

Guidance changes only approved wording after fixed evaluation and explicit activation. Six cases and nine variants support verified deployed activation and rollback. Engineering coverage includes thirteen hundred and thirty-five unit checks and seventy hosted browser checks. These are not model-accuracy results.

### 125–145s: Architecture

One Cloud Run application uses Gemini and ADK for extraction, deterministic server rules for decisions, Firestore for owned records and private storage for images. Existing scanning and alert tools set the baseline. Our focus is the inspectable path from evidence to a human-confirmed action.

### 145–160s: Future benefit

Future work includes a public Consumer Recall Explorer, images from official notices, and permissioned business insights. A pilot would measure review time, unsupported actions and evidence quality. Adoption and harm reduction remain unmeasured.

## Validation and remaining media work

Both new cuts measure exactly 230.000/160.000 seconds at 48 kHz mono PCM. Every complete spoken segment fits before its reserved pause; no speech was truncated. Peak level is -1.8 dBFS in each cut. Local tempo correction applies only to two submission scenes and remains below the admitted 1.2 ceiling. Listening/pronunciation review is pending: no actual audio playback feedback was available in this file-generation route. Actual visual evidence, public hosting and fresh playback validation remain required. Engineering counts are bound to successful exact-head hosted run 39130978886 (1,335 unit, 70 browser; HEAD 48c15250c76f7b5adf3cea673384d3be0007661e).
