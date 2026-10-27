# Five-minute Windows interview demo

Goal: explain three different failures using reproducible synthetic reports,
then show the engineering and CI evidence. The timed demo sends no network
traffic. Installation and GitHub access are preparation outside the five minutes.

## Preparation

Use a fresh folder so the original Windows-verified project remains intact.
Prerequisites: Git, Python 3.11+ with the Python launcher, and access to the
private repository. Use your usual GitHub sign-in; do not paste tokens into
commands or share the private repository without an explicit sharing decision.

PowerShell:

```powershell
$ErrorActionPreference = 'Stop'
$demoPath = Join-Path $env:USERPROFILE 'Documents\network-ops-toolkit-demo'
if (Test-Path -LiteralPath $demoPath) {
    throw 'Demo folder already exists. Choose a new folder name; do not overwrite it.'
}
git clone https://github.com/ikayofoegbu/network-ops-toolkit.git $demoPath
if ($LASTEXITCODE -ne 0) { throw 'Clone failed.' }
Set-Location -LiteralPath $demoPath
```

Before M4 is merged, switch this fresh checkout to the review branch:

```powershell
git switch feat/m4-interview-demo
if ($LASTEXITCODE -ne 0) { throw 'Review branch checkout failed.' }
```

After M4 is merged, a fresh default-branch clone already includes the material;
omit that branch-switch step. Then prepare the environment without activation
scripts or execution-policy changes:

```powershell
py -3 -m venv .venv
if ($LASTEXITCODE -ne 0) { throw 'Virtual environment creation failed.' }
& .\.venv\Scripts\python.exe -m pip install -e .
if ($LASTEXITCODE -ne 0) { throw 'Installation failed.' }
& .\.venv\Scripts\python.exe -m unittest discover -s tests -v
if ($LASTEXITCODE -ne 0) { throw 'Tests failed; resolve this before the demo.' }
```

Expect 58 tests on the M4 candidate. The suite includes real local loopback
traffic; it does not probe external systems. The three presentation cases below
are entirely synthetic. Open the engineering case study and the latest passing
CI run in advance. Have the stored JSON available as a clearly labelled backup
if your presentation device cannot run Python. No live probe is needed.

## Timed sequence

| Time | Action | Point to explain |
| --- | --- | --- |
| 0:00–0:30 | Introduce the project and scope | One host/port, bounded attempts, observations rather than invented causes |
| 0:30–1:20 | Render DNS failure | No TCP evidence exists when resolution fails |
| 1:20–2:10 | Render TCP refusal | Refusal differs from timeout; the rejecting device is unknown |
| 2:10–3:10 | Render TLS failure in text and JSON | TCP succeeded while certificate validation failed; application health remains unknown |
| 3:10–4:20 | Show the six-job CI evidence and Windows fixture fix | Explain the failure, the narrow fix and unchanged security assertions |
| 4:20–5:00 | State limits and answer one design question | No HTTP/STARTTLS, no insecure retry, no production or security-completeness claims |

Run these separately, in order, from the fresh checkout root:

```powershell
& .\.venv\Scripts\python.exe examples\troubleshooting_cases.py dns-failure
& .\.venv\Scripts\python.exe examples\troubleshooting_cases.py tcp-refused
& .\.venv\Scripts\python.exe examples\troubleshooting_cases.py tls-failure
& .\.venv\Scripts\python.exe examples\troubleshooting_cases.py tls-failure --json
```

Every text case must display `[SYNTHETIC DEMO — NO NETWORK TRAFFIC]`. The TLS case
must show TCP connected, TLS failed, `certificate_invalid` and JSON schema 2.
All example-renderer commands return 0 when printing succeeds, because their
failure results are intentionally simulated. The actual `netops probe` has
different exit semantics; do not present the renderer as a live probe.

## Rehearsal questions

- Why does TCP connected not prove the application works?
- Why retain failed address attempts when another address succeeds?
- Why leave certificate validation enabled during troubleshooting?
- What would you inspect next for each case, and what would you avoid changing?
- What exactly did Windows CI reveal that the local run missed?

Practice once on your own Windows device before using this in an interview.
Cross-platform CI of the Python examples does not certify your Git installation,
private-repository authentication, PowerShell environment, presentation setup or
five-minute delivery time. This guide is a prepared runbook, not a claim that you
have already rehearsed it. Keep a screenshot or saved CI page ready if the
interview environment has no browser access; clearly identify it as saved evidence.
