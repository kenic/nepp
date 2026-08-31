"""Strict draft-03 V2 codec. V1 and the obsolete 128-byte V2 are not accepted."""

from dataclasses import dataclass
from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR
from enum import IntEnum
import secrets
import struct

from .packet import Mode, Packet, Status
from .timestamp import EarthDate, ZERO

VERSION = 2
PACKET_SIZE = 160
UNKNOWN = 0xFFFFFFFF
_QUALITY = struct.Struct("!BBBBIIIII")
_SOLAR = struct.Struct("!QqI")


class Supply(IntEnum):
    UNAVAILABLE = 0
    TRACKING = 1
    HOLDOVER = 2
    UNKNOWN = 3


class SourceKind(IntEnum):
    UNKNOWN = 0
    ASTRONOMICAL = 1
    DIRECT = 2
    NEPP = 3
    MIXED = 4


@dataclass(frozen=True)
class Quality:
    state: int = 0
    source_kind: int = 0
    flags: int = 0
    stratum: int = 0
    reference_id: int = 0
    uncertainty: int = 0
    validity: int = 0
    data_age: int = 0
    update_age: int = 0

    @property
    def evaluated(self):
        return bool(self.flags & 1)

    @property
    def prediction(self):
        return (self.flags >> 1) & 3

    def validate(self, solar=False):
        if self.state not in tuple(Supply):
            raise ValueError("reserved supply state")
        if self.state == Supply.UNAVAILABLE:
            if self != Quality():
                raise ValueError("unavailable quality must be all zero")
            return
        if self.flags & 0xF8 or self.prediction == 3:
            raise ValueError("reserved quality flags")
        if not 0 <= self.stratum <= 15 or (not solar and self.stratum == 0):
            raise ValueError("invalid coordinate stratum")
        if self.validity != UNKNOWN and not 0 <= self.validity <= 3600:
            raise ValueError("reserved validity")
        if self.evaluated:
            if self.uncertainty == UNKNOWN or self.validity == UNKNOWN:
                raise ValueError("evaluated uncertainty requires bound and validity")
            if solar and self.uncertainty >= 0x80000000:
                raise ValueError("solar bound must be less than half a turn")
        elif self.uncertainty != UNKNOWN:
            raise ValueError("unknown uncertainty must use sentinel")

    def pack(self):
        try:
            return _QUALITY.pack(self.state, self.source_kind, self.flags,
                                 self.stratum, self.reference_id, self.uncertainty,
                                 self.validity, self.data_age, self.update_age)
        except (struct.error, OverflowError) as error:
            raise ValueError("quality field outside wire range") from error

    @classmethod
    def unpack(cls, data):
        if len(data) != 24:
            raise ValueError("quality descriptor must be 24 bytes")
        return cls(*_QUALITY.unpack(data))

    @classmethod
    def unassessed(cls, *, stratum=1, reference_id=0, validity=UNKNOWN,
                   source_kind=SourceKind.ASTRONOMICAL, prediction=0):
        return cls(Supply.TRACKING, source_kind, prediction << 1, stratum,
                   reference_id, UNKNOWN, validity, UNKNOWN, 0)


@dataclass(frozen=True)
class V2Packet:
    base: Packet
    token: bytes
    phase: int = 0
    phase_rate: int = 0
    solar_model: int = 0
    ed_quality: Quality = Quality()
    sp_quality: Quality = Quality()

    def pack(self):
        if self.base.version != VERSION or self.base.extensions:
            raise ValueError("V2 base must have version 2 and no extensions")
        if len(self.token) != 16:
            raise ValueError("token must be 16 bytes")
        try:
            solar = _SOLAR.pack(self.phase, self.phase_rate, self.solar_model)
        except (struct.error, OverflowError) as error:
            raise ValueError("solar field outside wire range") from error
        return (self.base.pack() + self.token + solar + self.ed_quality.pack()
                + self.sp_quality.pack())

    @classmethod
    def unpack(cls, data):
        if len(data) != PACKET_SIZE or ((data[0] >> 3) & 7) != VERSION:
            raise ValueError("expected draft-03 V2, exactly 160 bytes")
        # Decoding is separate from per-coordinate semantic validation so that
        # invalid SP need not discard independently usable ED.
        base = Packet.unpack(data[:76])
        return cls(base, data[76:92], *_SOLAR.unpack(data[92:112]),
                   Quality.unpack(data[112:136]), Quality.unpack(data[136:160]))

    @classmethod
    def request(cls, transmit=ZERO, poll=6, token=None):
        if token is None:
            token = secrets.token_bytes(16)
            while not any(token):
                token = secrets.token_bytes(16)
        packet = cls(Packet(version=2, mode=Mode.CLIENT, precision=0,
                            transmit=transmit, poll=poll), token)
        packet.validate_request()
        return packet

    def validate_request(self):
        if not any(self.token):
            raise ValueError("zero request token")
        expected = V2Packet(Packet(version=2, mode=Mode.CLIENT, precision=0,
                                   poll=self.base.poll, transmit=self.base.transmit),
                            self.token)
        if self.pack() != expected.pack():
            raise ValueError("noncanonical V2 request")

    def validate_ed(self):
        b, q = self.base, self.ed_quality
        q.validate()
        if b.mode != Mode.SERVER or not any(self.token):
            raise ValueError("not a server response")
        if q.state == Supply.UNAVAILABLE or b.status == Status.UNSYNCHRONIZED:
            raise ValueError("ED unavailable")
        if b.model_id != 1 or b.rate <= 0 or b.receive == ZERO or b.transmit == ZERO:
            raise ValueError("unsupported or invalid ED")
        if (q.stratum, q.reference_id) != (b.stratum, b.reference_id):
            raise ValueError("ED quality and base fields disagree")
        expected = {Supply.TRACKING: (Status.SYNCHRONIZED, Status.DEGRADED),
                    Supply.HOLDOVER: (Status.HOLDOVER,),
                    Supply.UNKNOWN: (Status.DEGRADED,)}
        if b.status not in expected[q.state]:
            raise ValueError("ED supply and status disagree")
        if not q.evaluated and b.root_dispersion != UNKNOWN:
            raise ValueError("unassessed ED must have unknown dispersion")

    def validate_sp(self):
        self.sp_quality.validate(solar=True)
        if self.sp_quality.state == Supply.UNAVAILABLE:
            if self.phase or self.phase_rate or self.solar_model:
                raise ValueError("unavailable SP must be zero")
            return False
        if self.solar_model != 1 or self.phase_rate <= 0:
            raise ValueError("unsupported or invalid SP")
        return True

    def validate_for(self, request):
        # Endpoint matching and one-shot consumption belong to the transport.
        if self.token != request.token or self.base.origin != request.base.transmit:
            raise ValueError("token or origin mismatch")
        self.validate_ed()


def phase_to_wire(value):
    value = Decimal(str(value))
    if not value.is_finite() or not 0 <= value < 1:
        raise ValueError("phase must be in [0,1)")
    return int((value * (1 << 64)).to_integral_value(rounding=ROUND_FLOOR))


def uncertainty_to_wire(value, solar=False):
    """Overflow is unknown, never a clamped claim of accuracy."""
    if value is None:
        return UNKNOWN
    value = Decimal(str(value))
    if not value.is_finite() or value < 0:
        raise ValueError("uncertainty must be finite and nonnegative")
    result = int((value * (1 << 32)).to_integral_value(rounding=ROUND_CEILING))
    limit = 0x80000000 if solar else UNKNOWN
    return result if result < limit else UNKNOWN
