# GitHub repository settings — owner action and verification

**Repository:** [imrohitagrawal/batchbeacon-ai](https://github.com/imrohitagrawal/batchbeacon-ai) · **Owner:** `@imrohitagrawal` · **Live application:** [batchbeacon.stackclimb.com](https://batchbeacon.stackclimb.com).

This is a **configuration checklist, not an assertion that changes are already applied**. The product is a real deployed cloud application; the selected product labels and inventory actions are synthetic/simulated demonstration inputs and outcomes, not a mock backend. As observed at review time, GitHub's REST repository readback reports the stale description, blank homepage, no topics, unprotected `main` and no rulesets. The linked ChatGPT GitHub app can read repository settings and change source files/PRs but **does not expose administration write actions** to modify About, homepage, topics, social preview or branch rulesets. Committing this document cannot change those GitHub settings. Verify after applying using the public repository sidebar and GitHub Settings.

## 1. The right-side About panel

From [the repository home](https://github.com/imrohitagrawal/batchbeacon-ai), select the small **gear icon beside About** and set:

**Description (copy exactly):**

> Live AI retail recall investigation on Google Cloud Run: Gemini + Google ADK extraction, deterministic evidence checks, human-confirmed simulated holds and Firestore-backed cases. Singapore AI Builder Cup 2026.

**Website:**

`https://batchbeacon.stackclimb.com`

**Topics** (up to 20 supported by GitHub; enter one at a time):

`google-adk`, `gemini`, `vertex-ai`, `cloud-run`, `firestore`, `fastapi`, `python`, `retail-tech`, `food-recall`, `generative-ai`, `human-in-the-loop`, `cloud-monitoring`, `playwright`, `github-actions`.

**Important:** Topics are discovery labels, not validation of engineering capabilities. In particular, do **not** add `rag`, `multi-agent`, `firebase-auth`, `bigquery` or `production-sla` for the current release.

Check **Save changes**, then refresh the public home and confirm About text, website hyperlink and topics. GitHub About is a compact metadata sidebar; it cannot embed a live UI screenshot or host a full-length technology explainer. Put the richer detail in [README](../README.md), [showcase](SHOWCASE.md) and [technology evidence](submission/google-technology-evidence.md).

## 2. Social preview versus screenshots

GitHub's image shown when a **repository URL is shared** is its *social preview*, not an inline About image. Configure it at **Settings → General → Social preview → Edit → Upload image**.

Recommended image: branded **1280 × 640 PNG or JPG under 1 MB**, with BatchBeacon AI wordmark, package → AI extraction → deterministic verification → human confirmation → saved queue. Use an approved/cleared public screenshot only if its private guest/session identifiers are removed and the verified release is identified correctly. Do not imply that a conceptual diagram is a live UI screenshot. Social preview does **not** replace README screenshots.

The README currently embeds four explicitly-labelled **older reviewed UI candidate** images; the [submitted video](https://youtu.be/IpY2_GeR4Ic) is the actual released-system footage. To display screenshots accurately labeled **live**, a browser capture of the accepted deployed app and a privacy/provenance check are required before committing new image bytes.

## 3. Owner-only merges to main

**Recommended strongest simple policy:** Keep this repository under the personal owner account `@imrohitagrawal`; invite teammates as **read-only/fork-based contributors** where possible. They can fork, propose changes and discuss pull requests without any direct merge permission. Do not give any other collaborator **Admin** or **Maintain** privileges.

To allow write-access feature branches but block teammates from merges:

1. Open [Settings → Rules → Rulesets](https://github.com/imrohitagrawal/batchbeacon-ai/settings/rules) → **New branch ruleset**.
2. Name it `main-owner-only`, set **Active**, include the default branch (`main`), and enable **Restrict updates** + **Restrict deletions** + **Block force pushes**.
3. In **Bypass list**, grant only **Repository administrators** (which at present should be owner only) with **For pull requests only**. Do **not** grant bypass to Write/Maintain roles, other collaborators or deployment bots. Verify no other administrator has access. A rule's bypass set describes classes of actors; GitHub cannot distinguish two administrators merely by your CODEOWNERS file.
4. Add another active ruleset, `main-quality-gates`, targeted at `main`, requiring a PR, resolved threads and the proven CI job `local-contracts`; **do not add a bypass** to that quality ruleset. Make sure the exact check appears and succeeds before enforcing it.
5. Enable review requirements only after considering GitHub's author-self-approval restriction and having a genuine separate reviewer. Requiring your own approval of **your own** PR is not a workable self-review policy. You can be the only merger while another teammate reviews.
6. Attempt a test PR from a non-admin collaborator account; confirm they can contribute/review but **cannot merge**. Ensure owner merges still require passing CI. Re-read [rulesets](https://github.com/imrohitagrawal/batchbeacon-ai/settings/rules) and [branch protection](https://github.com/imrohitagrawal/batchbeacon-ai/settings/branches) after saving.

`.github/CODEOWNERS` names an owner for review requests. It **does not** grant exclusive merge rights on its own; real restrictions require active server-side rules. If future maintainers are granted Admin, the class-based bypass expands to them: only the actual owner should retain admin access for the stated policy.

**Scope caution:** A policy that grants Admin a bypass for `Restrict updates` only "For pull requests" must be tested in GitHub's merge UI. If GitHub's plan/repository controls do not offer that exact mode, use fork-only contributions or a ruleset granting the only available owner/admin role, then verify the effective actor rights instead of asserting an untested guarantee.

## 4. Professional repository presentation

| Item | Desired state | Presently verifiable |
| --- | --- | --- |
| README and screenshots | Clear problem, live URL/video, visual gallery, current-vs-planned, architecture, evidence | Source-controlled updates, see [README](../README.md) |
| About/website/topics | Exact compact description + working website + accurate technology classification | **Manual GitHub settings action; unverified until readback changes** |
| Social preview | Branded PNG/JPG, appropriate size, privacy checked | **Manual GitHub settings action** |
| CODEOWNERS / governance | Named owner, PR template, contributor/security guidance | Source-controlled file; **does not protect main by itself** |
| Branch rules | Only owner/admin can update `main` via PR; checks enforced; no force push | **Manual settings action; unverified until readback** |
| Version/license | No implied open source or production releases; license decided by owner | No root software license granted; do not assume one |
| Provenance | Distinguish image/video sources, tests, deployment revision and future product plans | [Showcase](SHOWCASE.md), [evidence](submission/evidence-index.md) |

**After applying settings**, compare the public GitHub sidebar and rulesets to this checklist; a green GitHub Action or merged PR does not imply that About metadata or permissions changed.
