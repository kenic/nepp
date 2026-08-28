from decimal import Decimal
import socket
import threading
import time
import unittest

from nepp.client import calculate, query
from nepp.packet import Mode, Packet, Status
from nepp.server import make_response, serve
from nepp.timestamp import EarthDate


class SequenceClock:
    def __init__(self, values, rate=3.2e-8):
        self.values = iter(values)
        self._rate = rate

    def now(self):
        return next(self.values)

    def rate(self):
        return self._rate


class ProtocolTests(unittest.TestCase):
    def test_server_copies_transmit_to_origin(self):
        sent = EarthDate.from_decimal("2026.1")
        response = make_response(Packet(mode=Mode.CLIENT, transmit=sent),
                                 SequenceClock([EarthDate.from_decimal("2026.2"),
                                                EarthDate.from_decimal("2026.3")]))
        self.assertEqual(response.origin, sent)
        self.assertEqual(response.mode, Mode.SERVER)

    def test_offset_and_delay(self):
        e1 = EarthDate.from_decimal("2026.100")
        response = Packet(status=Status.SYNCHRONIZED, mode=Mode.SERVER, stratum=1,
                          origin=e1, receive=EarthDate.from_decimal("2026.104"),
                          transmit=EarthDate.from_decimal("2026.105"))
        result = calculate(response, e1, EarthDate.from_decimal("2026.103"))
        self.assertAlmostEqual(float(result.offset), 0.003)
        self.assertAlmostEqual(float(result.round_trip), 0.002)

    def test_origin_mismatch_is_rejected(self):
        response = Packet(status=Status.SYNCHRONIZED, mode=Mode.SERVER, stratum=1,
                          origin=EarthDate(2026, 2))
        with self.assertRaisesRegex(ValueError, "origin"):
            calculate(response, EarthDate(2026, 1), EarthDate(2026, 3))

    def test_udp_loopback_exchange(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
            probe.bind(("127.0.0.1", 0))
            port = probe.getsockname()[1]
        stop = threading.Event()
        server_clock = SequenceClock([EarthDate.from_decimal("2026.200001"),
                                      EarthDate.from_decimal("2026.200002")])
        thread = threading.Thread(target=serve,
                                  args=("127.0.0.1", port, server_clock, stop.is_set))
        thread.start()
        try:
            time.sleep(0.02)
            client_clock = SequenceClock([EarthDate.from_decimal("2026.200000"),
                                          EarthDate.from_decimal("2026.200003")])
            result = query("127.0.0.1", port, client_clock)
            self.assertEqual(result.response.origin, EarthDate.from_decimal("2026.200000"))
            self.assertAlmostEqual(float(result.offset), 0.0)
        finally:
            stop.set()
            thread.join(1)
