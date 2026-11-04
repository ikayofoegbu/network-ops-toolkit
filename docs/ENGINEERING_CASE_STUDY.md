# Engineering case study: evidence before diagnosis

## Problem and scope

A statement such as "the network is down" collapses several different questions:
did the name resolve, did a TCP connection succeed, and did TLS validation pass?
This independent portfolio project makes those observations explicit for one
host and port. It reports what was observed and suggests the next useful check
without claiming to identify an unobserved root cause.

The scope is intentionally small: Python 3.11+, Windows and Linux CI, no
third-party runtime dependencies, and at most eight distinct resolved addresses.
It is not an employer deliverable, an incident history, or a production
monitoring/scanning system. Implementation was AI-assisted; scope and merges
were owner-approved. The evidence is reproducible tests and recorded CI, not a
claim of manual authorship of every line.

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

The original TLS candidate passed locally and on Linux. Windows CI exposed a
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

## What the evidence supports

M3 retained 29 original tests and added 25 TLS tests. The 54-test suite includes
mocked failure paths and five real local TCP/TLS integration tests. A separate
manual installed-CLI check reached a local TLS server and returned validated TLS
with exit 0. These checks establish the tested behavior in those environments.

M4 adds the [three synthetic cases](TROUBLESHOOTING_CASES.md) and a
[five-minute Windows demo](WINDOWS_DEMO.md), plus regression checks for example
generation, simulation labelling, offline behavior and stored-JSON consistency.
Its pull request records the candidate's actual CI results separately from the
historical M3 evidence above.

## Limits I would state in an interview

I have not established real production connectivity, application health, every
certificate defect, certificate revocation status, macOS compatibility, or a
complete security assessment. IPv4 local TLS was tested; IPv6 TLS was not
separately integrated. A trust failure can mask a later hostname error. Default
trust stores, Python/OpenSSL behavior and runner images can change.

The next decision should follow a real use case, such as an explicitly bounded
application-level check. I would agree its safety limits, output contract and
acceptance criteria before adding it. See the [release review](RELEASE_REVIEW.md)
for the current publication and licensing status.

## Short explanation to rehearse

"I built a small, AI-assisted network diagnostic project around evidence rather
than automatic root-cause claims. It distinguishes DNS, TCP and optional TLS,
keeps certificate validation enabled, and preserves failures across addresses.
I used deterministic unit tests and controlled loopback integration tests, then
verified the supported Python versions on Windows and Linux. Windows CI caught
a fixture lifecycle issue that local testing missed. The scope is narrow, and I
can show exactly what the tool establishes and what it does not."

Use this wording only after rehearsing the demo and being able to explain the
code paths and limitations in your own words. No personal Windows rehearsal of
the M4 guide has been claimed.
