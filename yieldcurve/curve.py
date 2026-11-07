"""Zero curve with log-linear interpolation on discount factors."""
from __future__ import annotations

import math
from bisect import bisect_left
from typing import Sequence


class ZeroCurve:
    """Discount curve defined by pillar times (years) and discount factors.

    Interpolation is log-linear in discount factors, which means piecewise
    constant instantaneous forward rates between pillars. Beyond the last
    pillar the final forward rate is held flat.
    """

    def __init__(self, times: Sequence[float] | None = None, dfs: Sequence[float] | None = None):
        self.times: list[float] = [0.0]
        self.dfs: list[float] = [1.0]
        if times is not None and dfs is not None:
            for t, df in zip(times, dfs):
                self.add_pillar(t, df)

    def add_pillar(self, t: float, df: float) -> None:
        if t <= self.times[-1]:
            raise ValueError(f"Pillars must be strictly increasing, got {t} after {self.times[-1]}")
        if df <= 0:
            raise ValueError("Discount factors must be positive")
        self.times.append(t)
        self.dfs.append(df)

    def set_last_df(self, df: float) -> None:
        self.dfs[-1] = df

    def df(self, t: float) -> float:
        if t < 0:
            raise ValueError("Time must be non-negative")
        if t == 0:
            return 1.0
        i = bisect_left(self.times, t)
        if i < len(self.times) and self.times[i] == t:
            return self.dfs[i]
        if i >= len(self.times):
            # flat forward extrapolation using the last segment
            t0, t1 = self.times[-2], self.times[-1]
            d0, d1 = self.dfs[-2], self.dfs[-1]
            f = -math.log(d1 / d0) / (t1 - t0)
            return d1 * math.exp(-f * (t - t1))
        t0, t1 = self.times[i - 1], self.times[i]
        d0, d1 = self.dfs[i - 1], self.dfs[i]
        w = (t - t0) / (t1 - t0)
        return math.exp((1 - w) * math.log(d0) + w * math.log(d1))

    def zero_rate(self, t: float) -> float:
        """Continuously compounded zero rate."""
        if t <= 0:
            t = 1e-6
        return -math.log(self.df(t)) / t

    def forward_rate(self, t1: float, t2: float) -> float:
        """Simple forward rate between t1 and t2."""
        return (self.df(t1) / self.df(t2) - 1.0) / (t2 - t1)

    def __repr__(self) -> str:
        return f"ZeroCurve(pillars={len(self.times) - 1}, max_t={self.times[-1]:.2f}y)"
