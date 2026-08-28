"""NEPP's signed-year, unsigned-fraction 96-bit timestamp."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_FLOOR
import struct

FRACTION_SCALE = 1 << 64
TIMESTAMP_SIZE = 12


@dataclass(frozen=True, order=True)
class EarthDate:
    year: int
    fraction: int = 0

    def __post_init__(self) -> None:
        if not -(1 << 31) <= self.year < (1 << 31):
            raise ValueError("Earth Year is outside signed 32-bit range")
        if not 0 <= self.fraction < FRACTION_SCALE:
            raise ValueError("orbital fraction is outside unsigned 64-bit range")

    @classmethod
    def from_decimal(cls, value: Decimal | int | str) -> "EarthDate":
        value = Decimal(value)
        year = int(value.to_integral_value(rounding=ROUND_FLOOR))
        fraction = int(((value - year) * FRACTION_SCALE).to_integral_value(rounding=ROUND_FLOOR))
        return cls(year, fraction)

    @classmethod
    def unpack(cls, data: bytes) -> "EarthDate":
        if len(data) != TIMESTAMP_SIZE:
            raise ValueError("an NEPP timestamp must be exactly 12 octets")
        return cls(*struct.unpack("!iQ", data))

    def pack(self) -> bytes:
        return struct.pack("!iQ", self.year, self.fraction)

    def as_decimal(self) -> Decimal:
        return Decimal(self.year) + Decimal(self.fraction) / Decimal(FRACTION_SCALE)

    def difference(self, other: "EarthDate") -> Decimal:
        units = ((self.year - other.year) * FRACTION_SCALE +
                 self.fraction - other.fraction)
        return Decimal(units) / Decimal(FRACTION_SCALE)

    def __str__(self) -> str:
        return f"{self.as_decimal():.18f}"


ZERO = EarthDate(0, 0)
