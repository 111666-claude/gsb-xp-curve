"""经验曲线。"""
import random
import unittest

from xpcurve.core import MAX_LEVEL, PRESTIGE_UNIT, SEGMENTS, Curve


def reference_state(awards):
    """参考实现：分段算术 + 幂等 + 转生，逐级模拟，返回 (level, rest, prestige)。"""
    level, rest, prestige = 1, 0, 0
    seen = set()
    for event_id, gain in awards:
        if event_id in seen:
            continue
        seen.add(event_id)
        rest += gain
        while level < MAX_LEVEL:
            per = next(p for lim, p in SEGMENTS if lim is None or level < lim)
            if rest < per:
                break
            rest -= per
            level += 1
        if level >= MAX_LEVEL:
            prestige += rest // PRESTIGE_UNIT
            rest %= PRESTIGE_UNIT
    return level, rest, prestige


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

    def test_segmented_bulk_level_up(self):
        curve = Curve()
        self.assertEqual(curve.award("e1", "p", 1600), 13)
        self.assertEqual(curve.remainder_of("p"), 100)
        self.assertLessEqual(curve.work_count(), 3)

    def test_work_scales_with_segments_not_gain(self):
        curve = Curve()
        curve.award("e1", "p", 1000000)
        self.assertLessEqual(curve.work_count(), 3)


class IdempotencyTest(unittest.TestCase):
    def test_duplicate_event_id_settles_once(self):
        curve = Curve()
        curve.award("e1", "p", 500)
        self.assertEqual(curve.award("e1", "p", 500), 6)
        self.assertEqual(curve.level_of("p"), 6)
        self.assertEqual(curve.remainder_of("p"), 0)

    def test_duplicate_event_id_keeps_prestige(self):
        curve = Curve()
        curve.award("e1", "p", 19900 + 2500)
        curve.award("e1", "p", 19900 + 2500)
        self.assertEqual(curve.prestige_of("p"), 2)
        self.assertEqual(curve.remainder_of("p"), 500)


class RemainderTest(unittest.TestCase):
    def test_remainder_preserved(self):
        curve = Curve()
        curve.award("e1", "p", 250)
        self.assertEqual(curve.level_of("p"), 3)
        self.assertEqual(curve.remainder_of("p"), 50)

    def test_remainder_accumulates_across_awards(self):
        curve = Curve()
        curve.award("e1", "p", 60)
        curve.award("e2", "p", 60)
        self.assertEqual(curve.level_of("p"), 2)
        self.assertEqual(curve.remainder_of("p"), 20)


class PrestigeTest(unittest.TestCase):
    def test_overflow_converts_to_prestige(self):
        curve = Curve()
        to_cap = 900 + 20 * 200 + 30 * 500
        self.assertEqual(curve.award("e1", "p", to_cap + 2500), MAX_LEVEL)
        self.assertEqual(curve.prestige_of("p"), 2)
        self.assertEqual(curve.remainder_of("p"), 500)

    def test_sub_unit_overflow_stays_in_remainder(self):
        curve = Curve()
        to_cap = 900 + 20 * 200 + 30 * 500
        curve.award("e1", "p", to_cap + 999)
        self.assertEqual(curve.prestige_of("p"), 0)
        self.assertEqual(curve.remainder_of("p"), 999)


class ConservationTest(unittest.TestCase):
    def test_gain_equals_spent_plus_rest_plus_prestige(self):
        rng = random.Random(20261001)
        curve = Curve()
        total = 0
        for i in range(500):
            gain = rng.choice((0, 1, 37, 100, 999, 5000, 10 ** 6))
            total += gain
            curve.award("e%d" % i, "p", gain)
        spent = curve.spent_to(curve.level_of("p"))
        self.assertEqual(
            total,
            spent + curve.remainder_of("p") + curve.prestige_of("p") * PRESTIGE_UNIT,
        )


class CrossCheckTest(unittest.TestCase):
    def test_matches_reference_on_random_sequences(self):
        rng = random.Random(7)
        for case in range(200):
            curve = Curve()
            awards = []
            for _ in range(rng.randint(1, 40)):
                event_id = "e%d" % rng.randint(0, 15)  # 大量重复 event_id
                gain = rng.choice((0, 1, 50, 100, 777, 10 ** 4, 10 ** 6, 10 ** 7))
                awards.append((event_id, gain))
                curve.award(event_id, "p", gain)
            level, rest, prestige = reference_state(awards)
            self.assertEqual(curve.level_of("p"), level, "case %d" % case)
            self.assertEqual(curve.remainder_of("p"), rest, "case %d" % case)
            self.assertEqual(curve.prestige_of("p"), prestige, "case %d" % case)
            self.assertLessEqual(curve.work_count(), 3 * len(set(e for e, _ in awards)))


class QueryTest(unittest.TestCase):
    def test_unknown_player_is_level_one(self):
        self.assertEqual(Curve().level_of("missing"), 1)

    def test_work_starts_at_zero(self):
        self.assertEqual(Curve().work_count(), 0)


if __name__ == "__main__":
    unittest.main()
