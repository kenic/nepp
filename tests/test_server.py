import unittest

from nepp.server import RateLimiter


class FakeMonotonic:
    def __init__(self):
        self.value = 0.0

    def __call__(self):
        return self.value


class RateLimiterTests(unittest.TestCase):
    def test_limits_each_source_independently(self):
        now = FakeMonotonic()
        limiter = RateLimiter(rate=1, burst=2, clock=now)
        self.assertTrue(limiter.allow("192.0.2.1"))
        self.assertTrue(limiter.allow("192.0.2.1"))
        self.assertFalse(limiter.allow("192.0.2.1"))
        self.assertTrue(limiter.allow("192.0.2.2"))

    def test_tokens_replenish(self):
        now = FakeMonotonic()
        limiter = RateLimiter(rate=2, burst=1, clock=now)
        self.assertTrue(limiter.allow("192.0.2.1"))
        self.assertFalse(limiter.allow("192.0.2.1"))
        now.value = 0.5
        self.assertTrue(limiter.allow("192.0.2.1"))
