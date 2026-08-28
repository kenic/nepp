"""UDP client and four-coordinate calculation for NEPP Version 1."""

import argparse
from dataclasses import dataclass
from decimal import Decimal
import socket

from .clock import AstropyEarthDateClock, EarthDateClock
from .packet import Mode, Packet, Status
from .server import DEFAULT_PORT
from .timestamp import EarthDate


@dataclass(frozen=True)
class SynchronizationResult:
    response: Packet
    destination: EarthDate
    offset: Decimal
    round_trip: Decimal


def calculate(response: Packet, sent: EarthDate,
              destination: EarthDate) -> SynchronizationResult:
    if response.version != 1 or response.mode is not Mode.SERVER:
        raise ValueError("response is not a Version 1 server packet")
    if response.status is Status.UNSYNCHRONIZED or response.stratum > 15:
        raise ValueError("server is unsynchronized")
    if response.origin != sent:
        raise ValueError("response origin does not match the request")
    offset = (response.receive.difference(sent) +
              response.transmit.difference(destination)) / 2
    round_trip = (destination.difference(sent) -
                  response.transmit.difference(response.receive))
    return SynchronizationResult(response, destination, offset, round_trip)


def query(host: str, port: int, clock: EarthDateClock,
          timeout: float = 2.0) -> SynchronizationResult:
    sent = clock.now()
    request = Packet(mode=Mode.CLIENT, transmit=sent)
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.settimeout(timeout)
        sock.sendto(request.pack(), (host, port))
        data, _ = sock.recvfrom(65535)
        destination = clock.now()
    return calculate(Packet.unpack(data), sent, destination)


def main() -> None:
    parser = argparse.ArgumentParser(description="Query an experimental NEPP UDP server")
    parser.add_argument("host")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--timeout", type=float, default=2.0)
    args = parser.parse_args()
    result = query(args.host, args.port, AstropyEarthDateClock(), args.timeout)
    print(f"earth_date={result.response.transmit}")
    print(f"offset_ed={result.offset}")
    print(f"round_trip_ed={result.round_trip}")
    print(f"stratum={result.response.stratum}")
    print(f"model_id={result.response.model_id}")


if __name__ == "__main__":
    main()
