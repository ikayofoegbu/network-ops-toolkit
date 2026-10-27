"""Real local TLS handshakes; disposable trust stays inside each test context."""

import socket
import ssl
import threading
import unittest
from contextlib import contextmanager
from pathlib import Path

from netops.diagnostics import probe

FIXTURES = Path(__file__).parent / "fixtures" / "tls"


@contextmanager
def local_server(stall=False):
    server_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    # No session resumption is exercised. Avoid late TLS 1.3 ticket writes to
    # a handshake-only client which has already closed its socket.
    server_context.num_tickets = 0
    server_context.load_cert_chain(FIXTURES / "localhost.pem", FIXTURES / "localhost-test-key.pem")
    stop = threading.Event()
    errors = []
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.bind(("127.0.0.1", 0))
    listener.listen(1)
    listener.settimeout(3.0)
    port = listener.getsockname()[1]

    def serve():
        try:
            with listener:
                connection, _ = listener.accept()
                with connection:
                    connection.settimeout(3.0)
                    if stall:
                        stop.wait(3.0)
                    else:
                        try:
                            with server_context.wrap_socket(connection, server_side=True):
                                pass
                        except (ssl.SSLError, ConnectionResetError, ConnectionAbortedError):
                            # Certificate rejection and immediate client close can
                            # surface as TLS alerts or Windows peer-close errors.
                            # Tests still assert the exact client report below;
                            # a failed client handshake cannot pass the success test.
                            pass
        except Exception as exc:
            errors.append(exc)

    worker = threading.Thread(target=serve, daemon=True)
    worker.start()
    try:
        yield port
    finally:
        stop.set()
        worker.join(4.0)
        listener.close()
        if worker.is_alive():
            raise AssertionError("Local TLS server did not stop")
        if errors:
            raise AssertionError(f"Local TLS server failed: {errors!r}")


def loopback_resolver(host, port, **kwargs):
    return [(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", ("127.0.0.1", port))]


class TLSLoopbackTests(unittest.TestCase):
    def trusted_context(self):
        return ssl.create_default_context(cafile=str(FIXTURES / "ca.pem"))

    def test_real_validated_tls(self):
        with local_server() as port:
            report = probe("localhost", port, 2.0, tls=True, tls_context=self.trusted_context(), resolver=loopback_resolver)
        self.assertEqual(report["assessment"]["classification"], "tls_validated")
        self.assertTrue(report["tcp"]["attempts"][0]["tls"]["protocol"].startswith("TLS"))

    def test_real_hostname_mismatch_preserves_tcp(self):
        with local_server() as port:
            report = probe("wrong.example", port, 2.0, tls=True, tls_context=self.trusted_context(), resolver=loopback_resolver)
        self.assertEqual(report["tcp"]["status"], "connected")
        self.assertEqual(report["assessment"]["classification"], "tls_failed")
        self.assertEqual(report["tcp"]["attempts"][0]["tls"]["status"], "hostname_mismatch")

    def test_real_untrusted_certificate(self):
        # A context with no trusted roots deterministically rejects the test CA.
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        with local_server() as port:
            report = probe("localhost", port, 2.0, tls=True, tls_context=context, resolver=loopback_resolver)
        self.assertEqual(report["tcp"]["attempts"][0]["tls"]["status"], "certificate_invalid")

    def test_real_tls_timeout_after_tcp_success(self):
        with local_server(stall=True) as port:
            report = probe("localhost", port, 0.2, tls=True, tls_context=self.trusted_context(), resolver=loopback_resolver)
        self.assertEqual(report["tcp"]["status"], "connected")
        self.assertEqual(report["tcp"]["attempts"][0]["tls"]["status"], "timeout")
        self.assertEqual(report["assessment"]["classification"], "tls_failed")


if __name__ == "__main__":
    unittest.main()
