"""Verify offline troubleshooting examples and stored report consistency."""

import contextlib
import importlib.util
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("troubleshooting_cases", ROOT / "examples" / "troubleshooting_cases.py")
CASES = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CASES)


class SyntheticCaseTests(unittest.TestCase):
    def test_cases_use_no_network_and_preserve_layer_boundaries(self):
        with patch("socket.getaddrinfo", side_effect=AssertionError("real DNS invoked")), patch("socket.socket", side_effect=AssertionError("real socket invoked")):
            reports = {name: CASES.build_case(name) for name in CASES.CASES}
        self.assertTrue(all(report["synthetic_demo"] for report in reports.values()))
        self.assertEqual(reports["dns-failure"]["assessment"]["classification"], "dns_failed")
        self.assertEqual(reports["dns-failure"]["tcp"]["status"], "not_run")
        self.assertEqual(reports["tcp-refused"]["tcp"]["attempts"][0]["outcome"], "refused")
        self.assertEqual(reports["tls-failure"]["tcp"]["status"], "connected")
        self.assertEqual(reports["tls-failure"]["assessment"]["classification"], "tls_failed")
        self.assertEqual(reports["tls-failure"]["tcp"]["attempts"][0]["tls"]["verify_code"], 20)

    def test_checked_in_json_matches_current_report_path(self):
        for name in CASES.CASES:
            with self.subTest(case=name):
                stored = json.loads((ROOT / "examples" / "cases" / f"{name}.json").read_text(encoding="utf-8"))
                self.assertEqual(stored, CASES.build_case(name))

    def test_renderer_identifies_simulation_and_expected_failure_exit(self):
        with contextlib.redirect_stdout(io.StringIO()) as stdout:
            result = CASES.main(["all"])
        self.assertEqual(result, 0)
        self.assertEqual(stdout.getvalue().count("[SYNTHETIC DEMO — NO NETWORK TRAFFIC]"), 3)
        with contextlib.redirect_stdout(io.StringIO()) as stdout:
            result = CASES.main(["tls-failure", "--json"])
        self.assertEqual(result, 0)
        self.assertEqual(json.loads(stdout.getvalue())["tls"]["status"], "failed")

    def test_unknown_case_is_usage_error(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as raised:
            CASES.main(["unknown-case"])
        self.assertEqual(raised.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
