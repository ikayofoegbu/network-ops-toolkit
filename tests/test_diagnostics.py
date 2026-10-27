import errno
import socket
import unittest
from unittest.mock import patch

from netops.diagnostics import MAX_ADDRESSES, _attempt, demo_report, probe, validate_target


def record(ip, port=443, family=socket.AF_INET):
    sockaddr = (ip, port, 0, 0) if family == socket.AF_INET6 else (ip, port)
    return (family, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", sockaddr)


def resolver_for(*records):
    return lambda host, port, **kwargs: list(records)


def dial(outcome="connected"):
    return lambda info, timeout: {"address": info[4][0], "family": "IPv4" if info[0] == socket.AF_INET else "IPv6", "outcome": outcome, "elapsed_ms": 0.0}


class TargetValidationTests(unittest.TestCase):
    def test_good_inputs(self):
        for host in ("example.com", "example.com.", "localhost", "192.0.2.1", "2001:db8::1"):
            with self.subTest(host=host):
                validate_target(host, 443, 1)

    def test_reject_invalid_hosts(self):
        for host in ("", "bad host", "https://example.com", "example.com/path", "-bad.example", "host..com", "a" * 254):
            with self.subTest(host=host):
                with self.assertRaises(ValueError):
                    validate_target(host, 443, 1)

    def test_reject_invalid_ports(self):
        for port in (0, -1, 65536, True):
            with self.subTest(port=port):
                with self.assertRaises(ValueError):
                    validate_target("example.com", port, 1)

    def test_reject_invalid_timeout(self):
        for timeout in (0, 0.09, 10.01, float("nan"), float("inf")):
            with self.subTest(timeout=timeout):
                with self.assertRaises(ValueError):
                    validate_target("example.com", 443, timeout)


class ProbeTests(unittest.TestCase):
    def test_successful_connection(self):
        result = probe("example.com", 443, resolver=resolver_for(record("192.0.2.11")), connector=dial())
        self.assertEqual(result["assessment"]["classification"], "tcp_connected")
        self.assertEqual(result["tcp"]["status"], "connected")
        self.assertEqual(result["dns"]["status"], "resolved")
        self.assertEqual(result["schema_version"], 1)

    def test_dns_failure_never_dials(self):
        def failed(*args, **kwargs):
            raise socket.gaierror(-2, "Name not found")
        def should_not_dial(*args, **kwargs):
            self.fail("connector was called after DNS failure")
        result = probe("missing.example", 443, resolver=failed, connector=should_not_dial)
        self.assertEqual(result["assessment"]["classification"], "dns_failed")
        self.assertEqual(result["tcp"]["status"], "not_run")
        self.assertEqual(result["dns"]["error_code"], -2)

    def test_refusal_has_cautious_interpretation(self):
        result = probe("example.com", 443, resolver=resolver_for(record("192.0.2.11")), connector=dial("refused"))
        self.assertEqual(result["tcp"]["status"], "failed")
        self.assertIn("not identified", result["assessment"]["interpretation"])

    def test_timeout_does_not_assert_root_cause(self):
        result = probe("example.com", 443, resolver=resolver_for(record("192.0.2.11")), connector=dial("timeout"))
        self.assertIn("not proven", result["assessment"]["interpretation"])

    def test_dual_stack_and_deduplication(self):
        ips = [record("2001:db8::10", family=socket.AF_INET6), record("192.0.2.20"), record("192.0.2.20")]
        result = probe("example.com", 443, resolver=resolver_for(*ips), connector=dial())
        self.assertEqual(len(result["tcp"]["attempts"]), 2)
        self.assertEqual(result["dns"]["addresses"][0]["family"], "IPv6")
        self.assertEqual(result["dns"]["addresses"][1]["family"], "IPv4")

    def test_failed_ipv6_then_successful_ipv4(self):
        items = [record("2001:db8::10", family=socket.AF_INET6), record("192.0.2.20")]
        def mixed(info, timeout):
            return {"address": info[4][0], "outcome": "timeout" if info[0] == socket.AF_INET6 else "connected", "family": "IPv6" if info[0] == socket.AF_INET6 else "IPv4", "elapsed_ms": 1.0}
        result = probe("example.com", 443, resolver=resolver_for(*items), connector=mixed)
        self.assertEqual(result["tcp"]["status"], "connected")
        self.assertEqual([a["outcome"] for a in result["tcp"]["attempts"]], ["timeout", "connected"])

    def test_maximum_attempt_cap_reported(self):
        items = [record(f"192.0.2.{i}") for i in range(1, 11)]
        result = probe("example.com", 443, resolver=resolver_for(*items), connector=dial("timeout"))
        self.assertEqual(len(result["tcp"]["attempts"]), MAX_ADDRESSES)
        self.assertEqual(result["tcp"]["skipped_addresses"], 2)

    def test_no_usable_addresses(self):
        result = probe("example.com", 443, resolver=resolver_for(), connector=dial())
        self.assertEqual(result["dns"]["status"], "no_addresses")
        self.assertEqual(result["assessment"]["classification"], "no_usable_addresses")

    def test_socket_error_not_hidden(self):
        result = probe("example.com", 443, resolver=resolver_for(record("192.0.2.5")), connector=dial("socket_error"))
        self.assertEqual(result["tcp"]["status"], "failed")
        self.assertIn("individual address outcomes", result["assessment"]["interpretation"].lower())

    def test_dns_resolver_oserror(self):
        def failed(*args, **kwargs):
            raise OSError(errno.ENETUNREACH, "unreachable")
        result = probe("example.com", 443, resolver=failed, connector=dial())
        self.assertEqual(result["assessment"]["classification"], "dns_failed")

    def test_demo_injects_dependencies_no_real_network(self):
        with patch("socket.getaddrinfo", side_effect=AssertionError("real DNS invoked")), patch("socket.socket", side_effect=AssertionError("real TCP invoked")):
            report = demo_report()
        self.assertTrue(report["synthetic_demo"])
        self.assertEqual(report["assessment"]["classification"], "tcp_connected")
        self.assertEqual(report["tcp"]["attempts"][0]["elapsed_ms"], 12.4)


class SocketAttemptTests(unittest.TestCase):
    def _socket_result(self, exception=None):
        class FakeSocket:
            def __enter__(self):
                return self
            def __exit__(self, *args):
                return None
            def settimeout(self, timeout):
                pass
            def connect(self, sockaddr):
                if exception:
                    raise exception
        with patch("netops.diagnostics.socket.socket", return_value=FakeSocket()):
            return _attempt(record("192.0.2.20"), 2.0)

    def test_connected(self):
        self.assertEqual(self._socket_result()["outcome"], "connected")

    def test_refused(self):
        self.assertEqual(self._socket_result(ConnectionRefusedError(errno.ECONNREFUSED, "refused"))["outcome"], "refused")

    def test_timeout(self):
        self.assertEqual(self._socket_result(TimeoutError("timed out"))["outcome"], "timeout")

    def test_unreachable(self):
        self.assertEqual(self._socket_result(OSError(errno.ENETUNREACH, "no route"))["outcome"], "network_unreachable")

    def test_permission_denied(self):
        self.assertEqual(self._socket_result(PermissionError(errno.EACCES, "permission denied"))["outcome"], "permission_denied")

    def test_other_os_error(self):
        self.assertEqual(self._socket_result(OSError(errno.EINVAL, "invalid"))["outcome"], "socket_error")


if __name__ == "__main__":
    unittest.main()
