"""经验结算服务：分段升级代价、结算幂等、余数保留、满级转生、增量维护等级。

缺陷：逐级扣经验（代价随经验量线性增长）、同一 event_id 重复结算、余数被丢弃、
满级之后的多余经验直接消失、等级每次重算。
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

        缺陷：不去重（同一 event_id 重复结算）、逐级扣经验（忽略分段）、
        余数丢弃、满级之后的多余经验不转成转生点。
        """
        self.state[player] = self.state.get(player, 0) + gain
        return self._level_of_total(self.state[player])

    def level_of(self, player):
        """等级。缺陷：每次重算（同样是逐级循环）。"""
        return self._level_of_total(self.state.get(player, 0))

    def _level_of_total(self, total):
        level = 1
        while total >= 100:
            self.work += 1
            total -= 100
            level += 1
        return level

    def remainder_of(self, player):
        """当前等级内的余数。缺陷：没有余数概念。"""
        return 0

    def prestige_of(self, player):
        """转生点。缺陷：满级经验直接丢。"""
        return 0

    def work_count(self):
        return self.work
