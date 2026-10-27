# Milestone 1 verification record

Date: 2026-10-26. Scope: local isolated development environment only.

## Executed

- `PYTHONPATH=src python -m unittest discover -s tests -v` — **PASS, 29 tests** on Python 3.13.5. The suite includes one local-only 127.0.0.1 TCP handshake check; the remaining tests are mocked.
- `PYTHONPATH=src python -m netops demo` — **PASS**, visibly identified as simulated output.
- `PYTHONPATH=src python -m netops demo --json` — **PASS**, saved to `examples/demo-report.json`.
- `python -m compileall -q src tests` — **PASS**.
- One manual local test of a temporary TCP listener on 127.0.0.1 returned `connected`; after listener closure the next test returned `refused`. **PASS**.
- Editable package installation and installed `netops demo --json` command — **PASS** in an isolated test environment after supplying the locally available setuptools build backend. This setup differed from the default clean-venv installation; do not treat it as proof of standard Windows installation.

## Not executed / outstanding gates

- No probe against any external destination was made for this milestone.
- Windows PowerShell installation and local user-device verification remain outstanding.
- GitHub Actions is supplied as configuration but has **not** been run in the user's GitHub account.
- No GitHub repository was created or published in this milestone.
- Public release requires owner review, repository security review, CI, and a licensing decision.

## Owner verification update for Milestone 2

The owner subsequently confirmed successful Windows installation, synthetic demo execution and all 29 local tests, including the real loopback test. This supersedes the outstanding Windows gate above; it is owner-reported evidence, separate from the original isolated-environment checks. Remote GitHub Actions evidence remains pending.
