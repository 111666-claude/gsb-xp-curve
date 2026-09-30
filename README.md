# xp-curve

经验结算服务：分段升级代价、结算幂等、余数保留、满级转生、增量维护等级，只用 Python 标准库。

```
python3 -m xpcurve.cli --sample level
python3 -m xpcurve.cli --sample dup
python3 -m xpcurve.cli --sample cap
python3 -m unittest discover -s tests -v
```

## 口径（README 为准）

- **分段代价**：升到下一级所需经验按等级分段取（10 级前 100、30 级前 200、之后 500），
  等级上限 `MAX_LEVEL = 60`；结算要按分段一次算完，`work_count()` 只涨段数量级。
- **结算幂等**：同一个 `event_id` 只结算一次，重复发放不改变任何状态。
- **余数保留**：结算后剩下的经验要原样返回（`remainder_of`）。
- **满级转生**：到上限后多余经验按 `PRESTIGE_UNIT = 1000` 换转生点，不足一份的留在余数里。
- **守恒**：累计获得经验 = 升级消耗 + 余数 + 转生消耗（三部分加总必须等于发放总量）。
- **规模**：200 万玩家、每秒 10 万次发放，单次摊还 O(1)，内存 O(玩家数)。

## 输出契约（不改格式）

```
level=13 rest=100 work<=3
level=6
level=60 prestige=2 rest=500
work<=3
```

## 常量

```
SEGMENTS      = ((10, 100), (30, 200), (None, 500))
MAX_LEVEL     = 60
PRESTIGE_UNIT = 1000
```

## 目录

```
xpcurve/core.py   结算、余数与转生
xpcurve/cli.py    命令行入口
tests/            unittest 用例
```
