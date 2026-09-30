"""经验结算服务：分段升级代价、结算幂等、余数保留、满级转生、增量维护等级。

每个玩家只维护 [等级, 余数, 转生点] 三个标量；一次发放按分段整块扣经验，
单次结算最多遍历 SEGMENTS（段数量级），与发放经验量无关，摊还 O(1)。
"""

# 升到下一级所需经验的每一段：(等级上限, 每级经验)，最后一段上限为 None。
SEGMENTS = ((10, 100), (30, 200), (None, 500))

# MAX_LEVEL 是等级上限，PrestigeUnit 是满级后多少点经验换 1 点转生点。
MAX_LEVEL = 60
PRESTIGE_UNIT = 1000


class Curve:
    """每个玩家一条结算记录：[等级, 余数, 转生点]。"""

    def __init__(self, segments=SEGMENTS, max_level=MAX_LEVEL, prestige_unit=PRESTIGE_UNIT):
        self.segments = segments
        self.max_level = max_level
        self.prestige_unit = prestige_unit
        self.state = {}
        self.handled = set()
        self.work = 0

    def cost(self, level):
        """升到 level+1 需要的经验。"""
        for limit, per in self.segments:
            if limit is None or level < limit:
                return per
        return self.segments[-1][1]

    def award(self, event_id, player, gain):
        """结算一次经验收益，返回结算后的等级。

        同一 event_id 只结算一次；按分段整块升级；满级后多余经验转转生点，
        不足一个 PRESTIGE_UNIT 的留在余数里。
        """
        if event_id in self.handled:
            return self._level_of(player)
        self.handled.add(event_id)

        rec = self.state.get(player)
        if rec is None:
            rec = [1, 0, 0]
            self.state[player] = rec
        level, rest, prestige = rec
        rest += gain

        for limit, per in self.segments:
            self.work += 1
            if level >= self.max_level:
                break
            levels_left = self.max_level - level if limit is None else limit - level
            if levels_left <= 0:
                continue
            need = levels_left * per
            if rest >= need:
                rest -= need
                level += levels_left
            else:
                level += rest // per
                rest %= per
                break

        if level >= self.max_level:
            prestige += rest // self.prestige_unit
            rest %= self.prestige_unit

        rec[0], rec[1], rec[2] = level, rest, prestige
        return level

    def level_of(self, player):
        """等级，直接读增量维护的状态。"""
        return self._level_of(player)

    def _level_of(self, player):
        rec = self.state.get(player)
        return rec[0] if rec is not None else 1

    def remainder_of(self, player):
        """当前等级内的余数（满级后是不足一次转生的零头）。"""
        rec = self.state.get(player)
        return rec[1] if rec is not None else 0

    def prestige_of(self, player):
        """转生点。"""
        rec = self.state.get(player)
        return rec[2] if rec is not None else 0

    def total_gained_of(self, player):
        """累计发放给该玩家的有效经验总量（重复 event_id 不计）。"""
        return self.spent_to(self.level_of(player)) + self.remainder_of(player) \
            + self.prestige_of(player) * self.prestige_unit

    def spent_to(self, level):
        """从 1 级升到 level 级消耗的总经验。"""
        spent = 0
        prev = 1
        for limit, per in self.segments:
            upper = self.max_level if limit is None else min(limit, self.max_level)
            if level > prev:
                spent += (min(level, upper) - prev) * per
            prev = upper
            if level <= upper:
                break
        return spent

    def work_count(self):
        return self.work
