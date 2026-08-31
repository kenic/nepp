"""Legacy V1 client arithmetic remains usable with old V1 servers."""
import unittest
from nepp.client import calculate
from nepp.packet import Mode, Packet, Status
from nepp.timestamp import EarthDate


class ProtocolTests(unittest.TestCase):
    def test_offset_and_delay(self):
        e1 = EarthDate.from_decimal('2026.100')
        response = Packet(status=Status.SYNCHRONIZED, mode=Mode.SERVER, stratum=1,
                          origin=e1, receive=EarthDate.from_decimal('2026.104'),
                          transmit=EarthDate.from_decimal('2026.105'))
        result = calculate(response, e1, EarthDate.from_decimal('2026.103'))
        self.assertAlmostEqual(float(result.offset), 0.003)
        self.assertAlmostEqual(float(result.round_trip), 0.002)

    def test_origin_mismatch_is_rejected(self):
        response = Packet(status=Status.SYNCHRONIZED, mode=Mode.SERVER, stratum=1,
                          origin=EarthDate(2026, 2))
        with self.assertRaisesRegex(ValueError, 'origin'):
            calculate(response, EarthDate(2026, 1), EarthDate(2026, 3))
