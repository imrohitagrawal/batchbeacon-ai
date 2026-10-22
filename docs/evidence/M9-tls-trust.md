# TLS trust bundle correction

The locked certifi 2026.7.22 bundle contains the emSign ECC Root CA - G3 trust
anchor affected by [GHSA-6q48-6c7w-9gw2](https://github.com/certifi/python-certifi/security/advisories/GHSA-6q48-6c7w-9gw2).
The model HTTPX transport and Google Storage's Requests transport load this bundle.
Offline inspection reproduced that trust. No interception or credential exposure
was observed. The finding is a required correction to the application trust boundary.

The lock now selects published [certifi 2026.10.19](https://pypi.org/project/certifi/2026.10.19/).
The upstream advisory text names 2026.10.18; the normalized repository alert and
published PyPI release identify 2026.10.19. Artifact inspection verifies the actual
removal rather than relying on the version label alone.

Independent review verified the wheel against PyPI and lock hashes and every wheel
RECORD entry. The other 71 resolved packages are unchanged. Runtime code differs only
in the version string; no installation hooks were added. The sole certificate change
is removal of the affected root; no roots were added.

Two regression tests fail against the old installed bundle and pass with the patched
bundle. They inspect the installed model HTTP transport and Storage/Requests bundle,
and retain certificate and hostname verification. Full isolated unit suite: 1,383
passed. Browser, actual local Firestore, hosted push/PR and image/deployment checks
remain distinct evidence gates, recorded in the private release receipts.

This change does not modify prompts, timeouts, grants, model allowance or original
unknown liability. It does not resolve [M7's remaining real-model acceptance
gate](M7-judge-readiness.md). A changed lock alone does not patch the running image;
the tested image must be rebuilt and verified before the deployed correction is claimed.
