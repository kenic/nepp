"""UDP server for NEPP Version 1."""

import argparse
import socket
from typing import Callable

from .clock import AstropyEarthDateClock, EarthDateClock
from .packet import Mode, Packet, Status, rate_to_wire

DEFAULT_PORT = 41234


def make_response(request: Packet, clock: EarthDateClock) -> Packet:
    if request.version != 1 or request.mode is not Mode.CLIENT:
        raise ValueError("request must be a Version 1 client packet")
    received = clock.now()
    rate = rate_to_wire(clock.rate())
    transmitted = clock.now()
    return Packet(status=Status.SYNCHRONIZED, mode=Mode.SERVER, stratum=1,
                  poll=request.poll, precision=-52,
                  reference_id=int.from_bytes(b"ASTR", "big"),
                  reference=received, origin=request.transmit, receive=received,
                  transmit=transmitted, rate=rate, model_id=1)


def serve(host: str, port: int, clock: EarthDateClock,
          stop: Callable[[], bool] = lambda: False) -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind((host, port))
        sock.settimeout(0.1)
        while not stop():
            try:
                data, address = sock.recvfrom(65535)
            except socket.timeout:
                continue
            try:
                response = make_response(Packet.unpack(data), clock)
            except (ValueError, OverflowError):
                continue
            sock.sendto(response.pack(), address)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run an experimental NEPP UDP server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    args = parser.parse_args()
    serve(args.host, args.port, AstropyEarthDateClock())


if __name__ == "__main__":
    main()
