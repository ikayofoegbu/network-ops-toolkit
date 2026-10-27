"""Single-target, bounded TCP connectivity diagnostics.

This module reports observations, not inferred root causes. Resolver and connector
injection allows all test cases to execute without touching a real network.
"""

from __future__ import annotations

import errno
import ipaddress
import re
import socket
import ssl
from time import perf_counter
from typing import Any, Callable

from .tls import annotate_report, client_context, handshake, validate_context

MAX_ADDRESSES = 8
_FAMILY_NAMES = {socket.AF_INET: "IPv4", socket.AF_INET6: "IPv6"}
_UNREACHABLE_CODES = {errno.ENETUNREACH, errno.EHOSTUNREACH, 10051, 10065}
_PERMISSION_CODES = {errno.EACCES, errno.EPERM, 10013}
_HOST_LABEL = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?$")

# socket.getaddrinfo-compatible signature. Connectors receive an addrinfo tuple.
Resolver = Callable[..., list[tuple[Any, ...]]]
Connector = Callable[[tuple[Any, ...], float], dict[str, Any]]


def validate_target(host: str, port: int, timeout: float) -> None:
    """Reject likely input mistakes before any resolution or network activity."""
    if not host or host != host.strip() or len(host) > 253:
        raise ValueError("host must be a nonempty hostname or IP address (up to 253 characters)")
    if not isinstance(port, int) or isinstance(port, bool) or not 1 <= port <= 65535:
        raise ValueError("port must be an integer from 1 to 65535")
    if not 0.1 <= timeout <= 10.0:
        raise ValueError("timeout must be between 0.1 and 10 seconds")
    try:
        ipaddress.ip_address(host)
    except ValueError:
        candidate = host[:-1] if host.endswith(".") else host
        if not candidate or any(not _HOST_LABEL.fullmatch(label) for label in candidate.split(".")):
            raise ValueError("host must be a hostname or IP address, not a URL or path") from None


def _attempt(
    info: tuple[Any, ...], timeout: float, *,
    server_hostname: str | None = None, tls_context: ssl.SSLContext | None = None,
) -> dict[str, Any]:
    """Try one TCP connection and classify only directly observed socket results."""
    family, socktype, proto, _, sockaddr = info
    started = perf_counter()
    outcome = "connected"
    error_code: int | None = None
    tcp_elapsed: float | None = None
    tls_result: dict[str, Any] = {"status": "not_run"}
    try:
        with socket.socket(family, socktype, proto) as connection:
            connection.settimeout(timeout)
            connection.connect(sockaddr)
            tcp_elapsed = (perf_counter() - started) * 1000
            if tls_context is not None:
                tls_result = handshake(connection, tls_context, server_hostname)
    except ConnectionRefusedError as exc:
        outcome, error_code = "refused", exc.errno
    except TimeoutError as exc:
        outcome, error_code = "timeout", exc.errno
    except PermissionError as exc:
        outcome, error_code = "permission_denied", exc.errno
    except OSError as exc:
        code = exc.errno if exc.errno is not None else getattr(exc, "winerror", None)
        error_code = code
        if code in _UNREACHABLE_CODES:
            outcome = "network_unreachable"
        elif code in _PERMISSION_CODES:
            outcome = "permission_denied"
        else:
            outcome = "socket_error"
    result: dict[str, Any] = {
        "address": sockaddr[0],
        "family": _FAMILY_NAMES[family],
        "outcome": outcome,
        "elapsed_ms": round(tcp_elapsed if tcp_elapsed is not None else (perf_counter() - started) * 1000, 2),
    }
    if tls_context is not None:
        result["tls"] = tls_result
    if error_code is not None:
        result["os_error_code"] = error_code
    return result


def _assessment(dns_status: str, attempts: list[dict[str, Any]]) -> dict[str, Any]:
    if dns_status == "failed":
        return {
            "classification": "dns_failed",
            "interpretation": "The hostname could not be resolved. This does not identify the cause.",
            "next_checks": ["Check the hostname for mistakes.", "Check resolver settings and DNS reachability."],
        }
    outcomes = {entry["outcome"] for entry in attempts}
    if "connected" in outcomes:
        return {
            "classification": "tcp_connected",
            "interpretation": "At least one TCP handshake succeeded. Application health was not tested.",
            "next_checks": ["If the application still fails, check TLS and application-layer responses."],
        }
    if "refused" in outcomes:
        return {
            "classification": "tcp_failed",
            "interpretation": "At least one address refused the TCP connection; no connection succeeded. The rejecting device is not identified.",
            "next_checks": ["Confirm the service is listening on the selected port.", "Check endpoint and intermediary policies."],
        }
    if "timeout" in outcomes:
        return {
            "classification": "tcp_failed",
            "interpretation": "A TCP attempt timed out. Filtering, routing, and endpoint behavior are possibilities, not proven causes.",
            "next_checks": ["Check path and firewall policies using authorized tooling.", "Check the endpoint's availability."],
        }
    if "network_unreachable" in outcomes:
        return {
            "classification": "tcp_failed",
            "interpretation": "The operating system reported an unreachable network or host.",
            "next_checks": ["Inspect local routing, interfaces and VPN configuration."],
        }
    if "permission_denied" in outcomes:
        return {
            "classification": "tcp_failed",
            "interpretation": "The operating system denied a socket operation.",
            "next_checks": ["Review local device permissions and security policy."],
        }
    return {
        "classification": "tcp_failed",
        "interpretation": "TCP connectivity was not established. Inspect the individual address outcomes.",
        "next_checks": ["Review the recorded per-address errors before deciding what to test next."],
    }


def probe(
    host: str,
    port: int,
    timeout: float = 2.0,
    *,
    resolver: Resolver | None = None,
    connector: Connector | None = None,
    tls: bool = False,
    tls_context: ssl.SSLContext | None = None,
) -> dict[str, Any]:
    """Resolve one host and try up to MAX_ADDRESSES distinct addresses in order.

    The timeout is per TCP connect and optional TLS handshake, not an overall
    deadline. No ping, scanning or application-layer checks are performed.
    Optional direct TLS validates the
    certificate and requested hostname on the same TCP connection.
    """
    validate_target(host, port, timeout)
    if tls_context is not None and not tls:
        raise ValueError("tls_context requires tls=True")
    server_hostname = host.rstrip(".")
    if tls:
        tls_context = tls_context if tls_context is not None else client_context()
        validate_context(tls_context)
    resolver = resolver if resolver is not None else socket.getaddrinfo
    if connector is None:
        if tls:
            connector = lambda info, limit: _attempt(info, limit, server_hostname=server_hostname, tls_context=tls_context)
        else:
            connector = _attempt
    started = perf_counter()

    try:
        records = resolver(host, port, family=socket.AF_UNSPEC, type=socket.SOCK_STREAM)
    except (socket.gaierror, OSError) as exc:
        report = {
            "schema_version": 1,
            "target": {"host": host, "port": port, "timeout_per_address_seconds": timeout},
            "dns": {"status": "failed", "addresses": [], "error_code": getattr(exc, "errno", None)},
            "tcp": {"status": "not_run", "attempts": [], "skipped_addresses": 0},
            "assessment": _assessment("failed", []),
        }
        report["duration_ms"] = round((perf_counter() - started) * 1000, 2)
        return annotate_report(report, server_hostname) if tls else report

    distinct: list[tuple[Any, ...]] = []
    seen: set[tuple[Any, ...]] = set()
    for record in records:
        family, socktype, proto, _, sockaddr = record
        if family not in _FAMILY_NAMES:
            continue
        key = (family, sockaddr[0])
        if key not in seen:
            seen.add(key)
            distinct.append((family, socktype, proto, "", sockaddr))

    addresses = [{"address": item[4][0], "family": _FAMILY_NAMES[item[0]]} for item in distinct]
    limited = distinct[:MAX_ADDRESSES]
    attempts = [connector(info, timeout) for info in limited]
    connected = any(result["outcome"] == "connected" for result in attempts)
    report = {
        "schema_version": 1,
        "target": {"host": host, "port": port, "timeout_per_address_seconds": timeout},
        "dns": {"status": "resolved" if distinct else "no_addresses", "addresses": addresses},
        "tcp": {
            "status": "connected" if connected else ("failed" if attempts else "not_run"),
            "attempts": attempts,
            "skipped_addresses": max(0, len(distinct) - len(limited)),
        },
        "assessment": _assessment("resolved", attempts),
    }
    if not distinct:
        report["assessment"] = {
            "classification": "no_usable_addresses",
            "interpretation": "The resolver returned no usable IPv4 or IPv6 TCP addresses.",
            "next_checks": ["Check the hostname, local network stack and DNS records."],
        }
    report["duration_ms"] = round((perf_counter() - started) * 1000, 2)
    return annotate_report(report, server_hostname) if tls else report


def demo_report() -> dict[str, Any]:
    """An explicitly synthetic example. Performs zero network operations."""
    def fake_resolver(host: str, port: int, **_: Any) -> list[tuple[Any, ...]]:
        return [(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", ("192.0.2.10", port))]

    def fake_connector(info: tuple[Any, ...], timeout: float) -> dict[str, Any]:
        return {"address": info[4][0], "family": "IPv4", "outcome": "connected", "elapsed_ms": 12.4}

    report = probe("demo.example", 443, resolver=fake_resolver, connector=fake_connector)
    report["duration_ms"] = 12.4
    report["synthetic_demo"] = True
    return report

