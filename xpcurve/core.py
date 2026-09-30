"""经验结算服务：分段升级代价、结算幂等、余数保留、满级转生、增量维护等级。"""

# 升到下一级所需经验的每一段：(等级上限, 每级经验)，最后一段上限为 None。
SEGMENTS = ((10, 100), (30, 200), (None, 500))

# MAX_LEVEL 是等级上限，PrestigeUnit 是满级后多少点经验换 1 点转生点。
MAX_LEVEL = 60
PRESTIGE_UNIT = 1000


class Curve:
    """每个玩家一条结算记录：[等级, 余数, 转生点, 累计获得经验]。"""

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

        同一 event_id 只结算一次；升级按分段整段算完（每经过一段 work 只 +1）；
        升不满一级的经验留在余数里；满级后余数按 PRESTIGE_UNIT 转成转生点。
        """
        if event_id in self.handled:
            return self.level_of(player)
        self.handled.add(event_id)

        level, remainder, prestige, total = self.state.get(player, [1, 0, 0, 0])
        total += gain
        remainder += gain

        seg_index = self._segment_index(level)
        while level < self.max_level and seg_index < len(self.segments):
            self.work += 1
            limit, per = self.segments[seg_index]
            available = (self.max_level - level) if limit is None else (limit - level)
            steps = min(available, remainder // per)
            if steps == 0:
                break
            level += steps
            remainder -= steps * per
            seg_index += 1

        if level >= self.max_level:
            level = self.max_level
            prestige += remainder // self.prestige_unit
            remainder %= self.prestige_unit

        self.state[player] = [level, remainder, prestige, total]
        return level

    def _segment_index(self, level):
        for index, (limit, _per) in enumerate(self.segments):
            if limit is None or level < limit:
                return index
        return len(self.segments) - 1

    def level_of(self, player):
        """等级（增量维护，O(1)）。"""
        return self.state.get(player, [1, 0, 0, 0])[0]

    def remainder_of(self, player):
        """当前等级内的余数（满级后是不足一份转生的余数）。"""
        return self.state.get(player, [1, 0, 0, 0])[1]

    def prestige_of(self, player):
        """转生点。"""
        return self.state.get(player, [1, 0, 0, 0])[2]

    def total_of(self, player):
        """该玩家累计获得的经验（去重后的发放总量）。"""
        return self.state.get(player, [1, 0, 0, 0])[3]

    def spent_of(self, player):
        """升级已消耗的经验。"""
        return self._spent_to(self.level_of(player))

    def _spent_to(self, level):
        """从 1 级升到 level 级的总消耗。"""
        spent = 0
        prev = 1
        for limit, per in self.segments:
            top = self.max_level if limit is None else min(level, limit)
            if top > prev:
                spent += (top - prev) * per
            prev = top
            if limit is not None and level <= limit:
                break
        return spent

    def work_count(self):
        return self.work
