import unittest

from xpcurve.core import Curve


class CostTest(unittest.TestCase):
    def test_low_level_cost(self):
        self.assertEqual(Curve().cost(1), 100)

    def test_mid_level_cost(self):
        self.assertEqual(Curve().cost(15), 200)

    def test_high_level_cost(self):
        self.assertEqual(Curve().cost(40), 500)


class LevelTest(unittest.TestCase):
    def test_zero_xp_is_level_one(self):
        self.assertEqual(Curve().level_for(0), 1)

    def test_first_level_up(self):
        self.assertEqual(Curve().level_for(100), 2)


if __name__ == "__main__":
    unittest.main()
