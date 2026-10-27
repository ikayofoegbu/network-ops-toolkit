"""Mocked TLS behavior: no network access in this module."""

import contextlib
import io
import json
import socket
import ssl
import unittest
from unittest.mock import MagicMock, patch

from netops.cli import format_text, main
from netops.diagnostics import MAX_ADDRESSES, _attempt, demo_report, probe
from netops.tls import client_context, handshake


def record(ip="192.0.2.10", family=socket.AF_INET):
    address = (ip, 443, 0, 0) if family == socket.AF_INET6 else (ip, 443)
    return (family, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", address)


def observation(status, ip="192.0.2.10"):
    return {"address": ip, "family": "IPv4", "outcome": "connected", "elapsed_ms": 1.0, "tls": {"status": status}}


class HandshakeTests(unittest.TestCase):
    def run_handshake(self, error=None):
        context = MagicMock()
        if error:
            context.wrap_socket.side_effect = error
        secured = context.wrap_socket.return_value.__enter__.return_value
        secured.version.return_value = "TLSv1.3"
        secured.cipher.return_value = ("TLS_AES_256_GCM_SHA384", "TLSv1.3", 256)
        connection = MagicMock()
        result = handshake(connection, context, "example.com")
        context.wrap_socket.assert_called_once_with(connection, server_hostname="example.com")
        return result

    def test_validated_protocol_and_cipher(self):
        result = self.run_handshake()
        self.assertEqual(result["status"], "validated")
        self.assertEqual(result["protocol"], "TLSv1.3")
        self.assertEqual(result["cipher"], "TLS_AES_256_GCM_SHA384")
        self.assertGreaterEqual(result["elapsed_ms"], 0)

    def test_certificate_errors_and_name_mismatch_codes(self):
        for code, expected in [(10, "certificate_invalid"), (20, "certificate_invalid"), (62, "hostname_mismatch"), (64, "hostname_mismatch")]:
            with self.subTest(code=code):
                error = ssl.SSLCertVerificationError(1, "verification failed")
                error.verify_code = code
                error.verify_message = "controlled verification failure"
                result = self.run_handshake(error)
                self.assertEqual(result["status"], expected)
                self.assertEqual(result["verify_code"], code)

    def test_handshake_timeout(self):
        self.assertEqual(self.run_handshake(TimeoutError())["status"], "timeout")

    def test_protocol_error(self):
        self.assertEqual(self.run_handshake(ssl.SSLError(1, "protocol failure"))["status"], "handshake_failed")

    def test_socket_error_after_tcp_is_not_tcp_failure(self):
        self.assertEqual(self.run_handshake(ConnectionResetError(104, "reset"))["status"], "socket_error")

    def test_default_context_requires_trust_and_hostname(self):
        context = client_context()
        self.assertEqual(context.verify_mode, ssl.CERT_REQUIRED)
        self.assertTrue(context.check_hostname)


class TLSProbeTests(unittest.TestCase):
    def tls_probe(self, statuses):
        items = [record(f"192.0.2.{i + 1}") for i in range(len(statuses))]
        answers = [observation(status, item[4][0]) for status, item in zip(statuses, items)]
        with patch("netops.diagnostics._attempt", side_effect=answers) as dial:
            report = probe("example.com", 443, tls=True, resolver=lambda *a, **k: items)
        return report, dial

    def test_success_requires_validated_tls(self):
        report, _ = self.tls_probe(["validated"])
        self.assertEqual(report["assessment"]["classification"], "tls_validated")
        self.assertEqual(report["schema_version"], 2)
        self.assertEqual(report["tls"]["certificate_verification"], "required")
        self.assertIn("timeout_per_phase_seconds", report["target"])
        self.assertNotIn("timeout_per_address_seconds", report["target"])
        self.assertIn("Application health was not tested", report["assessment"]["interpretation"])

    def test_tls_failures_preserve_tcp_success(self):
        for status in ("hostname_mismatch", "certificate_invalid", "timeout", "handshake_failed", "socket_error"):
            with self.subTest(status=status):
                report, _ = self.tls_probe([status])
                self.assertEqual(report["tcp"]["status"], "connected")
                self.assertEqual(report["tls"]["status"], "failed")
                self.assertEqual(report["assessment"]["classification"], "tls_failed")

    def test_mixed_addresses_preserve_failed_tls_observation(self):
        report, _ = self.tls_probe(["certificate_invalid", "validated"])
        self.assertEqual(report["tls"]["status"], "validated")
        self.assertEqual(report["tcp"]["attempts"][0]["tls"]["status"], "certificate_invalid")

    def test_attempt_cap_applies_to_tls(self):
        report, dial = self.tls_probe(["timeout"] * 10)
        self.assertEqual(dial.call_count, MAX_ADDRESSES)
        self.assertEqual(report["tcp"]["skipped_addresses"], 2)

    def test_dns_failure_never_attempts_tls(self):
        with patch("netops.diagnostics.socket.getaddrinfo", side_effect=socket.gaierror(-2, "missing")), patch("netops.diagnostics._attempt") as dial:
            report = probe("missing.example", 443, tls=True)
        dial.assert_not_called()
        self.assertEqual(report["assessment"]["classification"], "dns_failed")
        self.assertEqual(report["tls"]["status"], "not_run")

    def test_no_addresses_never_claims_tls_failure(self):
        report = probe("example.com", 443, tls=True, resolver=lambda *a, **k: [])
        self.assertEqual(report["assessment"]["classification"], "no_usable_addresses")
        self.assertEqual(report["tls"]["status"], "not_run")

    def test_insecure_context_rejected_before_resolution(self):
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.check_hostname = False
        for verification in (ssl.CERT_NONE, ssl.CERT_REQUIRED):
            context.verify_mode = verification
            with patch("socket.getaddrinfo") as resolve:
                with self.assertRaisesRegex(ValueError, "verification"):
                    probe("example.com", 443, tls=True, tls_context=context)
                resolve.assert_not_called()

    def test_context_requires_opt_in(self):
        with self.assertRaisesRegex(ValueError, "tls=True"):
            probe("example.com", 443, tls_context=client_context())

    def test_optional_certificate_mode_rejected(self):
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.verify_mode = ssl.CERT_OPTIONAL
        with patch("socket.getaddrinfo") as resolve:
            with self.assertRaisesRegex(ValueError, "verification"):
                probe("example.com", 443, tls=True, tls_context=context)
        resolve.assert_not_called()

    def test_trailing_dot_normalized_for_certificate_name(self):
        with patch("netops.diagnostics._attempt", return_value=observation("validated")) as dial:
            report = probe("example.com.", 443, tls=True, resolver=lambda *a, **k: [record()])
        self.assertEqual(dial.call_args.kwargs["server_hostname"], "example.com")
        self.assertEqual(report["target"]["host"], "example.com.")

    def test_tcp_refusal_does_not_start_tls(self):
        context = client_context()
        sock = MagicMock()
        sock.__enter__.return_value = sock
        sock.connect.side_effect = ConnectionRefusedError(111, "refused")
        with patch("socket.socket", return_value=sock), patch("netops.diagnostics.handshake") as perform:
            result = _attempt(record(), 1.0, server_hostname="example.com", tls_context=context)
        perform.assert_not_called()
        self.assertEqual(result["outcome"], "refused")
        self.assertEqual(result["tls"]["status"], "not_run")

    def test_tls_uses_original_socket_without_second_connection(self):
        context = client_context()
        sock = MagicMock()
        sock.__enter__.return_value = sock
        with patch("socket.socket", return_value=sock) as create, patch("netops.diagnostics.handshake", return_value={"status": "timeout"}) as perform:
            result = _attempt(record(), 0.5, server_hostname="example.com", tls_context=context)
        create.assert_called_once()
        sock.connect.assert_called_once_with(("192.0.2.10", 443))
        sock.settimeout.assert_called_once_with(0.5)
        perform.assert_called_once_with(sock, context, "example.com")
        self.assertEqual(result["outcome"], "connected")

    def test_default_demo_is_unchanged(self):
        report = demo_report()
        self.assertEqual(report["schema_version"], 1)
        self.assertNotIn("tls", report)


class TLSCLITests(unittest.TestCase):
    def test_tls_cli_json_and_exit_codes(self):
        for status, expected_exit in [("validated", 0), ("timeout", 1)]:
            report, _ = TLSProbeTests().tls_probe([status])
            with patch("netops.cli.probe", return_value=report) as perform, contextlib.redirect_stdout(io.StringIO()) as stdout:
                result = main(["probe", "--host", "example.com", "--port", "443", "--tls", "--json"])
            perform.assert_called_once_with("example.com", 443, 2.0, tls=True)
            self.assertEqual(result, expected_exit)
            self.assertEqual(json.loads(stdout.getvalue())["tls"]["status"], "validated" if status == "validated" else "failed")

    def test_text_preserves_tcp_and_tls_outcomes(self):
        report, _ = TLSProbeTests().tls_probe(["hostname_mismatch"])
        text = format_text(report)
        self.assertIn("TCP: connected", text)
        self.assertIn("TLS: failed", text)
        self.assertIn("hostname_mismatch", text)


if __name__ == "__main__":
    unittest.main()
