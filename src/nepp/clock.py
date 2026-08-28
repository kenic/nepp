"""Earth Date clock interface and experimental Astropy realization."""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol

from .timestamp import EarthDate


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
