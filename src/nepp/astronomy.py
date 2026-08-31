"""Draft-03 basic model: retarded solar center + pure Lorentz aberration.

Uses ERFA epv00 as a provisional ephemeris, not an accuracy-certified source.
All expensive work and optional IERS retrieval take place in acquire(), never
in the UDP request path. EOP failure does not prevent ED calculation.
"""

from decimal import Decimal
import logging
import math
import time

from .source import SourceSample
from .timestamp import EarthDate
from .v2 import Quality

LOG = logging.getLogger("nepp.astronomy")
REFERENCE_ID = int.from_bytes(b"BASC", "big")


class BasicAstronomicalSource:
    def __init__(self, *, derivative_interval=30.0, validity=300, iers_table=None,
                 monotonic=None, wall_clock=None):
        if not math.isfinite(derivative_interval) or not 0 < derivative_interval <= 60:
            raise ValueError("derivative interval must be in (0,60] seconds")
        if not 1 <= validity <= 3600:
            raise ValueError("intended validity must be in [1,3600] seconds")
        try:
            import erfa
            import numpy as np
            from astropy.time import Time, TimeDelta
        except ImportError as error:
            raise RuntimeError("install NEPP with the 'astronomy' extra") from error
        self.erfa, self.np = erfa, np
        self.Time, self.TimeDelta = Time, TimeDelta
        self.width, self.validity = derivative_interval, validity
        self.iers_table = iers_table
        self.monotonic = monotonic or time.monotonic
        self.wall_clock = wall_clock or time.time
        self.last_solar_error = None

    def direction(self, instant):
        """Return basic-model direction in GCRS-aligned axes and light time (s)."""
        erfa, np = self.erfa, self.np
        t = instant.tdb
        # epv00 is approximate; restrict this realization, not the protocol.
        if not 1900 <= instant.tt.jyear <= 2100:
            raise ValueError("experimental ephemeris supports 1900-2100 only")
        helio, bary = erfa.epv00(t.jd1, t.jd2)
        earth = bary['p']
        c = 299792458.0 * 86400.0 / 149597870700.0  # AU per TDB day
        delay = 0.0
        for _ in range(12):
            sh, sb = erfa.epv00(t.jd1, t.jd2 - delay)
            ray = (sb['p'] - sh['p']) - earth
            new_delay = float(np.linalg.norm(ray) / c)
            if abs(new_delay - delay) < 1e-13:
                break
            delay = new_delay
        else:
            raise ValueError("solar light-time iteration did not converge")
        p = ray / np.linalg.norm(ray)
        b = bary['v'] / c
        g = np.sqrt(1 - np.dot(b, b))
        w = np.dot(p, b)
        s = g * p + (1 + w / (1 + g)) * b
        s /= np.linalg.norm(s)
        return s, new_delay * 86400.0

    def coordinates(self, instant):
        """ED as Decimal and true-equatorial solar right ascension, radians."""
        erfa = self.erfa
        s, _ = self.direction(instant)
        tt = instant.tt
        x, y, z = erfa.pnm06a(tt.jd1, tt.jd2) @ s
        _, deps = erfa.nut06a(tt.jd1, tt.jd2)
        eps = erfa.obl06(tt.jd1, tt.jd2) + deps
        longitude = math.atan2(math.cos(eps) * y + math.sin(eps) * z, x) % math.tau
        ra = math.atan2(y, x) % math.tau
        civil = instant.utc.ymdhms
        before = civil.month < 3 or (civil.month == 3 and longitude > math.pi)
        year = int(civil.year) - int(before)
        ed = Decimal(year) + Decimal(str(longitude / math.tau))
        return ed, ra

    def _solar(self, instants, ras):
        from astropy.utils import iers
        np, erfa = self.np, self.erfa
        table = self.iers_table if self.iers_table is not None else iers.IERS_Auto.open()
        # Include both derivative endpoints and the intended usage horizon.
        times = self.Time([*instants, instants[1] + self.TimeDelta(self.validity, format='sec')])
        offsets, status = table.ut1_utc(times, return_status=True)
        if np.any(np.asarray(status) < 0) or not np.all(np.isfinite(offsets.value)):
            raise ValueError("UT1 outside EOP coverage")
        # Astropy reports the upper interpolation row's source. Inspect BOTH
        # brackets and all intervening rows, including observed/predicted boundaries.
        grid = table['MJD'].value
        indices = np.searchsorted(grid, np.floor(times.utc.mjd), side='right')
        if np.any(indices <= 0) or np.any(indices >= len(table)):
            raise ValueError("EOP interpolation bracket unavailable")
        rows = np.arange(int(indices.min()) - 1, int(indices.max()) + 1)
        kinds = np.asarray(table.ut1_utc_source(rows))
        predicted = bool(np.any(kinds == iers.FROM_IERS_A_PREDICTION))
        phases = []
        for instant, ra, offset in zip(instants, ras, offsets):
            # Explicit delta avoids an implicit second IERS lookup or UT1=UTC.
            t = instant.copy()
            t.delta_ut1_utc = float(offset.to_value('s'))
            u, tt = t.ut1, t.tt
            gast = erfa.gst06a(u.jd1, u.jd2, tt.jd1, tt.jd2)
            phases.append((0.5 + (gast - ra) / math.tau) % 1)
        rate = ((phases[2] - phases[0] + 0.5) % 1 - 0.5) / (2 * self.width)
        # Unknown ephemeris prediction provenance prevents a 'no prediction'
        # claim, but known EOP prediction use can truthfully be reported.
        return phases[1], rate, 2 if predicted else 0

    def acquire(self):
        # Anchor BEFORE slow computation. Completion time is not coordinate time.
        m0 = self.monotonic()
        wall = self.wall_clock()
        m1 = self.monotonic()
        anchor = (m0 + m1) / 2
        instant = self.Time(wall, format='unix', scale='utc').tt
        width = self.TimeDelta(self.width, format='sec', scale='tt')
        instants = [instant - width, instant, instant + width]
        coords = [self.coordinates(t) for t in instants]
        rate = float((coords[2][0] - coords[0][0]) / Decimal(str(2 * self.width)))
        edq = Quality.unassessed(reference_id=REFERENCE_ID, validity=self.validity)
        phase, q, spq = None, 0.0, Quality()
        try:
            phase, q, prediction = self._solar(instants, [x[1] for x in coords])
            spq = Quality.unassessed(reference_id=REFERENCE_ID, validity=self.validity,
                                     prediction=prediction)
            self.last_solar_error = None
        except Exception as error:
            if self.last_solar_error is None:
                LOG.warning("SP unavailable; retaining unassessed ED: %s", error)
            self.last_solar_error = error
            phase, q, spq = None, 0.0, Quality()
        return SourceSample(anchor, EarthDate.from_decimal(coords[1][0]), rate, edq,
                            phase, q, spq, wall)
