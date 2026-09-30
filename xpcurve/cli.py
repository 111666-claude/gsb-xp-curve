"""命令行入口：跑经验曲线样例。"""

import argparse

from .core import Curve


def build_parser():
    parser = argparse.ArgumentParser(prog="xp-curve", description="经验曲线")
    parser.add_argument("--sample", default="segment", help="segment / overflow / cost")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.sample == "segment":
        curve = Curve()
        print("level=%d steps=%d" % (curve.level_for(1500), curve.steps_count()))
    elif args.sample == "overflow":
        curve = Curve()
        level, rest = curve.add(1300, 300)
        print("level=%d rest=%d" % (level, rest))
    elif args.sample == "cost":
        curve = Curve()
        for _ in range(1000):
            curve.level_for(1000000)
        print("steps=%d" % curve.steps_count())
    else:
        raise SystemExit("需要 --sample segment|overflow|cost")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
