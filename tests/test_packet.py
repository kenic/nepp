import unittest

from nepp.packet import BASE_PACKET_SIZE, Mode, Packet, Status
from nepp.timestamp import EarthDate


class PacketTests(unittest.TestCase):
    def test_known_packet_round_trip_and_offsets(self):
        packet = Packet(status=Status.SYNCHRONIZED, mode=Mode.SERVER, stratum=1,
                        poll=6, precision=-52, reference_id=0x41535452,
                        reference=EarthDate(2026, 1), origin=EarthDate(2026, 2),
                        receive=EarthDate(2026, 3), transmit=EarthDate(2026, 4),
                        rate=123456, model_id=1)
        wire = packet.pack()
        self.assertEqual(len(wire), BASE_PACKET_SIZE)
        self.assertEqual(wire[0], 0b00001100)
        self.assertEqual(wire[3], 204)
        self.assertEqual(wire[16:28], packet.reference.pack())
        self.assertEqual(Packet.unpack(wire), packet)

    def test_extensions_are_preserved(self):
        packet = Packet(extensions=b"extension")
        self.assertEqual(Packet.unpack(packet.pack()).extensions, b"extension")

    def test_short_packet_is_rejected(self):
        with self.assertRaises(ValueError):
            Packet.unpack(bytes(BASE_PACKET_SIZE - 1))
