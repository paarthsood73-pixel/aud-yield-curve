import math
from pathlib import Path

import pytest

from yieldcurve import FRA, Deposit, Swap, ZeroCurve, bootstrap, load_instruments

DATA = Path(__file__).resolve().parent.parent / "data" / "sample_aud_rates.csv"


@pytest.fixture(scope="module")
def market():
    insts = load_instruments(DATA)
    return insts, bootstrap(insts)


def test_every_instrument_reprices(market):
    insts, curve = market
    for inst in insts:
        if isinstance(inst, Swap):
            assert inst.par_rate(curve) == pytest.approx(inst.rate, abs=1e-10)
            assert inst.pv(curve) == pytest.approx(0.0, abs=1e-10)
        elif isinstance(inst, Deposit):
            assert curve.df(inst.maturity) == pytest.approx(1 / (1 + inst.rate * inst.maturity))
        elif isinstance(inst, FRA):
            assert curve.forward_rate(inst.start, inst.end) == pytest.approx(inst.rate, abs=1e-12)


def test_discount_factors_decrease(market):
    _, curve = market
    assert all(a > b for a, b in zip(curve.dfs, curve.dfs[1:]))


def test_flat_curve_recovers_flat_zero():
    r = 0.04
    curve = ZeroCurve([1, 2, 5], [math.exp(-r * t) for t in (1, 2, 5)])
    for t in (0.5, 1.7, 3.3, 7.0):
        assert curve.zero_rate(t) == pytest.approx(r)


def test_aud_frequency_convention():
    assert Swap(3, 0.04).freq == 4
    assert Swap(5, 0.04).freq == 2


def test_rejects_non_increasing_pillars():
    curve = ZeroCurve([1.0], [0.96])
    with pytest.raises(ValueError):
        curve.add_pillar(1.0, 0.95)
