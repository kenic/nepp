from decimal import Decimal
import unittest

from nepp.timestamp import EarthDate, FRACTION_SCALE


class EarthDateTests(unittest.TestCase):
    def test_wire_round_trip(self):
        value = EarthDate(2026, 1 << 63)
        self.assertEqual(EarthDate.unpack(value.pack()), value)
        self.assertEqual(len(value.pack()), 12)

    def test_decimal_encoding_floors_fraction(self):
        self.assertEqual(EarthDate.from_decimal("2026.25"),
                         EarthDate(2026, FRACTION_SCALE // 4))

    def test_negative_value_uses_floor_year(self):
        self.assertEqual(EarthDate.from_decimal("-0.25"),
                         EarthDate(-1, 3 * FRACTION_SCALE // 4))

    def test_difference_crosses_year_boundary(self):
        before = EarthDate(2026, FRACTION_SCALE - 10)
        after = EarthDate(2027, 5)
        self.assertEqual(after.difference(before), Decimal(15) / FRACTION_SCALE)
