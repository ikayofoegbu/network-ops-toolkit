# Security and release review

Review date: November 4, 2026 (America/Edmonton).

## Decision and remaining gate

No publication-blocking secret, infrastructure disclosure or ownership conflict
was found in the reviewed material. The original repository can be released
after the owner approves a license and the release documentation passes CI.
The repository remains private while that decision is pending. MIT is proposed;
no license has been applied by this review.

## Scope and method

Baseline main: `e55263fe044ef4a2fbbf093897093ce215179b30`.

- Enumerated all five returned Git refs: main, both feature branches, and the
  two pull-request head refs. Every ref points into the reviewed commit graph.
- Traversed all nine commits to the root; every parent is present. Fetched all
  seven distinct recursive trees without truncation and all 37 unique blobs,
  including superseded/deleted file versions. Recomputed each Git blob SHA;
  all matched GitHub. Current main contains 28 files.
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
| Dependencies | No third-party runtime dependencies. Build backend is `setuptools>=68`; its lower bound is not a reproducibility lock. Python/OpenSSL and trust behavior vary by environment. |
| Actions | Six-job Ubuntu/Windows, Python 3.11–3.13 matrix; read-only contents permission, checkout credentials not persisted, actions pinned by full commit SHA, ten-minute job timeout. No deployment or secret consumption in the workflow. |
| Documentation | Corrected unsupported macOS claim, stale M4 branch instructions and obsolete release prohibition; added a safe offline-first quick start and current review evidence. |
| Repository | Private, main default, no releases, wiki disabled, Pages absent. No unrelated repository settings changed. |

Branch-protection API access was denied to the integration. Rulesets API access
was unavailable for the current private repository plan. Neither is represented
as an independently verified enforcement control.

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

The older verification record preserves milestone-time evidence. Its historical
pending statements are superseded by the newer dated records and linked CI.

## Limits and publication checklist

macOS and IPv6 TLS integration are unverified. The tool does not establish HTTP
or application health, certificate revocation, an unobserved root cause, or a
complete security assessment. DNS and trust-store loading are outside the
per-phase socket timeout. Windows presentation rehearsal remains owner work.

Before public release:

1. Obtain owner approval for MIT (copyright 2026 Ikechukwu Ofoegbu), then add the
   standard license and package license metadata.
2. Update release status wording, run CI on the final release commit and review
   the result. Preserve historical PR/commit records.
3. Change visibility only for this repository; pin it and add its working link
   to the profile README.
4. Check repository, README, source and documentation without authentication,
   then reconfirm unrelated repositories remain private.
