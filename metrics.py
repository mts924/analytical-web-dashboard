"""Financial metrics used by the dashboard.

Every function is "pure": it takes data in and returns numbers,
with no display code, so it can be reused and tested on its own.
"""
import numpy as np
import pandas as pd

TRADING_DAYS = 252


def total_return(prices):
    """Return from the first to the last price."""
    return prices.iloc[-1] / prices.iloc[0] - 1


def annualized_volatility(returns):
    """Standard deviation of daily returns, scaled to one year."""
    return returns.std() * np.sqrt(TRADING_DAYS)


def sharpe_ratio(returns, rf_annual=0.0):
    """Annualized excess return per unit of total volatility."""
    excess = returns - rf_annual / TRADING_DAYS
    return excess.mean() / returns.std() * np.sqrt(TRADING_DAYS)


def sortino_ratio(returns, rf_annual=0.0):
    """Like Sharpe, but only penalizes returns below the risk-free rate."""
    excess = returns - rf_annual / TRADING_DAYS
    downside = np.sqrt((excess.clip(upper=0) ** 2).mean()) * np.sqrt(TRADING_DAYS)
    return excess.mean() * TRADING_DAYS / downside


def drawdown(prices):
    """Fall from the running peak, for every day."""
    return prices / prices.cummax() - 1


def max_drawdown(prices):
    """Worst peak-to-trough fall over the period."""
    return drawdown(prices).min()


def beta_alpha(asset_returns, market_returns, rf_annual=0.0):
    """CAPM beta and annualized alpha of an asset against the market."""
    pair = pd.concat([asset_returns, market_returns], axis=1).dropna()
    r, m = pair.iloc[:, 0], pair.iloc[:, 1]
    rf = rf_annual / TRADING_DAYS
    beta = r.cov(m) / m.var()
    alpha = ((r - rf).mean() - beta * (m - rf).mean()) * TRADING_DAYS
    return beta, alpha


def hedge_ratio(log_a, log_b):
    """Units of B that offset one unit of A (regression of log prices)."""
    return np.polyfit(log_b, log_a, 1)[0]


def half_life(spread):
    """Days for the spread to close half its gap (mean-reversion speed)."""
    lam = np.polyfit(spread.shift(1).iloc[1:], spread.diff().iloc[1:], 1)[0]
    return -np.log(2) / lam if lam < 0 else float("nan")
