"""命令行入口：跑经验结算样例。"""

import argparse

from .core import MAX_LEVEL, PRESTIGE_UNIT, Curve


def build_parser():
    parser = argparse.ArgumentParser(prog="xp-curve", description="经验结算")
    parser.add_argument("--sample", default="level", help="level / dup / cap / work")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.sample == "level":
        curve = Curve()
        level = curve.award("e1", "p", 1600)
        print("level=%d rest=%d work=%d" % (level, curve.remainder_of("p"), curve.work_count()))
    elif args.sample == "dup":
        curve = Curve()
        curve.award("e1", "p", 500)
        level = curve.award("e1", "p", 500)
        print("level=%d" % level)
    elif args.sample == "cap":
        curve = Curve()
        to_cap = 900 + 20 * 200 + 30 * 500
        level = curve.award("e1", "p", to_cap + 2500)
        print("level=%d prestige=%d rest=%d" % (level, curve.prestige_of("p"), curve.remainder_of("p")))
    elif args.sample == "work":
        curve = Curve()
        curve.award("e1", "p", 1000000)
        print("work=%d" % curve.work_count())
    else:
        raise SystemExit("需要 --sample level|dup|cap|work")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
