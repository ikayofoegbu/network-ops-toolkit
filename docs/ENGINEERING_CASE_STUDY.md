# Engineering case study: evidence before diagnosis

## Problem and scope

A statement such as "the network is down" collapses several different questions:
did the name resolve, did a TCP connection succeed, and did TLS validation pass?
The toolkit records those observations separately for one host and port,
preserves per-address outcomes, and suggests the next useful check.

The implementation uses Python 3.11+, has no third-party runtime dependencies,
and attempts at most eight distinct resolved addresses. Windows and Linux
behavior is verified by a six-job CI matrix.

## Decisions and trade-offs

| Decision | Reason | Limit |
| --- | --- | --- |
| Separate DNS, TCP and TLS observations | Avoid treating lower-layer success as application health | No HTTP or application-level validation |
| One target/port, cap of eight addresses | Bound connection attempts and retain dual-stack evidence | DNS timing is controlled by the system resolver |
| TLS upgrades the existing TCP connection | Preserve the connection context and avoid a second connect | Direct TLS only; no STARTTLS |
| Certificate and hostname validation required | Report meaningful authenticated TLS success | Trust depends on the selected environment; revocation is not established |
| Resolver/connector injection | Make failure cases deterministic without external probes | Simulated observations must remain labelled |
| TCP-only schema 1, TLS opt-in schema 2 | Preserve existing output while making TLS timing/fields explicit | Consumers must check the schema version |
| Fail-fast disabled in the six-job matrix | Collect evidence from every supported Python/OS combination | A green matrix is not every OS, network or security scenario |

TCP connect and TLS handshake each receive a timeout. This is not a whole-run
deadline: worst-case socket time can approach twice the chosen timeout per
address, and DNS/trust-store loading are outside that bound. The CLI requires
validated TLS for exit 0 when TLS was requested; TCP success alone is insufficient.

## A cross-platform defect found by CI

The initial TLS implementation passed locally and on Linux. Windows CI exposed a
problem in the test server fixture: an immediate handshake-only client close
could surface as connection abort/reset 10053/10054 and fail fixture cleanup
before the report assertions ran.

The correction stayed in the fixture. Unused TLS session tickets were disabled,
and expected TLS alerts/peer-close exceptions were handled during the server
handshake/close. Exact client outcome assertions remained active, while
unrelated fixture errors still failed the test. No tests were removed or skipped,
and client certificate/hostname validation was not weakened.

Evidence:

- [Initial failed PR run](https://github.com/ikayofoegbu/network-ops-toolkit/actions/runs/40428493825).
- [Test-only correction](https://github.com/ikayofoegbu/network-ops-toolkit/commit/4f33bc0101c7f018e402fc75eac180f95ef94597).
- [Corrected PR run](https://github.com/ikayofoegbu/network-ops-toolkit/actions/runs/40428655206).
- [Integrated M3 run](https://github.com/ikayofoegbu/network-ops-toolkit/actions/runs/40429917356): all six jobs passed, 54 tests per job at `90db84dd5f6373b9b367e8c17271365c70583415`.

The lesson is specific: local success did not establish Windows fixture
correctness. CI provided evidence to narrow the fix instead of weakening the
test's security requirement.

## Verification

The current suite contains **58 tests**: 29 original DNS/TCP tests, 25 TLS
tests and four regression tests for the example reports. Integration tests
exercise real TCP connections and TLS handshakes on loopback, including trusted
TLS, hostname mismatch, untrusted certificates and handshake timeout.

The [release verification run](https://github.com/ikayofoegbu/network-ops-toolkit/actions/runs/41929088813)
passed all six Windows/Linux Python 3.11-3.13 jobs, with 58 tests per job. Local
checks also verified editable installation, installed CLI commands, JSON
output, example consistency and wheel license metadata.

The [three troubleshooting cases](TROUBLESHOOTING_CASES.md) exercise the same
report-generation path using deterministic simulated observations. Separate
loopback integration tests exercise real socket behavior. The
[Windows walkthrough](WINDOWS_DEMO.md) provides reproducible commands.

## Operational scope

The tool checks name resolution, one TCP port and optional direct TLS. HTTP,
STARTTLS and certificate revocation checks are outside its scope. TLS success
means certificate and hostname validation passed against the selected trust
store; application health requires application-layer checks.

The integration suite covers IPv4 loopback TLS. macOS execution and IPv6 TLS
integration are outside the current CI coverage. Trust-store configuration,
Python/OpenSSL versions and runner images affect environment-specific behavior.
A chain-validation error can precede a hostname error, so reports preserve the
verification error returned by OpenSSL.

## Implementation summary

DNS, TCP and TLS observations remain separate throughout report generation.
TCP success is retained when TLS validation fails, each address keeps its own
outcome, and certificate verification stays enabled. Dependency injection makes
failure paths reproducible, while loopback integration tests verify the real
socket and TLS behavior. CI exposed a Windows fixture-lifecycle issue and
validated the targeted correction without weakening the client security checks.

Independent engineering project by Ikay Ofoegbu, developed with AI assistance.
See the [verification record](VERIFICATION.md) and [release review](RELEASE_REVIEW.md)
for the supporting checks.
