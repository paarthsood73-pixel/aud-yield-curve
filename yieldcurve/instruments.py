"""Market instruments used to build the curve.

Times are year fractions (ACT/365F style). AUD conventions are approximated:
swaps up to 3y pay quarterly against 3M BBSW, longer swaps pay semi-annually
against 6M BBSW. This is a single-curve setup, so the same curve is used for
projection and discounting.
"""
from __future__ import annotations

from dataclasses import dataclass

from .curve import ZeroCurve


def aud_swap_frequency(maturity: float) -> int:
    """Fixed-leg payments per year under AUD market convention."""
    return 4 if maturity <= 3.0 + 1e-9 else 2


@dataclass(frozen=True)
class Deposit:
    """Money market deposit (e.g. BBSW fixing) paying simple interest."""
    maturity: float
    rate: float

    @property
    def pillar(self) -> float:
        return self.maturity

    def implied_df(self, curve: ZeroCurve) -> float:
        return 1.0 / (1.0 + self.rate * self.maturity)


@dataclass(frozen=True)
class FRA:
    """Forward rate agreement from start to end (in years)."""
    start: float
    end: float
    rate: float

    @property
    def pillar(self) -> float:
        return self.end

    def implied_df(self, curve: ZeroCurve) -> float:
        return curve.df(self.start) / (1.0 + self.rate * (self.end - self.start))


@dataclass(frozen=True)
class Swap:
    """Vanilla fixed-for-floating par swap."""
    maturity: float
    rate: float
    frequency: int | None = None

    @property
    def pillar(self) -> float:
        return self.maturity

    @property
    def freq(self) -> int:
        return self.frequency or aud_swap_frequency(self.maturity)

    def schedule(self) -> list[float]:
        step = 1.0 / self.freq
        n = round(self.maturity * self.freq)
        return [step * (i + 1) for i in range(n)]

    def annuity(self, curve: ZeroCurve) -> float:
        step = 1.0 / self.freq
        return sum(step * curve.df(t) for t in self.schedule())

    def par_rate(self, curve: ZeroCurve) -> float:
        """Single-curve par rate: (1 - DF(T)) / annuity."""
        return (1.0 - curve.df(self.maturity)) / self.annuity(curve)

    def pv(self, curve: ZeroCurve, notional: float = 1.0) -> float:
        """PV to the fixed-rate receiver."""
        return notional * (self.rate - self.par_rate(curve)) * self.annuity(curve)
