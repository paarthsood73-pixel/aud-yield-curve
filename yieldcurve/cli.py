"""Command line entry point: python -m yieldcurve data/sample_aud_rates.csv"""
from __future__ import annotations

import argparse

from .bootstrap import bootstrap, load_instruments
from .instruments import Swap


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(description="Bootstrap an AUD zero curve from market quotes.")
    p.add_argument("csv", help="CSV of quotes (type,start,maturity,rate)")
    p.add_argument("--plot", metavar="PNG", help="Save a chart of zero and forward rates")
    args = p.parse_args(argv)

    insts = load_instruments(args.csv)
    curve = bootstrap(insts)

    print(f"{'Pillar (y)':>10} {'DF':>10} {'Zero %':>8} {'Reprice err (bp)':>17}")
    for inst in sorted(insts, key=lambda x: x.pillar):
        t = inst.pillar
        err = (inst.par_rate(curve) - inst.rate) * 1e4 if isinstance(inst, Swap) else 0.0
        print(f"{t:>10.4f} {curve.df(t):>10.6f} {curve.zero_rate(t) * 100:>8.4f} {err:>17.2e}")

    if args.plot:
        _plot(curve, args.plot)
        print(f"\nChart saved to {args.plot}")


def _plot(curve, path: str) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    ts = np.linspace(0.05, curve.times[-1], 400)
    zeros = [curve.zero_rate(t) * 100 for t in ts]
    fwds = [curve.forward_rate(t, t + 0.25) * 100 for t in ts]

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(ts, zeros, label="Zero rate (cont. comp.)", linewidth=2)
    ax.plot(ts, fwds, label="3M forward rate", linewidth=1.5, alpha=0.8)
    ax.scatter(curve.times[1:], [curve.zero_rate(t) * 100 for t in curve.times[1:]],
               s=18, zorder=3, label="Pillars")
    ax.set_xlabel("Maturity (years)")
    ax.set_ylabel("Rate (%)")
    ax.set_title("Bootstrapped AUD zero curve")
    ax.grid(alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=150)


if __name__ == "__main__":
    main()
