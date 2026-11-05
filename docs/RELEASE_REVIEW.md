# Security and release review

Review date: November 4, 2026 (America/Edmonton).

## Decision

The reachable-history review found no publication-blocking credentials or
infrastructure disclosures. The project is MIT licensed, with standard license
text and SPDX package metadata. The licensed release passed all six CI jobs.
The repository is public,
pinned on the profile, and anonymously accessible; see the completion record below.

## Scope and method

Baseline main: `e55263fe044ef4a2fbbf093897093ce215179b30`.

- Enumerated all five returned Git refs: main, both feature branches, and the
  two pull-request head refs. Every ref points into the reviewed commit graph.
- Traversed all nine commits to the root; every parent is present. Fetched all
  seven distinct recursive trees without truncation and all 37 unique blobs,
  including superseded/deleted file versions. Recomputed each Git blob SHA;
  all matched GitHub. The reviewed baseline contains 28 files.
- Reviewed Python source, tests, examples, documentation, package metadata,
  workflow configuration and historical changes. Searched all historical blobs
  for common token formats, credential assignments, PEM keys, email addresses,
  IP literals, hostnames and disclosure/ownership indicators.
- Reviewed both PR descriptions and issue metadata (no issue comments), current
  repository metadata/settings, and all six decoded logs from the latest
  baseline-main CI run.

This is a review of reachable repository history, not just a scan of current
files. It cannot enumerate GitHub's unreachable retained objects, prove that a
test key was never reused elsewhere, or establish the origin of every line from
code inspection alone. No history was rewritten, no evidence removed and no
credentials rotated.

## Findings

| Area | Result |
| --- | --- |
| Credentials | No common credential/token matches or credential assignments found. One private-key blob is the explicitly disclosed test fixture below. |
| Network data | IPv4 literals are loopback or documentation addresses; IPv6 examples use `2001:db8::/32`. Names are localhost, reserved/example names or public documentation/project URLs. No employer/customer topology or production configuration found. |
| Ownership | History and documentation describe an independent, AI-assisted personal portfolio project. No third-party copyright headers, vendored packages or conflicting license notices found. This is not a legal provenance guarantee. |
| Dependencies | No third-party runtime dependencies. Build backend is `setuptools>=77.0.3` (raised for SPDX metadata support); its lower bound is not a reproducibility lock. Python/OpenSSL and trust behavior vary by environment. |
| Actions | Six-job Ubuntu/Windows, Python 3.11–3.13 matrix; read-only contents permission, checkout credentials not persisted, actions pinned by full commit SHA, ten-minute job timeout. No deployment or secret consumption in the workflow. |
| Documentation | Corrected unsupported macOS claim, stale M4 branch instructions and obsolete release prohibition; added a safe offline-first quick start and current review evidence. |
| Repository at audit time | Private, main default, no releases, wiki disabled, Pages absent. |

## Disposable TLS fixture exception

`tests/fixtures/tls/localhost-test-key.pem` matches the public key in
`localhost.pem`. The leaf subject is `CN=localhost`, with SANs `localhost` and
`127.0.0.1`, issued by `CN=NetOps Disposable Test CA`. Both certificates are valid
January 1, 2020 through January 1, 2040. The leaf is not a CA. OpenSSL verified
its chain and localhost hostname against the fixture CA.

Leaf certificate SHA-256 fingerprint:
`C4:BA:AA:60:98:06:69:04:01:2A:49:BB:94:EB:26:C4:54:3C:E3:CF:9C:9C:02:BC:6D:3A:86:D8:E7:9F:EE:91`.

The fixture README documents intentional disclosure. Only the leaf test key is
present in the reviewed history; the CA signing key is absent. Its destruction
is documented by the project, not independently provable. Test listeners bind
only to `127.0.0.1`; clients load the CA into individual SSL contexts without
modifying OS trust. Certificate and hostname validation remain enabled.

These facts support public distribution as disposable test material. Never use
this key for a real service or install the CA into system trust. A secret scanner
may correctly flag its deliberate presence; do not use a blanket PEM exclusion.

## Executed validation

- Fresh local virtual environment: editable installation succeeded on Python
  3.12.14, Linux. `pip check` passed.
- All 58 unit and loopback integration tests passed. Real socket tests stayed on
  loopback; no external probe was executed.
- Source/test/example compilation, module demo, installed CLI demo, all three
  synthetic cases, JSON parsing and relative Markdown link checks passed.
- Baseline-main [CI run 40431342310](https://github.com/ikayofoegbu/network-ops-toolkit/actions/runs/40431342310)
  passed all six jobs, 58 tests per job. All six decoded job logs were inspected.
  These are results for the baseline commit, not a claim about later commits.

The [verification record](VERIFICATION.md) consolidates the release checks and
historical milestone results.

## Limits

macOS and IPv6 TLS integration are unverified. The tool does not establish HTTP
or application health, certificate revocation, an unobserved root cause, or a
complete security assessment. DNS and trust-store loading are outside the
per-phase socket timeout.

## Publication completion

Completed November 4, 2026 (America/Edmonton).

- GitHub recognizes the MIT license; the built wheel includes
  LICENSE and SPDX license metadata.
- Licensed release commit: `c0c5f932fde1907a50d83121a27936641195d18b`.
  [Release CI](https://github.com/ikayofoegbu/network-ops-toolkit/actions/runs/41928155607):
  all six Windows/Linux Python 3.11–3.13 jobs passed, 58 tests each; decoded
  logs were inspected. Local installation, 58 tests, dependency checks,
  installed demos, example JSON, wheel packaging and Markdown links passed.
- Retrieved and checked 84 job logs across all 14 workflow runs available before
  publication. No matches for the checked common token/private-key patterns were
  found in those logs. This automated log scan is not a guarantee that every
  possible secret format would be detected.
- The repository was published with its reviewed commit history preserved.
- Toolkit pinned to the profile. The profile README now links to the source,
  engineering case study and troubleshooting examples.
- Requests with no authentication or cookies returned HTTP 200 for the profile,
  repository, README, Python source, troubleshooting documentation and LICENSE.
- This completion record is a documentation update after the licensed release;
  the linked run above tests the licensed release commit, not later commits.
