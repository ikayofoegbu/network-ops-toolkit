# Verification record

## Release verification

The [release verification run](https://github.com/ikayofoegbu/network-ops-toolkit/actions/runs/41929088813)
tested commit `c60ba2161bd3a65c2b821a062c4f02d47690e433`. All six jobs passed,
with **58 tests per job**:

| Operating system | Python versions | Result |
| --- | --- | --- |
| Ubuntu | 3.11, 3.12, 3.13 | 58 tests passed in each job |
| Windows | 3.11, 3.12, 3.13 | 58 tests passed in each job |

Each job installs the package, checks dependencies, compiles the source and
tests, runs the test suite, and executes both module and installed CLI examples.
The [Actions page](https://github.com/ikayofoegbu/network-ops-toolkit/actions)
provides results for subsequent commits.

## Reproduce the checks

From the repository root using an activated virtual environment:

```text
python -m pip install -e .
python -m pip check
python -m compileall -q src tests examples
python -m unittest discover -s tests -v
python -m netops demo --json
netops demo --json
python examples/troubleshooting_cases.py all
```

For PowerShell without environment activation, use the
[Windows walkthrough](WINDOWS_DEMO.md).

## Test coverage

- DNS resolution errors, address handling, deduplication and the eight-address cap.
- TCP success, refusal, timeout, unreachable destinations and permission errors.
- TLS validation, hostname mismatch, certificate errors, handshake failures and timeout.
- Preservation of TCP success and individual failures across addresses.
- Argument validation, report formatting, JSON schemas and CLI exit codes.
- Example report consistency, simulation labels and absence of network access in examples.
- Five loopback integration tests using real TCP connections and TLS handshakes.

Unit tests inject controlled resolver/socket outcomes. Integration tests bind
temporary listeners to `127.0.0.1`, with disposable certificate trust configured
inside individual SSL contexts.

## Local and packaging checks

Release checks on Linux with Python 3.12.14 verified editable installation,
all 58 tests, dependency consistency, source compilation, example text/JSON
output and relative documentation links. An anonymous public clone was installed
and passed all 58 tests. The built wheel includes the MIT license and SPDX
license metadata. Initial Windows installation and the original 29-test suite
were also confirmed on the maintainer's device.

## Development milestones

| Milestone | Recorded validation |
| --- | --- |
| Initial DNS/TCP implementation | 29 tests; real loopback connection/refusal checks; local Python 3.13.5 |
| Cross-platform CI | [Six passing jobs](https://github.com/ikayofoegbu/network-ops-toolkit/actions/runs/40427289295), 29 tests each |
| TLS integration | [Six passing jobs](https://github.com/ikayofoegbu/network-ops-toolkit/actions/runs/40429917356), 54 tests each |
| Troubleshooting examples | [Six passing jobs](https://github.com/ikayofoegbu/network-ops-toolkit/actions/runs/40431342310), 58 tests each |
| MIT release | [Six passing jobs](https://github.com/ikayofoegbu/network-ops-toolkit/actions/runs/41928155607), 58 tests each |

## Coverage boundaries

CI covers Windows and Ubuntu on Python 3.11-3.13. Integration tests cover IPv4
loopback TCP/TLS. macOS execution and IPv6 TLS integration are outside this
matrix. Live endpoint behavior depends on the network, service, DNS and trust
configuration. The test suite exercises protocol observations; HTTP, STARTTLS
and certificate revocation checks are outside the toolkit's current scope.
