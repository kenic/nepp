"""Earth Date clock interface and experimental Astropy realization."""

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
import logging
import threading
import time
from typing import Protocol

from .timestamp import EarthDate

LOG = logging.getLogger("nepp.clock")


class EarthDateClock(Protocol):
    def now(self) -> EarthDate: ...
    def rate(self) -> float: ...


@dataclass
class AstropyEarthDateClock:
    derivative_interval: float = 30.0

    @staticmethod
    def _value_at(unix_seconds: float) -> float:
        try:
            from astropy.coordinates import GeocentricTrueEcliptic, get_sun
            from astropy.time import Time
        except ImportError as error:
            raise RuntimeError("install NEPP with the 'astronomy' extra") from error
        instant = Time(unix_seconds, format="unix", scale="utc")
        longitude = get_sun(instant).transform_to(
            GeocentricTrueEcliptic(equinox=instant)).lon.to_value("deg") % 360.0
        civil = datetime.fromtimestamp(unix_seconds, timezone.utc)
        before_march_equinox = civil.month < 3 or (civil.month == 3 and longitude > 180.0)
        year = civil.year - (1 if before_march_equinox else 0)
        return year + longitude / 360.0

    def now(self) -> EarthDate:
        value = self._value_at(datetime.now(timezone.utc).timestamp())
        return EarthDate.from_decimal(str(value))

    def rate(self) -> float:
        center = datetime.now(timezone.utc).timestamp()
        width = self.derivative_interval
        return (self._value_at(center + width) - self._value_at(center - width)) / (2 * width)


class CachedEarthDateClock:
    """Interpolate a costly astronomical clock between periodic refreshes."""

    def __init__(self, source: EarthDateClock, refresh_interval: float = 300.0):
        if refresh_interval <= 0:
            raise ValueError("refresh interval must be positive")
        self.source = source
        self.refresh_interval = refresh_interval
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread = None
        self._anchor = EarthDate(0)
        self._anchor_monotonic = 0.0
        self._rate = 0.0
        self.last_error = None
        self.refresh()

    def refresh(self) -> None:
        anchor = self.source.now()
        anchor_monotonic = time.monotonic()
        rate = self.source.rate()
        with self._lock:
            self._anchor = anchor
            self._anchor_monotonic = anchor_monotonic
            self._rate = rate
            self.last_error = None

    def now(self) -> EarthDate:
        with self._lock:
            elapsed = time.monotonic() - self._anchor_monotonic
            value = self._anchor.as_decimal() + Decimal(str(self._rate * elapsed))
        return EarthDate.from_decimal(value)

    def rate(self) -> float:
        with self._lock:
            return self._rate

    def start(self) -> None:
        if self._thread is not None:
            return
        self._thread = threading.Thread(target=self._refresh_loop,
                                        name="nepp-astronomy", daemon=True)
        self._thread.start()

    def close(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=2)
            self._thread = None

    def _refresh_loop(self) -> None:
        while not self._stop.wait(self.refresh_interval):
            try:
                self.refresh()
            except Exception as error:  # retain the last good astronomical state
                self.last_error = error
                LOG.warning("astronomical clock refresh failed; continuing in holdover",
                            exc_info=True)
