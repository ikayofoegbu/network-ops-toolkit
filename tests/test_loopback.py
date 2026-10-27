"""Controlled integration check: local loopback only; no external network."""

import socket
import unittest

from netops.diagnostics import probe


class LoopbackIntegrationTests(unittest.TestCase):
    def test_actual_tcp_handshake_to_loopback_listener(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
            listener.bind(("127.0.0.1", 0))
            listener.listen(1)
            port = listener.getsockname()[1]
            report = probe("127.0.0.1", port, timeout=1.0)
        self.assertEqual(report["assessment"]["classification"], "tcp_connected")
        self.assertEqual(report["dns"]["addresses"], [{"address": "127.0.0.1", "family": "IPv4"}])
        self.assertEqual(report["tcp"]["attempts"][0]["outcome"], "connected")


if __name__ == "__main__":
    unittest.main()
