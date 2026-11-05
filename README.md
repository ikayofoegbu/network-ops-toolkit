# Network Operations & Troubleshooting Toolkit

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](https://www.python.org/)

**Independent engineering portfolio project · [MIT licensed](LICENSE)**

A Python command-line toolkit for **single-host DNS and TCP diagnostics with optional validated direct TLS**. It records connection outcomes by address and produces readable or JSON reports with practical troubleshooting checks.

## What it does

- Resolves a supplied hostname to IPv4 and IPv6 addresses.
- Attempts a single TCP port on up to **8 distinct resolved addresses** (no port ranges or network scanning).
- Distinguishes TCP connected, refused, timeout, unreachable and local permission errors where the OS exposes these distinctions.
- Optionally validates a direct TLS handshake on the same TCP connection, preserving certificate, hostname, timeout and handshake outcomes.
- Produces readable reports or structured JSON with observations and suggested next checks.
- Includes offline examples, unit tests and five TCP/TLS loopback integration tests.
- Tested in CI on Windows and Linux with Python 3.11–3.13 and **no third-party runtime dependencies**.

## Quick start

Install Python 3.11+ and Git, then obtain the source:

```text
git clone https://github.com/ikayofoegbu/network-ops-toolkit.git
cd network-ops-toolkit
```

From the repository root, on Windows PowerShell (no activation or execution-policy changes required):

```powershell
py -3 -m venv .venv
& .\.venv\Scripts\python.exe -m pip install -e .
& .\.venv\Scripts\python.exe -m netops demo
& .\.venv\Scripts\python.exe -m netops demo --json
```

On Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python -m netops demo
python -m netops demo --json
```

The demo is synthetic and **does not access the network**. Installation downloads build tooling if needed; the package itself has no third-party runtime dependencies. Probe only an endpoint you control or are authorized to test:

```text
python -m netops probe --host YOUR_AUTHORIZED_HOST --port 443 --timeout 2 --tls --json
```

On Windows without activation, replace `python` with `& .\.venv\Scripts\python.exe` in subsequent commands. Replace `YOUR_AUTHORIZED_HOST` with a hostname or IP address, not a URL. Real results vary by system, DNS, endpoint and policy. A failed real probe returns exit code `1`; input/usage errors return `2`; TCP connectivity established returns `0`. When `--tls` is requested, exit `0` requires at least one validated TLS handshake; TCP success alone is insufficient.

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
HTTP requests and application health checks are outside the current scope.

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

## Run the test suite

```powershell
python -m unittest discover -s tests -v
```

The suite contains **58 tests**. Unit tests cover controlled DNS, TCP and TLS outcomes. Integration tests use temporary listeners on `127.0.0.1` for real TCP connections and TLS handshakes, including certificate validation, hostname mismatch, untrusted certificates and handshake timeout. The test CA is loaded into individual SSL contexts.

GitHub Actions tests Python 3.11, 3.12 and 3.13 on Windows and Linux. All six jobs in the [release verification run](https://github.com/ikayofoegbu/network-ops-toolkit/actions/runs/41929088813) passed with 58 tests each. See the [verification record](docs/VERIFICATION.md) for commands, coverage and milestone results.

## Troubleshooting examples

Three reproducible examples cover DNS failure, TCP refusal, and TCP success followed by TLS certificate validation failure. They use simulated observations through the same report-generation path as the live probe and send no network traffic.

```text
python examples/troubleshooting_cases.py all
python examples/troubleshooting_cases.py tls-failure --json
```

The example renderer returns `0` after successfully printing a report. The live probe uses the connectivity exit codes described above.

Read the [case walkthroughs](docs/TROUBLESHOOTING_CASES.md), [engineering case study](docs/ENGINEERING_CASE_STUDY.md) and [Windows walkthrough](docs/WINDOWS_DEMO.md).

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

## Documentation

- [Engineering case study](docs/ENGINEERING_CASE_STUDY.md): architecture, design decisions and the Windows TLS fixture fix.
- [Troubleshooting cases](docs/TROUBLESHOOTING_CASES.md): interpreting DNS, TCP and TLS results.
- [Windows walkthrough](docs/WINDOWS_DEMO.md): installation, tests and example commands.
- [Verification record](docs/VERIFICATION.md): automated and local validation evidence.
- [Security and release review](docs/RELEASE_REVIEW.md): history review, dependency checks and disposable TLS fixtures.

## Supported scope

The toolkit reports DNS resolution, TCP connectivity and optional direct TLS validation. HTTP, STARTTLS and certificate revocation checks are outside its scope. Windows and Linux are covered by CI; macOS execution and IPv6 TLS integration are outside the current test matrix. DNS and trust-store loading follow the host environment's timing and configuration.

## Project and license

Independent engineering project by Ikay Ofoegbu, developed with AI assistance. Released under the [MIT license](LICENSE).
