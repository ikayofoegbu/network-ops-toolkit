import contextlib
import io
import json
import unittest
from unittest.mock import patch

from netops.cli import bounded_timeout, format_text, main, positive_port
from netops.diagnostics import demo_report


class CliTests(unittest.TestCase):
    def test_demo_text(self):
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            result = main(["demo"])
        self.assertEqual(result, 0)
        self.assertIn("SYNTHETIC DEMO", stdout.getvalue())
        self.assertIn("Application health was not tested", stdout.getvalue())

    def test_demo_json(self):
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            result = main(["demo", "--json"])
        self.assertEqual(result, 0)
        self.assertTrue(json.loads(stdout.getvalue())["synthetic_demo"])

    def test_probe_failed_exit_code(self):
        fake = demo_report()
        fake["tcp"]["status"] = "failed"
        fake["tcp"]["attempts"][0]["outcome"] = "timeout"
        fake["assessment"]["classification"] = "tcp_failed"
        with patch("netops.cli.probe", return_value=fake):
            with contextlib.redirect_stdout(io.StringIO()):
                result = main(["probe", "--host", "localhost", "--port", "443"])
        self.assertEqual(result, 1)

    def test_invalid_port_and_timeout_are_rejected(self):
        for argv in (["probe", "--host", "localhost", "--port", "0"],
                     ["probe", "--host", "localhost", "--port", "443", "--timeout", "999"]):
            with self.subTest(argv=argv):
                with contextlib.redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit) as raised:
                        main(argv)
                self.assertEqual(raised.exception.code, 2)

    def test_invalid_host_fails_before_probe(self):
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as raised:
                main(["probe", "--host", "https://example.com", "--port", "443"])
        self.assertEqual(raised.exception.code, 2)

    def test_helpers(self):
        self.assertEqual(positive_port("443"), 443)
        self.assertEqual(bounded_timeout("0.5"), 0.5)

    def test_text_has_conservative_assessment(self):
        output = format_text(demo_report())
        self.assertIn("TCP handshake succeeded", output)


if __name__ == "__main__":
    unittest.main()
