"""Immutable source snapshots and bounded, off-request refresh/holdover."""

from dataclasses import dataclass, replace
from decimal import Decimal
import logging
import math
import threading
import time
from typing import Optional

from .packet import Mode, Packet, Status, rate_to_wire
from .timestamp import EarthDate
from .v2 import Quality, Supply, UNKNOWN, V2Packet, phase_to_wire

LOG = logging.getLogger("nepp.source")


@dataclass(frozen=True)
class SourceSample:
    """Provider contract: any evaluated bound covers the encoded linear model,
    quantization and local elapsed-time realization throughout validity.
    The built-in experimental provider deliberately makes no such claim.
    """
    epoch: float  # monotonic instant corresponding to the coordinate, not completion
    ed: EarthDate
    rate: float
    ed_quality: Quality
    phase: Optional[float] = None
    phase_rate: float = 0.0
    sp_quality: Quality = Quality()
    wall_epoch: Optional[float] = None

    def validate(self):
        if not math.isfinite(self.epoch) or not math.isfinite(self.rate) or self.rate <= 0:
            raise ValueError("invalid source epoch/rate")
        if self.ed.year == 0 and self.ed.fraction == 0:
            raise ValueError("source ED cannot be absent")
        self.ed_quality.validate()
        self.ed_quality.pack()
        if self.ed_quality.state == Supply.UNAVAILABLE:
            raise ValueError("source ED unavailable")
        rate_to_wire(self.rate)
        self.sp_quality.validate(solar=True)
        self.sp_quality.pack()
        if self.phase is None:
            if self.phase_rate or self.sp_quality != Quality():
                raise ValueError("absent solar state is not canonical")
        else:
            phase_to_wire(self.phase)
            if self.sp_quality.state == Supply.UNAVAILABLE or self.phase_rate <= 0:
                raise ValueError("invalid solar source state")
            rate_to_wire(self.phase_rate)
        if self.wall_epoch is not None and not math.isfinite(self.wall_epoch):
            raise ValueError("invalid source wall epoch")

    def ed_at(self, epoch):
        return EarthDate.from_decimal(self.ed.as_decimal()
                                     + Decimal(str(self.rate)) * Decimal(str(epoch - self.epoch)))


class CachedSource:
    """The source's acquire() supplies one coherent ED/SP snapshot.

    Failure retains bounded holdover; the request thread never calls acquire().
    Optional wall_epoch allows detection of host-clock steps or suspend gaps.
    """

    def __init__(self, source, refresh_interval=60.0, max_age=3600.0,
                 monotonic=None, wall_clock=None):
        if (not math.isfinite(refresh_interval) or not math.isfinite(max_age)
                or not 0 < refresh_interval <= max_age <= 3600):
            raise ValueError("require 0 < refresh <= max-age <= 3600 seconds")
        self.source = source
        self.refresh_interval = refresh_interval
        self.max_age = max_age
        self.monotonic = monotonic or time.monotonic
        self.wall_clock = wall_clock or time.time
        self._lock = threading.Lock()
        self._refresh_lock = threading.Lock()
        self._stop = threading.Event()
        self._thread = None
        self._sample = None
        self.last_error = None
        self.refresh()

    def refresh(self):
        with self._refresh_lock:
            try:
                sample = self.source.acquire()
                sample.validate()
                if sample.epoch > self.monotonic():
                    raise ValueError("source anchor is in the future")
            except Exception as error:
                with self._lock:
                    first_failure = self.last_error is None
                    self.last_error = error
                if first_failure:
                    LOG.warning("source refresh failed; bounded holdover or unavailable: %s", error)
                return False
            with self._lock:
                self._sample = sample
                self.last_error = None
            return True

    def snapshot(self):
        with self._lock:
            sample, failed = self._sample, self.last_error is not None
        if sample is not None and sample.wall_epoch is not None:
            elapsed = self.monotonic() - sample.epoch
            if abs((self.wall_clock() - sample.wall_epoch) - elapsed) > 1.0:
                # Do not interpret a wall-clock step or sleep gap as ED elapsed time.
                return None, True
        return sample, failed

    def start(self):
        if self._thread is None:
            self._thread = threading.Thread(target=self._loop, daemon=True,
                                            name="nepp-source-refresh")
            self._thread.start()

    def _loop(self):
        while not self._stop.wait(self.refresh_interval):
            self.refresh()

    def close(self):
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=2)


def _age(value, elapsed):
    if value == UNKNOWN:
        return UNKNOWN
    age = value + math.ceil(elapsed)
    return age if 0 <= age < UNKNOWN else UNKNOWN


def propagate_quality(q, elapsed, max_age, failed=False, earlier_receive=False):
    if q.state == Supply.UNAVAILABLE:
        return q
    if elapsed < 0 or elapsed > max_age:
        return Quality()
    expired = q.validity != UNKNOWN and elapsed > q.validity
    holdover = failed or expired or q.state == Supply.HOLDOVER
    # Past the supplied interval or after a source failure, never renew a bound.
    invalidate_bound = expired or failed or earlier_receive
    flags = q.flags & ~1 if invalidate_bound else q.flags
    if holdover:
        flags = (flags & ~6) | 4  # known extrapolation/prediction
    validity = UNKNOWN if expired else q.validity
    if validity != UNKNOWN:
        validity = max(0, math.floor(min(q.validity - elapsed, max_age - elapsed)))
    return replace(q, state=Supply.HOLDOVER if holdover else q.state,
                   flags=flags, uncertainty=UNKNOWN if invalidate_bound else q.uncertainty,
                   validity=validity, data_age=_age(q.data_age, elapsed),
                   update_age=_age(q.update_age, elapsed))


def build_response(request, sample, received, transmitted, *, max_age=3600, failed=False):
    """No astronomical work; E2/E3 and solar fields use one immutable snapshot."""
    request.validate_request()
    base = Packet(version=2, mode=Mode.SERVER, precision=-40,
                  poll=request.base.poll, origin=request.base.transmit,
                  root_delay=UNKNOWN, root_dispersion=UNKNOWN)
    if transmitted < received or not all(map(math.isfinite, (received, transmitted))):
        raise ValueError("invalid local exchange times")
    if sample is None or transmitted < sample.epoch or transmitted - sample.epoch > max_age:
        return V2Packet(base, request.token)
    elapsed = transmitted - sample.epoch
    edq = propagate_quality(sample.ed_quality, elapsed, max_age, failed,
                            earlier_receive=received < sample.epoch)
    spq = propagate_quality(sample.sp_quality, elapsed, max_age, failed)
    if not edq.state:
        return V2Packet(base, request.token)
    status = {Supply.TRACKING: Status.SYNCHRONIZED, Supply.HOLDOVER: Status.HOLDOVER,
              Supply.UNKNOWN: Status.DEGRADED}[edq.state]
    base = replace(base, status=status, stratum=edq.stratum,
                   reference_id=edq.reference_id, reference=sample.ed,
                   receive=sample.ed_at(received), transmit=sample.ed_at(transmitted),
                   rate=rate_to_wire(sample.rate), model_id=1)
    phase = phase_rate = model = 0
    if sample.phase is not None and spq.state:
        # Decimal modulo keeps a value just below 1 from rounding to 1.0.
        value = (Decimal(str(sample.phase)) + Decimal(str(sample.phase_rate))
                 * Decimal(str(elapsed))) % 1
        phase = phase_to_wire(value)
        phase_rate = rate_to_wire(sample.phase_rate)
        model = 1
    response = V2Packet(base, request.token, phase, phase_rate, model, edq, spq)
    response.validate_ed()
    response.validate_sp()
    return response
