# Disposable TLS test fixtures

These files exist solely for local automated tests. `localhost-test-key.pem` is
an intentionally disclosed, disposable test server key, not a credential for any
real service. Never deploy it or trust this CA outside an individual test context.
No employer material or production keys are present.

The CA and server certificate are valid from January 1, 2020 to January 1, 2040.
The server SAN contains localhost and 127.0.0.1. Basic constraints, key usage,
extended key usage, subject key IDs and issuer key ID support strict validation.
The CA signing key was discarded. Regenerate the complete fixture set before
2040 or if certificate policy changes; never disable verification to fix a test.

Tests explicitly trust ca.pem in a new in-memory SSL context. They do not install
it into the operating system trust store. CI loads these PEM files with Python's
standard library; no OpenSSL executable or third-party test package is needed.
