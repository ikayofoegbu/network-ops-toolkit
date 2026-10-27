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

## Milestone 2: initial GitHub Actions verification

Date: 2026-10-26 (America/Cambridge_Bay).

- Repository: https://github.com/ikayofoegbu/network-ops-toolkit (private).
- Tested source commit: `8eb121af3feabff48f625466ea8ae075b23b8c52`.
- Actual push-triggered run: https://github.com/ikayofoegbu/network-ops-toolkit/actions/runs/40427289295.
- All six jobs completed successfully: Python 3.11, 3.12 and 3.13 on ubuntu-latest and windows-latest.
- Each job installed the package, checked dependencies, compiled sources, ran the 29-test unit/loopback suite, and exercised both module and installed CLI synthetic demos. No test failures occurred.
- Reviewed warnings: inherited checkout v4 and setup-python v5 used deprecated Node 20 declarations. A follow-up changes only CI action references to verified Node 24 v6 commits, pinned by full SHA. That follow-up requires its own CI result; consult the repository Actions page for subsequent runs.
- Runner notice: ubuntu-latest is a moving image label. This matrix is not a test of every Linux distribution, macOS, external connectivity, TLS or application health.
- No public release, external probes, paid services, or Milestone 3 implementation authorized.
