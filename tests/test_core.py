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


SEGMENTS = ((10, 100), (30, 200), (None, 500))
MAX_LEVEL = 60
PRESTIGE_UNIT = 1000


def ref_cost(level):
    for limit, per in SEGMENTS:
        if limit is None or level < limit:
            return per
    return SEGMENTS[-1][1]


def ref_spent_to(level):
    """独立参考实现：升到 level 级的分段累计消耗。"""
    spent = 0
    prev = 1
    for limit, per in SEGMENTS:
        top = MAX_LEVEL if limit is None else min(level, limit)
        spent += max(0, top - prev) * per
        prev = top
        if limit is not None and level <= limit:
            break
    return spent


class ReferenceCurve:
    """独立参考实现：幂等 + 分段算术 + 满级转生，状态直接增量维护。"""

    def __init__(self):
        self.players = {}
        self.handled = set()
        self.work = 0

    def award(self, event_id, player, gain):
        if event_id in self.handled:
            return
        self.handled.add(event_id)
        level, remainder, prestige, total = self.players.get(player, (1, 0, 0, 0))
        total += gain
        remainder += gain
        seg_index = 0
        for seg_limit, seg_per in SEGMENTS:
            if seg_limit is None or level < seg_limit:
                break
            seg_index += 1
        while level < MAX_LEVEL and seg_index < len(SEGMENTS):
            self.work += 1
            limit, per = SEGMENTS[seg_index]
            available = MAX_LEVEL - level if limit is None else limit - level
            steps = min(available, remainder // per)
            if steps == 0:
                break
            level += steps
            remainder -= steps * per
            seg_index += 1
        if level >= MAX_LEVEL:
            prestige += remainder // PRESTIGE_UNIT
            remainder %= PRESTIGE_UNIT
        self.players[player] = (level, remainder, prestige, total)


class SegmentCostTest(unittest.TestCase):
    def test_segment_boundary_costs(self):
        curve = Curve()
        self.assertEqual(curve.cost(1), 100)
        self.assertEqual(curve.cost(9), 100)
        self.assertEqual(curve.cost(10), 200)
        self.assertEqual(curve.cost(29), 200)
        self.assertEqual(curve.cost(30), 500)
        self.assertEqual(curve.cost(60), 500)

    def test_award_consumes_segments_in_one_pass(self):
        curve = Curve()
        self.assertEqual(curve.award("e1", "p", 1600), 13)
        self.assertEqual(curve.remainder_of("p"), 100)
        self.assertLessEqual(curve.work_count(), 3)

    def test_segment_arithmetic_full_cost_to_cap(self):
        curve = Curve()
        to_cap = 9 * 100 + 20 * 200 + 30 * 500
        self.assertEqual(curve.award("e1", "p", to_cap), 60)
        self.assertEqual(curve.remainder_of("p"), 0)
        self.assertEqual(curve.prestige_of("p"), 0)


class IdempotencyTest(unittest.TestCase):
    def test_duplicate_event_settled_once(self):
        curve = Curve()
        curve.award("e1", "p", 500)
        level = curve.award("e1", "p", 500)
        self.assertEqual(level, 6)
        self.assertEqual(curve.level_of("p"), 6)
        self.assertEqual(curve.remainder_of("p"), 0)
        self.assertEqual(curve.total_of("p"), 500)

    def test_duplicate_event_changes_nothing(self):
        curve = Curve()
        curve.award("e1", "p", 1600)
        snapshot = (
            curve.level_of("p"),
            curve.remainder_of("p"),
            curve.prestige_of("p"),
            curve.total_of("p"),
            curve.work_count(),
        )
        curve.award("e1", "p", 99999)
        self.assertEqual(snapshot, (
            curve.level_of("p"),
            curve.remainder_of("p"),
            curve.prestige_of("p"),
            curve.total_of("p"),
            curve.work_count(),
        ))

    def test_event_id_is_global_across_players(self):
        curve = Curve()
        self.assertEqual(curve.award("e1", "a", 100), 2)
        self.assertEqual(curve.award("e1", "b", 100), 1)


class RemainderTest(unittest.TestCase):
    def test_remainder_preserved(self):
        curve = Curve()
        curve.award("e1", "p", 250)
        self.assertEqual(curve.level_of("p"), 3)
        self.assertEqual(curve.remainder_of("p"), 50)

    def test_remainder_carries_across_awards(self):
        curve = Curve()
        curve.award("e1", "p", 150)
        curve.award("e2", "p", 150)
        self.assertEqual(curve.level_of("p"), 4)
        self.assertEqual(curve.remainder_of("p"), 0)

    def test_remainder_unknown_player(self):
        self.assertEqual(Curve().remainder_of("missing"), 0)


class PrestigeTest(unittest.TestCase):
    def test_prestige_at_cap(self):
        curve = Curve()
        to_cap = 9 * 100 + 20 * 200 + 30 * 500
        curve.award("e1", "p", to_cap + 2500)
        self.assertEqual(curve.level_of("p"), 60)
        self.assertEqual(curve.prestige_of("p"), 2)
        self.assertEqual(curve.remainder_of("p"), 500)

    def test_experience_after_cap_becomes_prestige(self):
        curve = Curve()
        to_cap = 9 * 100 + 20 * 200 + 30 * 500
        curve.award("e1", "p", to_cap)
        curve.award("e2", "p", 1200)
        self.assertEqual(curve.level_of("p"), 60)
        self.assertEqual(curve.prestige_of("p"), 1)
        self.assertEqual(curve.remainder_of("p"), 200)
        curve.award("e3", "p", 800)
        self.assertEqual(curve.prestige_of("p"), 2)
        self.assertEqual(curve.remainder_of("p"), 0)

    def test_sub_prestige_remainder_stays(self):
        curve = Curve()
        to_cap = 9 * 100 + 20 * 200 + 30 * 500
        curve.award("e1", "p", to_cap + 999)
        self.assertEqual(curve.prestige_of("p"), 0)
        self.assertEqual(curve.remainder_of("p"), 999)


class ConservationTest(unittest.TestCase):
    def test_conservation_randomized(self):
        import random
        rng = random.Random(20261001)
        curve = Curve()
        players = ["p%d" % i for i in range(20)]
        event_seq = 0
        for _ in range(500):
            event_seq += 1
            event_id = "e%d" % event_seq
            player = rng.choice(players)
            gain = rng.choice([0, 1, 99, 100, 1000, 10 ** rng.randint(3, 9)])
            curve.award(event_id, player, gain)
        for player in players:
            total = curve.total_of(player)
            spent = ref_spent_to(curve.level_of(player))
            self.assertEqual(
                total,
                spent + curve.remainder_of(player)
                + curve.prestige_of(player) * PRESTIGE_UNIT,
            )


class CrossCheckTest(unittest.TestCase):
    def test_200_random_sequences_match_reference(self):
        import random
        rng = random.Random(424242)
        for case in range(200):
            curve = Curve()
            ref = ReferenceCurve()
            players = ["p%d" % i for i in range(rng.randint(1, 8))]
            issued = []
            for _ in range(rng.randint(1, 60)):
                event_id = "e%d" % rng.randint(0, 39)
                player = rng.choice(players)
                gain = rng.choice([
                    0, 1, 50, 99, 100, 150, 200, 500, 1600, 19900,
                    rng.randint(0, 10 ** 6),
                    rng.randint(0, 10 ** 9),
                ])
                issued.append((event_id, player, gain))
                curve.award(event_id, player, gain)
                ref.award(event_id, player, gain)
            for event_id, player, gain in issued:
                curve.award(event_id, player, gain)
                ref.award(event_id, player, gain)
            for player in players:
                ref_level, ref_rest, ref_prestige, ref_total = ref.players.get(
                    player, (1, 0, 0, 0)
                )
                self.assertEqual(curve.level_of(player), ref_level, case)
                self.assertEqual(curve.remainder_of(player), ref_rest, case)
                self.assertEqual(curve.prestige_of(player), ref_prestige, case)
                self.assertEqual(curve.total_of(player), ref_total, case)
            self.assertEqual(curve.work_count(), ref.work, case)
            unique_events = len(curve.handled)
            self.assertLessEqual(curve.work_count(), 3 * unique_events)
