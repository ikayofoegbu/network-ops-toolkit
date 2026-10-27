"""Validated TLS handshakes on an already-connected, caller-owned socket."""

from __future__ import annotations

import socket
import ssl
from time import perf_counter
from typing import Any

# OpenSSL X509 verification codes, not text matching against translated messages.
# https://github.com/openssl/openssl/blob/master/include/openssl/x509_vfy.h.in
_NAME_MISMATCH_CODES = {62, 64}


def client_context() -> ssl.SSLContext:
    """Use Python's client defaults and system trust; never disable verification."""
    return ssl.create_default_context()


def validate_context(context: ssl.SSLContext) -> None:
    if not context.check_hostname or context.verify_mode != ssl.CERT_REQUIRED:
        raise ValueError("TLS requires certificate and hostname verification")


def handshake(connection: socket.socket, context: ssl.SSLContext, host: str) -> dict[str, Any]:
    """Record a TLS observation; no HTTP, application payload, or insecure retry."""
    started = perf_counter()
    result: dict[str, Any]
    try:
        with context.wrap_socket(connection, server_hostname=host) as secured:
            cipher = secured.cipher()
            result = {
                "status": "validated",
                "protocol": secured.version(),
                "cipher": cipher[0] if cipher else None,
            }
    except ssl.SSLCertVerificationError as exc:
        code = getattr(exc, "verify_code", None)
        result = {
            "status": "hostname_mismatch" if code in _NAME_MISMATCH_CODES else "certificate_invalid",
            "verify_code": code,
            "verify_message": getattr(exc, "verify_message", "Certificate verification failed"),
        }
    except TimeoutError:
        result = {"status": "timeout"}
    except ssl.SSLError as exc:
        result = {"status": "handshake_failed", "reason": getattr(exc, "reason", None)}
    except OSError as exc:
        result = {"status": "socket_error", "os_error_code": exc.errno}
    result["elapsed_ms"] = round((perf_counter() - started) * 1000, 2)
    return result


def annotate_report(report: dict[str, Any], host: str) -> dict[str, Any]:
    """Add TLS schema v2 fields without changing the underlying TCP observations."""
    observations = [attempt.get("tls", {"status": "not_run"}) for attempt in report["tcp"]["attempts"]]
    validated = any(item["status"] == "validated" for item in observations)
    attempted = any(item["status"] != "not_run" for item in observations)
    report["schema_version"] = 2
    report["target"]["timeout_per_phase_seconds"] = report["target"].pop("timeout_per_address_seconds")
    report["tls"] = {
        "status": "validated" if validated else ("failed" if attempted else "not_run"),
        "server_hostname": host,
        "certificate_verification": "required",
    }
    if validated:
        report["assessment"] = {
            "classification": "tls_validated",
            "interpretation": "At least one TLS handshake passed certificate and hostname validation using the configured trust store. Application health was not tested.",
            "next_checks": ["If the application still fails, check its application-layer responses."],
        }
    elif report["tcp"]["status"] == "connected":
        report["assessment"] = {
            "classification": "tls_failed",
            "interpretation": "TCP connectivity succeeded, but no TLS handshake passed validation. Inspect each TLS outcome; the root cause is not established.",
            "next_checks": ["Review certificate trust, validity and hostname errors before changing configuration.", "For timeouts or handshake errors, check the service's TLS configuration and path using authorized tooling."],
        }
    return report
