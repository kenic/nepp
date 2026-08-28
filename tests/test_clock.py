import unittest
from unittest.mock import patch

from nepp.clock import CachedEarthDateClock
from nepp.timestamp import EarthDate


class SourceClock:
    def __init__(self):
        self.now_calls = 0
        self.rate_calls = 0

    def now(self):
        self.now_calls += 1
        return EarthDate.from_decimal("2026.25")

    def rate(self):
        self.rate_calls += 1
        return 0.0001


class CachedClockTests(unittest.TestCase):
    @patch("nepp.clock.time.monotonic", side_effect=[100.0, 110.0])
    def test_interpolates_without_repeating_astronomy(self, _monotonic):
        source = SourceClock()
        clock = CachedEarthDateClock(source, refresh_interval=300)
        self.assertAlmostEqual(float(clock.now().as_decimal()), 2026.251, places=12)
        self.assertEqual(source.now_calls, 1)
        self.assertEqual(source.rate_calls, 1)

    def test_rejects_nonpositive_refresh(self):
        with self.assertRaises(ValueError):
            CachedEarthDateClock(SourceClock(), refresh_interval=0)
