"""Sequential bootstrap of a zero curve from deposits, FRAs and swaps."""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable, Union

from scipy.optimize import brentq

from .curve import ZeroCurve
from .instruments import FRA, Deposit, Swap

Instrument = Union[Deposit, FRA, Swap]


def bootstrap(instruments: Iterable[Instrument]) -> ZeroCurve:
    """Build a curve one pillar at a time, shortest maturity first.

    Deposits and FRAs have closed-form discount factors. Swaps are solved
    with Brent's method so that the swap reprices to par, because the swap's
    intermediate coupons can fall between existing pillars and depend on the
    interpolated (unknown) segment.
    """
    insts = sorted(instruments, key=lambda x: x.pillar)
    curve = ZeroCurve()
    for inst in insts:
        if isinstance(inst, (Deposit, FRA)):
            curve.add_pillar(inst.pillar, inst.implied_df(curve))
            continue

        guess = curve.df(inst.pillar)
        curve.add_pillar(inst.pillar, guess)

        def objective(df: float) -> float:
            curve.set_last_df(df)
            return inst.par_rate(curve) - inst.rate

        curve.set_last_df(brentq(objective, 1e-6, 1.5, xtol=1e-14))
    return curve


def load_instruments(path: str | Path) -> list[Instrument]:
    """Read a CSV with columns: type, start, maturity, rate (rate in percent)."""
    out: list[Instrument] = []
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            kind = row["type"].strip().lower()
            mat = float(row["maturity"])
            rate = float(row["rate"]) / 100.0
            if kind == "deposit":
                out.append(Deposit(mat, rate))
            elif kind == "fra":
                out.append(FRA(float(row["start"]), mat, rate))
            elif kind == "swap":
                out.append(Swap(mat, rate))
            else:
                raise ValueError(f"Unknown instrument type: {row['type']}")
    return out
