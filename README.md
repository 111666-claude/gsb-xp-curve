# xp-curve

经验曲线：分段升级代价、批量结算与经验余数，只用 Python 标准库。

```
python3 -m xpcurve.cli --sample segment
python3 -m xpcurve.cli --sample overflow
python3 -m xpcurve.cli --sample cost
python3 -m unittest discover -s tests -v
```

## 口径（README 为准）

- **分段代价**：升到下一级所需经验按等级分段取（低于 10 级每级 100，低于 30 级每级 200，
  其余每级 500），`level_for` 必须按分段算术换算，不许逐级扣经验。
- **余数**：总经验换算后剩下的经验要原样返回，不许丢弃。
- **下限**：总经验不允许为负，负数收益把经验压到 0 为止。
- **不变量**：同一份总经验重复换算等级相同；余数小于升到下一级所需经验；
  换算代价与总经验大小无关（`steps_count` 只涨段数量级）。
- **规模**：单服 200 万玩家的批量结算、每秒 10 万次换算，单次 O(段数)，内存 O(1)。

## 输出契约（不改格式）

```
level=13 steps<=3
level=13 rest=100
steps<=3000
```

## 目录

```
xpcurve/core.py   分段曲线与结算
xpcurve/cli.py    命令行入口
tests/            unittest 用例
```
