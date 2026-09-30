import unittest

from xpcurve.core import Curve


class CostTest(unittest.TestCase):
    def test_low_level_cost(self):
        self.assertEqual(Curve().cost(1), 100)

    def test_mid_level_cost(self):
        self.assertEqual(Curve().cost(15), 200)

    def test_high_level_cost(self):
        self.assertEqual(Curve().cost(40), 500)


class AwardTest(unittest.TestCase):
    def test_first_level_up(self):
        self.assertEqual(Curve().award("e1", "p", 100), 2)

    def test_zero_gain_stays_level_one(self):
        self.assertEqual(Curve().award("e1", "p", 0), 1)


class QueryTest(unittest.TestCase):
    def test_unknown_player_is_level_one(self):
        self.assertEqual(Curve().level_of("missing"), 1)

    def test_work_starts_at_zero(self):
        self.assertEqual(Curve().work_count(), 0)


if __name__ == "__main__":
    unittest.main()
