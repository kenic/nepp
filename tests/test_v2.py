from dataclasses import replace
from decimal import Decimal
import queue
import socket
import threading
import time
import unittest
from unittest.mock import patch
from nepp.packet import Packet, Status
from nepp.timestamp import EarthDate
from nepp.v2 import Quality, UNKNOWN, V2Packet, phase_to_wire, uncertainty_to_wire
from nepp.source import SourceSample, CachedSource, build_response
from nepp.server import serve, RateLimiter
from nepp.probe import query


def sample(epoch=100):
    quality = Quality.unassessed(reference_id=123, validity=300)
    return SourceSample(epoch, EarthDate.from_decimal('2026.4'), 3.2e-8,
                        quality, .99999, 1 / 86400, quality)


class CodecTests(unittest.TestCase):
    def test_request_layout(self):
        r = V2Packet.request(token=b'x' * 16)
        wire = r.pack()
        self.assertEqual(len(wire), 160)
        self.assertEqual(wire[:4], bytes([0xd3, 16, 6, 0]))
        self.assertEqual(wire[76:92], b'x' * 16)
        self.assertEqual(wire[92:], bytes(68))
        self.assertEqual(V2Packet.unpack(wire), r)

    def test_noncanonical_requests(self):
        r = V2Packet.request()
        for offset in [1, 3, 4, 12, 16, 28, 40, 64, 72, 92, 112, 136]:
            data = bytearray(r.pack()); data[offset] ^= 1
            with self.subTest(offset=offset), self.assertRaises(ValueError):
                V2Packet.unpack(data).validate_request()
        with self.assertRaises(ValueError): V2Packet.request(token=bytes(16))
        for length in [0, 76, 128, 159, 161, 200]:
            with self.subTest(length=length), self.assertRaises(ValueError):
                V2Packet.unpack(bytes(length))
        data = bytearray(r.pack()); data[0] = 0xcb
        with self.assertRaises(ValueError): V2Packet.unpack(data)

    def test_quality_sentinels(self):
        q = Quality.unassessed()
        q.validate()
        self.assertEqual(len(q.pack()), 24)
        for bad in [replace(q, state=4), replace(q, flags=8), replace(q, flags=6),
                    replace(q, uncertainty=0), replace(q, flags=1),
                    replace(q, validity=3601), replace(q, stratum=0), replace(q, state=0)]:
            with self.subTest(bad=bad), self.assertRaises(ValueError): bad.validate()
        replace(q, flags=1, uncertainty=0, validity=0).validate()
        with self.assertRaises(ValueError):
            replace(q, flags=1, uncertainty=0x80000000, validity=1).validate(solar=True)

    def test_rounding(self):
        self.assertEqual(phase_to_wire(Decimal(1) - Decimal(2) ** -64), 2**64 - 1)
        self.assertEqual(uncertainty_to_wire(Decimal(2) ** -33), 1)
        self.assertEqual(uncertainty_to_wire(1), UNKNOWN)
        self.assertEqual(uncertainty_to_wire(.5, solar=True), UNKNOWN)


class SourceTests(unittest.TestCase):
    def test_response_common_epoch(self):
        req = V2Packet.request(EarthDate.from_decimal('2026.1'))
        r = build_response(req, sample(), 101, 102)
        r.validate_for(req); self.assertTrue(r.validate_sp())
        self.assertEqual(len(r.pack()), 160)
        self.assertEqual(V2Packet.unpack(r.pack()), r)
        self.assertEqual(r.base.transmit, sample().ed_at(102))
        self.assertEqual(r.base.receive, sample().ed_at(101))
        self.assertLess(r.phase / 2**64, .001)
        self.assertEqual(r.ed_quality.validity, 298)
        self.assertEqual(r.ed_quality.update_age, 2)
        self.assertEqual(r.base.root_dispersion, UNKNOWN)
        with self.assertRaises(ValueError): r.validate_for(V2Packet.request())

    def test_holdover_expiry_and_absence(self):
        req = V2Packet.request()
        for now, failed in [(401, False), (102, True)]:
            r = build_response(req, sample(), now, now, failed=failed)
            self.assertEqual(r.base.status, Status.HOLDOVER)
            self.assertEqual(r.ed_quality.prediction, 2)
            self.assertEqual(r.ed_quality.uncertainty, UNKNOWN)
        for s, now in [(None, 101), (sample(), 3701)]:
            r = build_response(req, s, now, now)
            self.assertEqual(r.ed_quality, Quality())
            self.assertEqual(r.sp_quality, Quality())
            self.assertEqual(r.base.stratum, 16)
            with self.assertRaises(ValueError): r.validate_ed()

    def test_ed_without_sp(self):
        s = replace(sample(), phase=None, phase_rate=0, sp_quality=Quality())
        r = build_response(V2Packet.request(), s, 100, 101)
        r.validate_ed(); self.assertFalse(r.validate_sp())

    def test_invalid_sp_does_not_invalidate_ed(self):
        r = build_response(V2Packet.request(), sample(), 100, 101)
        r = replace(r, sp_quality=replace(r.sp_quality, flags=128))
        r = V2Packet.unpack(r.pack())
        r.validate_ed()
        with self.assertRaises(ValueError): r.validate_sp()

    def test_source_age_advances_without_reset(self):
        s = sample()
        s = replace(s, ed_quality=replace(s.ed_quality, data_age=100, update_age=20))
        r = build_response(V2Packet.request(), s, 100, 100.1)
        self.assertEqual(r.ed_quality.data_age, 101)
        self.assertEqual(r.ed_quality.update_age, 21)

    def test_initial_failure_is_unavailable(self):
        class Source:
            def acquire(self): raise ValueError('unavailable')
        c = CachedSource(Source())
        self.assertEqual(c.snapshot(), (None, True))

    def test_bound_not_renewed(self):
        s = sample()
        s = replace(s, ed_quality=replace(s.ed_quality, flags=1, uncertainty=1))
        self.assertTrue(build_response(V2Packet.request(), s, 101, 102).ed_quality.evaluated)
        self.assertFalse(build_response(V2Packet.request(), s, 99, 102).ed_quality.evaluated)
        self.assertFalse(build_response(V2Packet.request(), s, 401, 402).ed_quality.evaluated)

    def test_cache_failure_and_wall_step(self):
        class Source:
            def acquire(self): return replace(sample(), wall_epoch=1000)
        c = CachedSource(Source(), monotonic=lambda: 101, wall_clock=lambda: 1001)
        self.assertIsNotNone(c.snapshot()[0])
        with patch.object(c.source, 'acquire', side_effect=ValueError('failed')):
            self.assertFalse(c.refresh())
        self.assertTrue(c.snapshot()[1])
        c.wall_clock = lambda: 1005
        self.assertIsNone(c.snapshot()[0])


class UDPTests(unittest.TestCase):
    def test_real_udp_v2_and_silent_legacy_drop(self):
        class Source:
            def acquire(self): return sample(time.monotonic())
        cache = CachedSource(Source())
        stop, addresses = threading.Event(), queue.Queue()
        thread = threading.Thread(target=serve, args=('127.0.0.1', 0, cache, stop.is_set),
                                  kwargs={'on_bound': addresses.put})
        thread.start()
        try:
            address = addresses.get(timeout=3)
            r = query(*address)
            r.validate_ed(); self.assertTrue(r.validate_sp())
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.settimeout(.15)
                for data in [Packet().pack(), bytes(128), bytes(160)]:
                    sock.sendto(data, address)
                    with self.assertRaises(socket.timeout): sock.recv(1024)
        finally:
            stop.set(); thread.join(2)
        self.assertFalse(thread.is_alive())

    def test_bounded_limiter_and_mapped_address(self):
        limiter = RateLimiter(burst=1, max_clients=2, clock=lambda: 0)
        self.assertTrue(limiter.allow('192.0.2.1'))
        self.assertFalse(limiter.allow('::ffff:192.0.2.1'))
        limiter.allow('192.0.2.2'); limiter.allow('192.0.2.3')
        self.assertEqual(len(limiter._clients), 2)
        for _ in range(500): limiter.allow('192.0.2.4')
        self.assertFalse(limiter.allow('192.0.2.5'))
