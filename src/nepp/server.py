"""Experimental draft-03 V2-only UDP server; legacy requests are dropped."""

import argparse
from collections import OrderedDict
import ipaddress
import math
import logging
import signal
import socket
import threading
import time
from typing import Callable

from .astronomy import BasicAstronomicalSource
from .source import CachedSource, build_response
from .v2 import V2Packet, PACKET_SIZE

DEFAULT_PORT = 56377
LOG = logging.getLogger("nepp.server")


class RateLimiter:
    """Small per-address token bucket for an unauthenticated UDP service."""

    def __init__(self, rate: float = 2.0, burst: float = 8.0,
                 clock: Callable[[], float] = time.monotonic,
                 max_clients=4096):
        if not math.isfinite(rate) or not math.isfinite(burst) or rate <= 0 or burst < 1 or max_clients < 1:
            raise ValueError("rate and burst must be positive")
        self.rate, self.burst, self.clock = rate, burst, clock
        self._clients = OrderedDict()
        self.max_clients = max_clients
        self._global = (400.0, clock())

    def allow(self, address: str) -> bool:
        now = self.clock()
        tokens, updated = self._global
        tokens = min(400.0, tokens + max(0, now - updated) * 200.0)
        self._global = (tokens - 1 if tokens >= 1 else tokens, now)
        if tokens < 1:
            return False
        ip = ipaddress.ip_address(address)
        address = str(getattr(ip, 'ipv4_mapped', None) or ip)
        tokens, updated = self._clients.pop(address, (self.burst, now))
        tokens = min(self.burst, tokens + (now - updated) * self.rate)
        allowed = tokens >= 1
        self._clients[address] = (tokens - 1 if allowed else tokens, now)
        if len(self._clients) > self.max_clients:
            self._clients.popitem(last=False)
        return allowed


def _server_socket(host: str, port: int) -> socket.socket:
    candidates = socket.getaddrinfo(host, port, socket.AF_UNSPEC, socket.SOCK_DGRAM,
                                    socket.IPPROTO_UDP, socket.AI_PASSIVE)
    candidates.sort(key=lambda item: item[0] != socket.AF_INET6)
    last_error = None
    for family, kind, protocol, _, address in candidates:
        sock = socket.socket(family, kind, protocol)
        try:
            if family == socket.AF_INET6:
                try:
                    sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
                except OSError:
                    pass
            sock.bind(address)
            return sock
        except OSError as error:
            last_error = error
            sock.close()
    raise last_error or OSError("no usable UDP address")


def serve(host: str, port: int, clock: CachedSource,
          stop: Callable[[], bool] = lambda: False,
          limiter: RateLimiter = None, on_bound=None) -> None:
    limiter = limiter or RateLimiter()
    accepted = rejected = 0
    with _server_socket(host, port) as sock:
        sock.settimeout(0.1)
        LOG.info("V2-only listening on %s", sock.getsockname())
        if on_bound:
            on_bound(sock.getsockname())
        while not stop():
            try:
                data, address = sock.recvfrom(65535)
                received = clock.monotonic()
            except socket.timeout:
                continue
            if not limiter.allow(address[0]):
                rejected += 1
                continue
            try:
                if len(data) != PACKET_SIZE:
                    raise ValueError("wrong packet length")
                request = V2Packet.unpack(data)
                request.validate_request()
                sample, failed = clock.snapshot()
                response = build_response(request, sample, received, clock.monotonic(),
                                          max_age=clock.max_age, failed=failed)
            except (ValueError, OverflowError):
                rejected += 1
                continue
            try:
                sock.sendto(response.pack(), address)
            except OSError:
                rejected += 1
                continue
            accepted += 1
        LOG.info("stopped after %d responses and %d rejected packets", accepted, rejected)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run an experimental NEPP UDP server")
    parser.add_argument("--host", default="::",
                        help="address to bind (default: ::, dual-stack where supported)")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--refresh", type=float, default=60.0,
                        help="astronomical clock refresh interval in seconds")
    parser.add_argument("--max-age", type=float, default=3600,
                        help="maximum snapshot age before declaring unavailable")
    parser.add_argument("--offline", action="store_true", help="use bundled IERS data only")
    parser.add_argument("--http-port", type=int, help="enable loopback HTTP API for Caddy")
    parser.add_argument("--web-root", help="also serve Web assets under /web/ (local development)")
    parser.add_argument("--rate-limit", type=float, default=2.0,
                        help="accepted requests per second per source address")
    parser.add_argument("--burst", type=float, default=8.0,
                        help="per-source request burst allowance")
    parser.add_argument("--log-level", choices=("DEBUG", "INFO", "WARNING", "ERROR"),
                        default="INFO")
    args = parser.parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level),
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    stopped = threading.Event()
    for signum in (signal.SIGINT, signal.SIGTERM):
        signal.signal(signum, lambda _signum, _frame: stopped.set())
    if not 0 <= args.port <= 65535:
        parser.error("port must be 0..65535")
    if args.http_port is not None and not 0 <= args.http_port <= 65535:
        parser.error("HTTP port must be 0..65535")
    if args.web_root and args.http_port is None:
        parser.error("--web-root requires --http-port")
    if args.offline:
        from astropy.utils import iers
        iers.conf.auto_download = False
    clock = CachedSource(BasicAstronomicalSource(), args.refresh, args.max_age)
    clock.start()
    http = None
    try:
        if args.http_port is not None:
            from .web import start_http
            http = start_http(clock, args.http_port, args.web_root)
            LOG.info("Web preview/API: http://127.0.0.1:%s/web/", http.server_port)
        serve(args.host, args.port, clock, stopped.is_set,
              RateLimiter(args.rate_limit, args.burst))
    finally:
        if http:
            http.shutdown()
            http.server_close()
        clock.close()


if __name__ == "__main__":
    main()
