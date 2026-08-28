"""NEPP Version 1 base-packet codec."""

from dataclasses import dataclass
from enum import IntEnum
import struct

from .timestamp import EarthDate, ZERO

VERSION = 1
BASE_PACKET_SIZE = 76
_HEADER = struct.Struct("!BBBBIII")
_TRAILER = struct.Struct("!qI")


class Status(IntEnum):
    SYNCHRONIZED = 0
    DEGRADED = 1
    HOLDOVER = 2
    UNSYNCHRONIZED = 3


class Mode(IntEnum):
    RESERVED = 0
    SYMMETRIC_ACTIVE = 1
    SYMMETRIC_PASSIVE = 2
    CLIENT = 3
    SERVER = 4
    BROADCAST = 5


@dataclass(frozen=True)
class Packet:
    status: Status = Status.UNSYNCHRONIZED
    version: int = VERSION
    mode: Mode = Mode.CLIENT
    stratum: int = 16
    poll: int = 6
    precision: int = -52
    root_delay: int = 0
    root_dispersion: int = 0
    reference_id: int = 0
    reference: EarthDate = ZERO
    origin: EarthDate = ZERO
    receive: EarthDate = ZERO
    transmit: EarthDate = ZERO
    rate: int = 0
    model_id: int = 0
    extensions: bytes = b""

    def __post_init__(self) -> None:
        if not 0 <= self.version <= 7:
            raise ValueError("version must fit in 3 bits")
        if not 0 <= self.stratum <= 255:
            raise ValueError("stratum must fit in one octet")
        if not -128 <= self.poll <= 127 or not -128 <= self.precision <= 127:
            raise ValueError("poll and precision must be signed octets")
        for name in ("root_delay", "root_dispersion", "reference_id", "model_id"):
            if not 0 <= getattr(self, name) <= 0xFFFFFFFF:
                raise ValueError(f"{name} must be an unsigned 32-bit integer")
        if not -(1 << 63) <= self.rate < (1 << 63):
            raise ValueError("rate must be a signed 64-bit integer")

    @property
    def rate_ed_per_second(self) -> float:
        return self.rate / (1 << 63)

    def pack(self) -> bytes:
        flags = (int(self.status) << 6) | (self.version << 3) | int(self.mode)
        head = _HEADER.pack(flags, self.stratum, self.poll & 0xFF,
                            self.precision & 0xFF, self.root_delay,
                            self.root_dispersion, self.reference_id)
        stamps = b"".join(x.pack() for x in
                          (self.reference, self.origin, self.receive, self.transmit))
        return head + stamps + _TRAILER.pack(self.rate, self.model_id) + self.extensions

    @classmethod
    def unpack(cls, data: bytes) -> "Packet":
        if len(data) < BASE_PACKET_SIZE:
            raise ValueError("NEPP packet is shorter than 76 octets")
        flags, stratum, poll, precision, delay, dispersion, ref_id = _HEADER.unpack(data[:16])
        try:
            status = Status(flags >> 6)
            mode = Mode(flags & 7)
        except ValueError as error:
            raise ValueError("packet contains a reserved value") from error
        stamps = [EarthDate.unpack(data[n:n + 12]) for n in (16, 28, 40, 52)]
        rate, model_id = _TRAILER.unpack(data[64:76])
        return cls(status, (flags >> 3) & 7, mode, stratum,
                   _signed_octet(poll), _signed_octet(precision), delay,
                   dispersion, ref_id, *stamps, rate, model_id, data[76:])


def _signed_octet(value: int) -> int:
    return value - 256 if value >= 128 else value


def seconds_to_short(value: float) -> int:
    if value < 0:
        raise ValueError("delay cannot be negative")
    return min(round(value * 65536), 0xFFFFFFFF)


def rate_to_wire(rate: float) -> int:
    encoded = round(rate * (1 << 63))
    if not -(1 << 63) <= encoded < (1 << 63):
        raise ValueError("rate cannot be represented")
    return encoded
