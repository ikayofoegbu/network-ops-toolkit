# Network Operations & Troubleshooting Toolkit

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](https://www.python.org/)

**Status: private development candidate. Public release is not authorized.**

An independent engineering portfolio project that turns narrow, reproducible network observations into evidence-driven troubleshooting reports. First milestone: **single-host DNS resolution and TCP connectivity diagnostics**.

## What it does

- Resolves a supplied hostname to IPv4 and IPv6 addresses.
- Attempts a single TCP port on up to **8 distinct resolved addresses** (no port ranges or network scanning).
- Distinguishes TCP connected, refused, timeout, unreachable and local permission errors where the OS exposes these distinctions.
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

The demo is synthetic and **does not access the network**. Real probe results vary by system, DNS, endpoint and policy. A failed real probe returns exit code `1`; input/usage errors return `2`; TCP connectivity established returns `0`.

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

## How to interpret the result

| Observation | What is known | What is **not** established |
| --- | --- | --- |
| DNS failed | Local name resolution failed | Whether the hostname is down or DNS is misconfigured |
| TCP connected | One TCP handshake completed | Whether TLS, HTTP or the application works |
| TCP refused | A connection was refused | Whether refusal originated at the host or an intermediary |
| TCP timeout | A connection attempt timed out | Whether firewall, routing, endpoint or another cause is responsible |
| Network unreachable | OS reported an unreachable network/host | Which upstream device/path caused the issue |

**Dual-stack caution:** all individual address attempts appear in the report. A success on one address does not erase failures on another. `--timeout` is *per address*, not a whole-run deadline; the probe attempts at most 8 resolved addresses. DNS itself is subject to the system resolver's timing, not this TCP timeout.

## Reproduce tests with no external network probes

```powershell
python -m unittest discover -s tests -v
```

Unit tests inject fake DNS and TCP dependencies and **do not send packets**. A separate test creates a temporary listener on `127.0.0.1` to verify a real local TCP handshake; it does not contact external systems. GitHub Actions is **configured** to test Python 3.11–3.13 on Linux and Windows; the initial GitHub Actions run passed all six jobs ([evidence](https://github.com/ikayofoegbu/network-ops-toolkit/actions/runs/40427289295)). Any future external-network integration tests must be separately approved and run only against systems you control or are authorized to test.

## Repository structure

```text
src/netops/diagnostics.py  single-target DNS/TCP observations and cautious interpretations
src/netops/cli.py          argument validation, text/JSON output and exit codes
src/netops/__main__.py     python -m netops entry point
tests/                    deterministic offline regression tests
examples/demo-report.json reproducible JSON output from the synthetic demo
.github/workflows/ci.yml cross-platform automated checks
```

## Privacy and safety

Do not put employer IP ranges, production hostnames, credentials, troubleshooting exports or operational topology in this repo. No logging, telemetry, persistent storage or external API calls are included. Real probes initiate the specific TCP connection you requested, and should only be used where you have authorization. Run the `demo` command if you only want to inspect output without network activity.

## Roadmap and release gate

- **M1:** single-target diagnostics, 29 unit/loopback tests, documentation and synthetic demo. Windows installation and local tests confirmed by the owner.
- **M2 (current):** private GitHub integration and automated verification on Python 3.11–3.13 across Windows and Linux. The initial six-job matrix passed; see [verification evidence](docs/VERIFICATION.md).
- **M3 (proposal only):** define a small next diagnostic capability and its acceptance criteria after reviewing M2 results. No implementation is authorized.

Before making this repository **public**: review all code and git history for sensitive material; choose a license; confirm the documentation and sample output; run CI; and make the owner approval decision. A passing test suite does not prove cross-network connectivity in every environment.

This is an original personal portfolio project, not an employer deliverable and not part of Follyhouse Studios or Tell On Yourself.
