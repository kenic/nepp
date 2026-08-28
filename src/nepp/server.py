"""UDP server for NEPP Version 1."""

import argparse
from collections import defaultdict
import logging
import signal
import socket
import threading
import time
from typing import Callable

from .clock import AstropyEarthDateClock, CachedEarthDateClock, EarthDateClock
from .packet import Mode, Packet, Status, rate_to_wire

DEFAULT_PORT = 56377
LOG = logging.getLogger("nepp.server")


class RateLimiter:
    """Small per-address token bucket for an unauthenticated UDP service."""

    def __init__(self, rate: float = 2.0, burst: float = 8.0,
                 clock: Callable[[], float] = time.monotonic):
        if rate <= 0 or burst < 1:
            raise ValueError("rate and burst must be positive")
        self.rate, self.burst, self.clock = rate, burst, clock
        self._clients = {}
        self._requests = 0

    def allow(self, address: str) -> bool:
        now = self.clock()
        tokens, updated = self._clients.get(address, (self.burst, now))
        tokens = min(self.burst, tokens + (now - updated) * self.rate)
        allowed = tokens >= 1
        self._clients[address] = (tokens - 1 if allowed else tokens, now)
        self._requests += 1
        if self._requests % 4096 == 0:
            cutoff = now - max(300.0, self.burst / self.rate * 4)
            self._clients = {key: value for key, value in self._clients.items()
                             if value[1] >= cutoff}
        return allowed


def make_response(request: Packet, clock: EarthDateClock) -> Packet:
    if request.version != 1 or request.mode is not Mode.CLIENT:
        raise ValueError("request must be a Version 1 client packet")
    received = clock.now()
    rate = rate_to_wire(clock.rate())
    transmitted = clock.now()
    status = Status.HOLDOVER if getattr(clock, "last_error", None) else Status.SYNCHRONIZED
    return Packet(status=status, mode=Mode.SERVER, stratum=1,
                  poll=request.poll, precision=-52,
                  reference_id=int.from_bytes(b"ASTR", "big"),
                  reference=received, origin=request.transmit, receive=received,
                  transmit=transmitted, rate=rate, model_id=1)


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


def serve(host: str, port: int, clock: EarthDateClock,
          stop: Callable[[], bool] = lambda: False,
          limiter: RateLimiter = None) -> None:
    limiter = limiter or RateLimiter()
    accepted = rejected = 0
    with _server_socket(host, port) as sock:
        sock.settimeout(0.1)
        LOG.info("listening on %s:%d/udp", host, port)
        while not stop():
            try:
                data, address = sock.recvfrom(65535)
            except socket.timeout:
                continue
            if not limiter.allow(address[0]):
                rejected += 1
                continue
            try:
                response = make_response(Packet.unpack(data), clock)
            except (ValueError, OverflowError):
                rejected += 1
                continue
            sock.sendto(response.pack(), address)
            accepted += 1
        LOG.info("stopped after %d responses and %d rejected packets", accepted, rejected)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run an experimental NEPP UDP server")
    parser.add_argument("--host", default="::",
                        help="address to bind (default: ::, dual-stack where supported)")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--refresh", type=float, default=300.0,
                        help="astronomical clock refresh interval in seconds")
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
    clock = CachedEarthDateClock(AstropyEarthDateClock(), args.refresh)
    clock.start()
    try:
        serve(args.host, args.port, clock, stopped.is_set,
              RateLimiter(args.rate_limit, args.burst))
    finally:
        clock.close()


if __name__ == "__main__":
    main()
