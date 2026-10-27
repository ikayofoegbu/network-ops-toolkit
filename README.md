# Network Operations & Troubleshooting Toolkit

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](https://www.python.org/)

**Status: private development candidate. Public release is not authorized.**

An independent engineering portfolio project that turns narrow, reproducible network observations into evidence-driven troubleshooting reports. Current scope: **single-host DNS/TCP diagnostics with optional validated direct TLS**.

## What it does

- Resolves a supplied hostname to IPv4 and IPv6 addresses.
- Attempts a single TCP port on up to **8 distinct resolved addresses** (no port ranges or network scanning).
- Distinguishes TCP connected, refused, timeout, unreachable and local permission errors where the OS exposes these distinctions.
- Optionally validates a direct TLS handshake on the same TCP connection, preserving certificate, hostname, timeout and handshake outcomes.
- Prints a readable report or structured JSON with suggested **next checks**, not invented root causes.
- Includes a no-network synthetic demo, offline unit tests and a controlled local-only loopback integration test.
- Runs on Windows, macOS and Linux with Python 3.11+ and **no third-party runtime dependencies**.

## Quick start

From the repository root, on Windows PowerShell:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
python -m netops demo
python -m netops probe --host example.com --port 443 --timeout 2
python -m netops probe --host example.com --port 443 --json
```

On macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python -m netops demo
python -m netops probe --host example.com --port 443 --timeout 2
```

The demo is synthetic and **does not access the network**. Real probe results vary by system, DNS, endpoint and policy. A failed real probe returns exit code `1`; input/usage errors return `2`; TCP connectivity established returns `0`. When `--tls` is requested, exit `0` requires at least one validated TLS handshake; TCP success alone is insufficient.

### Synthetic demonstration

```text
NETWORK OPS TOOLKIT — CONNECTIVITY REPORT
[SYNTHETIC DEMO — NO NETWORK TRAFFIC]
Target: demo.example:443
DNS: resolved
  Resolved: 192.0.2.10 (IPv4)
TCP: connected
  192.0.2.10 (IPv4): connected in 12.40 ms
Assessment: tcp_connected
At least one TCP handshake succeeded. Application health was not tested.
Suggested next checks:
  - If the application still fails, check TLS and application-layer responses.
```

`192.0.2.10` is a documentation-only address; the demo's successful result is entirely simulated.

## Optional TLS diagnostic

Use `netops probe --host HOST --port PORT --tls --json` only against a system you
control or are authorized to test. Direct TLS services are supported; STARTTLS,
HTTP requests and application health checks are outside this milestone.

Certificate chain and hostname validation stay enabled using Python's default
client context and system trust. There is no insecure mode or automatic retry
with verification disabled. A trailing DNS dot is removed for certificate name
validation while the requested target remains in the report.

A successful TCP handshake can coexist with `tls_failed`. Individual attempts
record `validated`, `certificate_invalid`, `hostname_mismatch`, `timeout`,
`handshake_failed`, `socket_error` or `not_run`. OpenSSL verification codes and
messages are retained for certificate errors. A name mismatch may be masked by
an earlier trust failure; this tool reports the error observed, not every possible
certificate problem. One validated address does not erase failures on others.

TCP-only reports and the synthetic demo retain schema version 1. TLS opt-in
reports use schema version 2, adding a top-level TLS summary and per-address TLS
observations. Schema 2 uses `target.timeout_per_phase_seconds`: `--timeout`
applies separately to each TCP connect and its TLS handshake. Total socket time
may approach twice that value per address, up to 8 addresses. DNS and trust-store
loading do not have a timeout imposed by this tool. TCP and TLS elapsed times
are recorded separately. TLS validation does not establish application health,
certificate revocation status, or a complete security assessment.

## How to interpret the result

| Observation | What is known | What is **not** established |
| --- | --- | --- |
| DNS failed | Local name resolution failed | Whether the hostname is down or DNS is misconfigured |
| TCP connected | One TCP handshake completed | Whether TLS, HTTP or the application works |
| TLS validated | A TLS handshake passed configured trust and hostname checks | Whether the application works or all addresses passed |
| TLS failed after TCP connected | TCP worked; TLS did not pass validation | A proven routing, firewall or service root cause |
| TCP refused | A connection was refused | Whether refusal originated at the host or an intermediary |
| TCP timeout | A connection attempt timed out | Whether firewall, routing, endpoint or another cause is responsible |
| Network unreachable | OS reported an unreachable network/host | Which upstream device/path caused the issue |

**Dual-stack caution:** all individual address attempts appear in the report. A success on one address does not erase failures on another. `--timeout` is per TCP connect and, when enabled, per TLS handshake, not a whole-run deadline; the probe attempts at most 8 resolved addresses. DNS itself is subject to the system resolver's timing, not this TCP timeout.

## Reproduce tests with no external network probes

```powershell
python -m unittest discover -s tests -v
```

Unit tests inject fake DNS and TCP dependencies and **do not send packets**. Local integration tests create temporary listeners on `127.0.0.1` to verify real TCP and TLS behavior, including trusted TLS, hostname mismatch, untrusted certificate and handshake timeout. They do not contact external systems. TLS fixtures are disposable test material; their CA is trusted only inside individual test contexts. The test suite currently contains 54 tests. GitHub Actions is **configured** to test Python 3.11–3.13 on Linux and Windows; the initial GitHub Actions run passed all six jobs ([evidence](https://github.com/ikayofoegbu/network-ops-toolkit/actions/runs/40427289295)). Any future external-network integration tests must be separately approved and run only against systems you control or are authorized to test.

## Repository structure

```text
src/netops/diagnostics.py  single-target DNS/TCP observations and cautious interpretations
src/netops/cli.py          argument validation, text/JSON output and exit codes
src/netops/tls.py          validated TLS observations and cautious interpretation
src/netops/__main__.py     python -m netops entry point
tests/                    mocked unit tests and local TCP/TLS integration tests
tests/fixtures/tls/        explicitly disposable TLS test certificates and key
examples/demo-report.json reproducible JSON output from the synthetic demo
.github/workflows/ci.yml cross-platform automated checks
```

## Privacy and safety

Do not put employer IP ranges, production hostnames, credentials, troubleshooting exports or operational topology in this repo. No application logging, telemetry, persistent result storage or external API calls are included. Python SSL configuration, including SSLKEYLOGFILE when set by the operator, remains subject to Python standard-library behavior. Real probes initiate the specific TCP connection you requested, and should only be used where you have authorization. Run the `demo` command if you only want to inspect output without network activity.

## Roadmap and release gate

- **M1:** single-target diagnostics, 29 unit/loopback tests, documentation and synthetic demo. Windows installation and local tests confirmed by the owner.
- **M2 (current):** private GitHub integration and automated verification on Python 3.11–3.13 across Windows and Linux. The initial six-job matrix passed; see [verification evidence](docs/VERIFICATION.md).
- **M3 (integrated):** optional validated direct TLS diagnostics, mocked failures and controlled loopback integration tests. [PR #1](https://github.com/ikayofoegbu/network-ops-toolkit/pull/1) merged after owner approval; all six [post-merge CI jobs](https://github.com/ikayofoegbu/network-ops-toolkit/actions/runs/40429821370) passed with 54 tests per job.

Before making this repository **public**: review all code and git history for sensitive material; choose a license; confirm the documentation and sample output; run CI; and make the owner approval decision. A passing test suite does not prove cross-network connectivity in every environment.

This is an original personal portfolio project, not an employer deliverable and not part of Follyhouse Studios or Tell On Yourself.

