"""Three reproducible synthetic cases. No DNS, TCP or TLS traffic is sent.

Run from the repository root after installing the package:
    python examples/troubleshooting_cases.py all
    python examples/troubleshooting_cases.py tls-failure --json
"""

from __future__ import annotations

import argparse
import json
import socket
import ssl
from typing import Any, Sequence

from netops.cli import format_text
from netops.diagnostics import probe

CASES = ("dns-failure", "tcp-refused", "tls-failure")
HOST = "service.example"
ADDRESS = "192.0.2.10"


def build_case(name: str) -> dict[str, Any]:
    """Use the real report/assessment path with explicitly fake observations."""
    if name not in CASES:
        raise ValueError(f"unknown synthetic case: {name}")

    def resolver(host: str, port: int, **kwargs: Any) -> list[tuple[Any, ...]]:
        if name == "dns-failure":
            # Fixed synthetic code for repeatability; real OS codes vary.
            raise socket.gaierror(-2, "simulated name resolution failure")
        return [(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", (ADDRESS, port))]

    def connector(info: tuple[Any, ...], timeout: float) -> dict[str, Any]:
        attempt: dict[str, Any] = {
            "address": ADDRESS,
            "family": "IPv4",
            "outcome": "refused" if name == "tcp-refused" else "connected",
            "elapsed_ms": 5.0,
        }
        if name == "tls-failure":
            attempt["tls"] = {
                "status": "certificate_invalid",
                "verify_code": 20,
                "verify_message": "unable to get local issuer certificate",
                "elapsed_ms": 3.0,
            }
        return attempt

    options: dict[str, Any] = {"resolver": resolver, "connector": connector}
    if name == "tls-failure":
        # Only constructs a validating context. The fake connector never wraps a
        # socket, and no OS trust store is read or changed for this simulation.
        options.update(tls=True, tls_context=ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT))
    report = probe(HOST, 443, **options)
    report["duration_ms"] = 8.0 if name == "tls-failure" else 5.0
    report["synthetic_demo"] = True
    return report


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Print synthetic troubleshooting cases without network traffic.")
    parser.add_argument("case", choices=(*CASES, "all"))
    parser.add_argument("--json", action="store_true", help="Print one report or, for all, an object keyed by case name")
    args = parser.parse_args(argv)
    selected = CASES if args.case == "all" else (args.case,)
    reports = {name: build_case(name) for name in selected}
    if args.json:
        print(json.dumps(reports if args.case == "all" else reports[args.case], indent=2))
    else:
        for index, (name, report) in enumerate(reports.items()):
            if index:
                print()
            print(f"CASE: {name}")
            print(format_text(report))
    # This is an example renderer. Simulated failures are expected, so successful
    # rendering returns 0. The live netops probe retains its real exit semantics.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
