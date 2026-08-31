"""Model sanity/regression checks, not independent accuracy certification."""
import importlib.util
import math
import unittest
from unittest.mock import patch
from nepp.astronomy import BasicAstronomicalSource


@unittest.skipUnless(importlib.util.find_spec('astropy'), 'astronomy extra not installed')
class AstronomyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from astropy.utils import iers
        from astropy.time import Time
        cls.Time = Time
        cls.table = iers.IERS_B.open(iers.IERS_B_FILE)

    def source(self, date='2020-06-21T12:00:00'):
        return BasicAstronomicalSource(iers_table=self.table,
            wall_clock=lambda: self.Time(date, scale='utc').unix,
            monotonic=lambda: 100)

    def test_historical_eop_and_solar_noon(self):
        s = self.source().acquire()
        s.validate()
        self.assertAlmostEqual(float(s.ed.as_decimal()), 2020.25, delta=.002)
        self.assertAlmostEqual(s.phase, .5, delta=.005)
        self.assertTrue(2.9e-8 < s.rate < 3.5e-8)
        self.assertTrue(1.15e-5 < s.phase_rate < 1.17e-5)
        self.assertFalse(s.ed_quality.evaluated)
        self.assertFalse(s.sp_quality.evaluated)
        self.assertEqual(s.epoch, 100)

    def test_missing_eop_keeps_ed(self):
        source = self.source()
        with patch.object(source, '_solar', side_effect=ValueError('missing EOP')):
            s = source.acquire()
        s.validate()
        self.assertIsNone(s.phase)
        self.assertGreater(s.rate, 0)

    def test_out_of_range_eop_keeps_ed(self):
        s = self.source('2090-01-01T12:00:00').acquire()
        s.validate()
        self.assertIsNone(s.phase)

    def test_direction_light_time_and_unit_norm(self):
        source = self.source()
        s, light = source.direction(self.Time('2020-01-01', scale='tt'))
        self.assertAlmostEqual(sum(s*s), 1, places=14)
        self.assertTrue(480 < light < 515)

    def test_year_wrap_and_leap_second(self):
        source = self.source('2020-03-20T03:50:00')
        s = source.acquire()
        self.assertTrue(2019.999 < float(s.ed.as_decimal()) < 2020.001)
        self.assertGreater(s.rate, 0)
        ed, _ = source.coordinates(self.Time('2016-12-31T23:59:60', scale='utc'))
        self.assertTrue(2016 < ed < 2017)

    def test_outside_ephemeris_range(self):
        with self.assertRaises(ValueError):
            self.source().coordinates(self.Time('1800-01-01', scale='tt'))
