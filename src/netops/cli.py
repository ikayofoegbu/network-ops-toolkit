"""Command-line interface for bounded diagnostics."""

from __future__ import annotations

import argparse
import json
from typing import Any, Sequence

from .diagnostics import demo_report, probe


def format_text(report: dict[str, Any]) -> str:
    target = report["target"]
    lines = [
        "NETWORK OPS TOOLKIT — CONNECTIVITY REPORT",
        "[SYNTHETIC DEMO — NO NETWORK TRAFFIC]" if report.get("synthetic_demo") else "[LIVE LOCAL SOCKET OBSERVATIONS]",
        f"Target: {target['host']}:{target['port']}",
        f"DNS: {report['dns']['status']}",
    ]
    for address in report["dns"]["addresses"]:
        lines.append(f"  Resolved: {address['address']} ({address['family']})")
    lines.append(f"TCP: {report['tcp']['status']}")
    if "tls" in report:
        lines.append(f"TLS: {report['tls']['status']} (certificate and hostname verification required)")
    for attempt in report["tcp"]["attempts"]:
        lines.append(
            f"  {attempt['address']} ({attempt['family']}): {attempt['outcome']} "
            f"in {attempt['elapsed_ms']:.2f} ms"
        )
        if "tls" in attempt:
            observed = attempt["tls"]
            detail = observed.get("verify_message") or observed.get("reason") or observed.get("protocol")
            lines.append(f"    TLS: {observed['status']}" + (f" ({detail})" if detail else ""))
    if report["tcp"]["skipped_addresses"]:
        lines.append(f"  Not attempted: {report['tcp']['skipped_addresses']} additional addresses")
    lines.append(f"Assessment: {report['assessment']['classification']}")
    lines.append(report["assessment"]["interpretation"])
    lines.append("Suggested next checks:")
    lines.extend(f"  - {check}" for check in report["assessment"]["next_checks"])
    return "\n".join(lines)


def positive_port(text: str) -> int:
    try:
        port = int(text)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("port must be an integer") from exc
    if not 1 <= port <= 65535:
        raise argparse.ArgumentTypeError("port must be between 1 and 65535")
    return port


def bounded_timeout(text: str) -> float:
    try:
        timeout = float(text)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("timeout must be a number") from exc
    if not 0.1 <= timeout <= 10.0:
        raise argparse.ArgumentTypeError("timeout must be from 0.1 to 10 seconds")
    return timeout


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a bounded, single-port TCP connectivity check.")
    subs = parser.add_subparsers(dest="command", required=True)
    command = subs.add_parser("probe", help="Perform local DNS and TCP diagnostics for one host and port")
    command.add_argument("--host", required=True, help="Hostname or IP address, not a URL")
    command.add_argument("--port", type=positive_port, required=True, help="TCP port 1–65535")
    command.add_argument("--timeout", type=bounded_timeout, default=2.0, help="Timeout for each address's TCP connect and optional TLS handshake (0.1–10 seconds per phase)")
    command.add_argument("--json", action="store_true", help="Machine-readable JSON output")
    command.add_argument("--tls", action="store_true", help="Validate a direct TLS handshake and certificate on the same TCP connection")
    demo = subs.add_parser("demo", help="Print deterministic synthetic output without network activity")
    demo.add_argument("--json", action="store_true", help="Machine-readable JSON output")

    args = parser.parse_args(argv)
    if args.command == "demo":
        report = demo_report()
    else:
        try:
            report = probe(args.host, args.port, args.timeout, tls=True) if args.tls else probe(args.host, args.port, args.timeout)
        except ValueError as exc:
            parser.error(str(exc))
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(format_text(report))
    return 0 if report["assessment"]["classification"] in {"tcp_connected", "tls_validated"} else 1

