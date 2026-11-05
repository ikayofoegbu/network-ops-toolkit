# Windows installation and troubleshooting walkthrough

This walkthrough installs the toolkit, runs its automated tests and renders
three reproducible troubleshooting cases in PowerShell.

## Requirements

- Git and Python 3.11+ with the Windows Python launcher.
- A new checkout directory; the commands preserve any existing directory.
- The public repository can be cloned without signing in.

## Install and verify

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

Create an isolated environment and run the test suite:

```powershell
py -3 -m venv .venv
if ($LASTEXITCODE -ne 0) { throw 'Virtual environment creation failed.' }
& .\.venv\Scripts\python.exe -m pip install -e .
if ($LASTEXITCODE -ne 0) { throw 'Installation failed.' }
& .\.venv\Scripts\python.exe -m unittest discover -s tests -v
if ($LASTEXITCODE -ne 0) { throw 'Test suite failed.' }
```

Expect 58 passing tests. The integration tests use temporary loopback listeners
for real TCP and TLS checks. Example reports below use deterministic simulated
observations.

## Run the troubleshooting cases

Run these separately, in order, from the fresh checkout root:

```powershell
& .\.venv\Scripts\python.exe examples\troubleshooting_cases.py dns-failure
& .\.venv\Scripts\python.exe examples\troubleshooting_cases.py tcp-refused
& .\.venv\Scripts\python.exe examples\troubleshooting_cases.py tls-failure
& .\.venv\Scripts\python.exe examples\troubleshooting_cases.py tls-failure --json
```

Text output displays `[SYNTHETIC DEMO — NO NETWORK TRAFFIC]`. The TLS case
shows TCP connected, TLS failed, `certificate_invalid` and JSON schema 2.
All example-renderer commands return 0 when printing succeeds, because their
failure results are intentionally simulated. The actual `netops probe` has
different exit semantics: it returns 1 when the requested connection or TLS
validation fails. See the [README](../README.md) for live-probe usage.
