"""Automated checks for metrics.py: each test uses data where the answer is known."""
import numpy as np
import pandas as pd
import pytest

import metrics as fm


def test_total_return():
    prices = pd.Series([100, 110, 120])
    assert fm.total_return(prices) == pytest.approx(0.20)


def test_max_drawdown():
    # Peak at 120, trough at 90: (90 / 120) - 1 = -25%
    prices = pd.Series([100, 120, 90, 130])
    assert fm.max_drawdown(prices) == pytest.approx(-0.25)


def test_constant_returns_have_zero_volatility():
    returns = pd.Series([0.01] * 50)
    assert fm.annualized_volatility(returns) == pytest.approx(0.0)


def test_risk_free_rate_lowers_sharpe():
    rng = np.random.default_rng(0)
    returns = pd.Series(rng.normal(0.001, 0.01, 500))
    assert fm.sharpe_ratio(returns, rf_annual=0.04) < fm.sharpe_ratio(returns, rf_annual=0.0)


def test_market_has_beta_one_and_zero_alpha():
    rng = np.random.default_rng(1)
    market = pd.Series(rng.normal(0, 0.01, 500))
    beta, alpha = fm.beta_alpha(market, market)
    assert beta == pytest.approx(1.0)
    assert alpha == pytest.approx(0.0, abs=1e-10)


def test_twice_the_market_has_beta_two():
    rng = np.random.default_rng(2)
    market = pd.Series(rng.normal(0, 0.01, 500))
    beta, _ = fm.beta_alpha(2 * market, market)
    assert beta == pytest.approx(2.0)


def test_hedge_ratio_recovers_known_slope():
    log_b = pd.Series(np.linspace(1, 2, 100))
    log_a = 1.5 * log_b + 0.3
    assert fm.hedge_ratio(log_a, log_b) == pytest.approx(1.5)


def test_half_life_of_simulated_mean_reverting_spread():
    # s_t = 0.9 * s_(t-1) + noise  ->  lambda = -0.1  ->  half-life = ln(2) / 0.1 ≈ 6.9 days
    rng = np.random.default_rng(3)
    s = np.zeros(5000)
    for t in range(1, 5000):
        s[t] = 0.9 * s[t - 1] + rng.normal(0, 1)
    assert fm.half_life(pd.Series(s)) == pytest.approx(np.log(2) / 0.1, rel=0.2)
