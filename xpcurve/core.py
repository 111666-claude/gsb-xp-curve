"""经验曲线：分段升级代价、批量结算与经验余数。

缺陷：所有等级都按第一段代价算（分段被忽略）、逐级扣经验（代价随等级线性增长）、
结算时经验余数被丢弃、查询每次重算全表。
"""

# 升到下一级所需经验的每一段：(等级上限, 每级经验)，最后一段上限为 None。
SEGMENTS = ((10, 100), (30, 200), (None, 500))


class Curve:
    """经验曲线。"""

    def __init__(self, segments=SEGMENTS):
        self.segments = segments
        self.steps = 0

    def cost(self, level):
        """升到 level+1 需要的经验。"""
        for limit, per in self.segments:
            if limit is None or level < limit:
                return per
        return self.segments[-1][1]

    def level_for(self, xp):
        """按总经验换算等级。

        缺陷：无视后面的分段，一律按 100 经验一级逐级扣（代价随经验线性增长）。
        """
        level = 1
        while xp >= 100:
            self.steps += 1
            xp -= 100
            level += 1
        return level

    def add(self, xp, gain, now_ms=0):
        """结算一次经验收益，返回 (等级, 余数)。

        缺陷：余数永远返回 0（被丢掉），负数收益也不做下限保护。
        """
        return self.level_for(xp + gain), 0

    def steps_count(self):
        return self.steps
