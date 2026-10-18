## Summary
<!-- Describe the outcome and why the change matters. -->

## Scope and evidence
- [ ] Shipped, planned and not-tested claims are distinguished.
- [ ] Behavior-changing assertions link to tests, retained evidence and the relevant source revision.
- [ ] Source jurisdiction, version, lot/identity and human-confirmation boundaries remain correct.
- [ ] Private cloud IDs, credentials, guest sessions and runtime policy files are excluded.

## Validation
<!-- List exact commands, workflow runs, expected failures and what was NOT exercised. -->
- [ ] `./scripts/check.sh` (or explain why not run)
- [ ] Browser checks when applicable
- [ ] Mermaid/Markdown links and any static SVG fallbacks remain synchronized
- [ ] Real-model, cloud, operational and model-quality gates are not inferred from local CI

## Release impact
- **Affected area:** documentation / offline code / deployment / model / public submission
- **Deployed commit/image changed?** yes / no
- **Cloud spend, source rights or external access changed?** yes / no
- **Owner review or approval required?** yes / no
- **Rollback/recovery path:** 

See [contributing guide](../CONTRIBUTING.md), [current scope](../docs/submission/release-scope.md), [architecture](../docs/submission/architecture.md) and [security policy](../SECURITY.md). A merged change is not proof of an accepted deployed release.
