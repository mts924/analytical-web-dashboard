import html
import itertools

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
import yfinance as yf
from statsmodels.tsa.stattools import coint

import metrics as fm
import ui

st.set_page_config(page_title="Market Analytics Dashboard", page_icon="📊", layout="wide")
ui.apply()
ui.header("Market Analytics Dashboard",
          "Performance, risk and relationships across 40+ assets: stocks, ETFs, bonds, gold and crypto.")

# --- Asset universe ---
UNIVERSE = {
    "US indices (ETFs)": {"SPY": "S&P 500", "QQQ": "Nasdaq 100", "IWM": "Russell 2000", "DIA": "Dow Jones"},
    "Countries (ETFs)": {"EWQ": "France", "EWG": "Germany", "VGK": "Europe", "EWJ": "Japan",
                         "EWS": "Singapore", "FXI": "China", "EEM": "Emerging markets"},
    "Sectors (ETFs)": {"XLK": "US Tech", "XLF": "US Financials", "XLE": "US Energy", "XLV": "US Healthcare"},
    "Bonds & commodities": {"TLT": "US 20y+ bonds", "HYG": "High-yield bonds", "GLD": "Gold",
                            "SLV": "Silver", "USO": "Oil"},
    "US stocks": {"AAPL": "Apple", "MSFT": "Microsoft", "NVDA": "Nvidia", "AMZN": "Amazon",
                  "GOOGL": "Alphabet", "META": "Meta", "TSLA": "Tesla", "JPM": "JPMorgan"},
    "European stocks": {"MC.PA": "LVMH", "TTE.PA": "TotalEnergies", "AIR.PA": "Airbus", "OR.PA": "L'Oréal",
                        "BNP.PA": "BNP Paribas", "ASML.AS": "ASML", "SAP.DE": "SAP"},
    "Asian stocks": {"D05.SI": "DBS", "7203.T": "Toyota", "2330.TW": "TSMC", "0700.HK": "Tencent"},
    "Crypto": {"BTC-USD": "Bitcoin", "ETH-USD": "Ethereum"},
}
NAMES = {t: n for group in UNIVERSE.values() for t, n in group.items()}

PRESETS = {
    "Core markets": ["SPY", "QQQ", "IWM", "GLD"],
    "Stocks, bonds and gold": ["SPY", "TLT", "GLD", "HYG"],
    "Global equities": ["SPY", "VGK", "EWJ", "EEM", "EWS"],
    "Mega-cap tech": ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META"],
    "Europe vs Asia": ["MC.PA", "TTE.PA", "AIR.PA", "D05.SI", "7203.T", "2330.TW"],
    "Commodities and crypto": ["GLD", "SLV", "USO", "BTC-USD", "ETH-USD"],
    "Pairs trading candidates": ["GLD", "SLV", "XLE", "USO", "SPY", "DIA"],
}


def label(t):
    """Readable name used in cards, tables and charts."""
    return f"{NAMES[t]} ({t})" if t in NAMES else t


def pick_label(t):
    """Ticker first, so it stays visible when the sidebar truncates the text."""
    return f"{t} · {NAMES[t]}" if t in NAMES else t


# --- Sidebar: choose assets ---
st.sidebar.markdown("### Select assets")
preset = st.sidebar.selectbox("Start from a preset", list(PRESETS))
tickers = st.sidebar.multiselect("Assets", [t for t in NAMES], default=PRESETS[preset],
                                 format_func=pick_label, placeholder="Search by name or ticker")
custom = st.sidebar.text_input("Add other tickers", placeholder="e.g. NFLX, SAN.PA",
                               help="Any ticker known to Yahoo Finance. Suffixes: .PA Paris, .SI Singapore, "
                                    ".T Tokyo, .HK Hong Kong.")
tickers += [t.strip().upper() for t in custom.split(",") if t.strip()]
tickers = list(dict.fromkeys(tickers))  # remove duplicates, keep order
st.sidebar.markdown("### Period")
period = st.sidebar.radio("Period", ["6mo", "1y", "2y", "5y"], index=1, horizontal=True,
                          label_visibility="collapsed")

if not tickers:
    st.warning("Pick at least one asset in the sidebar.")
    st.stop()


# --- Data (cached for 1 hour) ---
@st.cache_data(ttl=3600)
def load_prices(tickers, period):
    data = yf.download(tickers, period=period, progress=False)["Close"]
    if isinstance(data, pd.Series):
        data = data.to_frame(tickers[0])
    return data


@st.cache_data(ttl=86400)
def load_info(ticker):
    try:
        return yf.Ticker(ticker).info
    except Exception:
        return {}


data = load_prices(tickers, period).dropna(axis=1, how="all")
missing = [t for t in tickers if t not in data.columns]
if missing:
    st.warning(f"No data found for: {', '.join(missing)}")

# Weekdays only (crypto trades on weekends), and fill exchange holidays with the last price
prices = data[data.index.dayofweek < 5].ffill().dropna()
if prices.empty or len(prices) < 2:
    st.error("Not enough data to analyze. Try other assets or a longer period.")
    st.stop()
returns = prices.pct_change().dropna()
named_prices = prices.rename(columns=label)  # same data, readable names, for charts


# --- Risk-free rate: 3-month US T-bill (^IRX, quoted in % per year) ---
@st.cache_data(ttl=86400)
def load_risk_free(period):
    irx = yf.download("^IRX", period=period, progress=False)["Close"]
    if isinstance(irx, pd.DataFrame):
        irx = irx.iloc[:, 0]
    return float(irx.dropna().mean() / 100) if not irx.dropna().empty else 0.0


rf_annual = load_risk_free(period)

# --- Metrics (calculations live in metrics.py) ---
total_return = fm.total_return(prices)
volatility = fm.annualized_volatility(returns)
sharpe = fm.sharpe_ratio(returns, rf_annual)
sortino = fm.sortino_ratio(returns, rf_annual)
drawdown = fm.drawdown(prices)

# --- Beta and alpha vs the S&P 500 (CAPM) ---
bench_ret = load_prices(["SPY"], period)["SPY"].pct_change().reindex(returns.index)
beta, alpha = {}, {}
for t in returns.columns:
    beta[t], alpha[t] = fm.beta_alpha(returns[t], bench_ret, rf_annual)

summary = pd.DataFrame({"Total return": total_return, "Volatility": volatility,
                        "Sharpe": sharpe, "Sortino": sortino, "Max drawdown": drawdown.min(),
                        "Beta": pd.Series(beta), "Alpha": pd.Series(alpha)})
summary.index = [label(t) for t in summary.index]

# --- KPI cards, 4 per row ---
for i in range(0, len(prices.columns), 4):
    row = st.columns(4)
    for col, t in zip(row, prices.columns[i:i + 4]):
        col.metric(label(t), f"{prices[t].iloc[-1]:,.2f}", f"{total_return[t]:+.1%}")
st.caption(f"Data as of {prices.index[-1]:%d %b %Y}. Prices are in each asset's own currency "
           f"(e.g. EUR for Paris stocks, SGD for DBS).")

# --- Automatic insight ---
best = summary["Sharpe"].idxmax()
riskiest = summary["Volatility"].idxmax()
ui.insight(f"Best risk-adjusted asset: <b>{html.escape(best)}</b> (Sharpe {summary.loc[best, 'Sharpe']:.2f}). "
           f"Most volatile: <b>{html.escape(riskiest)}</b> ({summary.loc[riskiest, 'Volatility']:.1%} a year).")

tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(["Performance", "Risk", "Correlation", "Portfolio",
                                                    "Company", "Stat arb", "Methodology"])

with tab1:
    rebased = named_prices / named_prices.iloc[0] * 100
    ui.chart(px.line(rebased, title="Value of 100 invested"), width="stretch")
    st.caption("Every asset starts at 100, so they can be compared on the same scale.")

with tab2:
    ui.chart(px.line(drawdown.rename(columns=label), title="Drawdown from peak"), width="stretch")
    rolling_vol = returns.rolling(30).std() * 252 ** 0.5
    ui.chart(px.line(rolling_vol.rename(columns=label), title="30-day rolling volatility (annualized)"),
             width="stretch")
    st.subheader("Risk and return")


    def tone(v):
        return f"color: {ui.GREEN}" if v > 0 else f"color: {ui.RED}"


    styled = (summary.style
              .format({"Total return": "{:+.1%}", "Volatility": "{:.1%}", "Sharpe": "{:.2f}",
                       "Sortino": "{:.2f}", "Max drawdown": "{:.1%}", "Beta": "{:.2f}", "Alpha": "{:+.1%}"})
              .map(tone, subset=["Total return", "Alpha"]))
    st.dataframe(styled, width="stretch")
    st.caption(f"Sharpe and Sortino use a risk-free rate of {rf_annual:.2%} a year "
               f"(average 3-month US T-bill over the period). Beta and alpha are measured against the S&P 500.")

with tab3:
    n = len(prices.columns)
    corr = returns.rename(columns=label).corr()
    ui.chart(px.imshow(corr, text_auto=".2f", color_continuous_scale=ui.DIVERGING,
                       zmin=-1, zmax=1, title="Correlation of daily returns", height=max(420, 50 * n)),
             width="stretch")
    st.caption("Close to 1 = they move together. Low or negative = good diversification.")

with tab4:
    st.write("Choose how much to put in each asset. Weights are rescaled to add up to 100%.")
    w_raw = {}
    for i in range(0, len(prices.columns), 4):
        row = st.columns(4)
        for col, t in zip(row, prices.columns[i:i + 4]):
            w_raw[t] = col.slider(label(t), 0, 100, 25, step=5)

    if sum(w_raw.values()) == 0:
        st.warning("Give at least one asset a weight above 0.")
    else:
        weights = pd.Series(w_raw) / sum(w_raw.values())

        # Buy and hold: invest once on day 1, never rebalance
        port_value = (prices / prices.iloc[0] * weights).sum(axis=1) * 100
        port_ret = port_value.pct_change().dropna()

        p_return = port_value.iloc[-1] / 100 - 1
        p_vol = port_ret.std() * 252 ** 0.5
        p_sharpe = fm.sharpe_ratio(port_ret, rf_annual)
        p_mdd = (port_value / port_value.cummax() - 1).min()

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Return", f"{p_return:+.1%}")
        c2.metric("Volatility", f"{p_vol:.1%}")
        c3.metric("Sharpe", f"{p_sharpe:.2f}")
        c4.metric("Max drawdown", f"{p_mdd:.1%}")

        avg_vol = (volatility[weights.index] * weights).sum()
        if avg_vol - p_vol > 0.005:
            st.success(f"Diversification at work: the weighted average volatility of your assets is "
                       f"{avg_vol:.1%}, but your portfolio's is only {p_vol:.1%}, "
                       f"because the assets don't move perfectly together.")

        chart = (named_prices / named_prices.iloc[0] * 100).assign(Portfolio=port_value)
        fig = px.line(chart, title="Your portfolio vs each asset (100 invested)")
        fig.update_traces(opacity=0.35)
        fig.update_traces(selector={"name": "Portfolio"}, opacity=1, line_width=4)
        ui.chart(fig, width="stretch")
        st.caption("Simplification: currency movements between assets are ignored.")

with tab5:
    pick = st.selectbox("Choose an asset", list(prices.columns), format_func=label)
    info = load_info(pick)


    def fmt_big(x):
        if not isinstance(x, (int, float)):
            return "—"
        for div, suffix in [(1e12, "T"), (1e9, "B"), (1e6, "M")]:
            if abs(x) >= div:
                return f"{x / div:.1f}{suffix}"
        return f"{x:,.0f}"


    def fmt_num(x):
        return f"{x:.2f}" if isinstance(x, (int, float)) else "—"


    if not info:
        st.warning("Details are unavailable for this asset right now.")
    else:
        st.subheader(info.get("longName", label(pick)))
        details = [info.get("sector"), info.get("industry"), info.get("country"), info.get("currency")]
        st.caption(" · ".join(d for d in details if d))

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Market cap", fmt_big(info.get("marketCap") or info.get("totalAssets")))
        c2.metric("P/E (trailing)", fmt_num(info.get("trailingPE")))
        c3.metric("P/E (forward)", fmt_num(info.get("forwardPE")))
        c4.metric("Beta", fmt_num(info.get("beta")))

        low, high = info.get("fiftyTwoWeekLow"), info.get("fiftyTwoWeekHigh")
        if isinstance(low, (int, float)) and isinstance(high, (int, float)):
            st.write(f"**52-week range:** {low:,.2f} – {high:,.2f}")
        summary_text = info.get("longBusinessSummary")
        if summary_text:
            st.write(summary_text)

with tab6:
    st.write("Pairs trading: find two assets whose prices are tied together, "
             "and bet on their gap closing when it gets unusually wide.")

    if len(prices.columns) < 2:
        st.warning("Select at least two assets in the sidebar.")
    else:
        log_p = np.log(prices)

        # --- Train / test split: find and fit the pair on the past, test it on later data ---
        train_pct = st.slider("Share of the period used for training (%)", 30, 80, 50, step=5)
        split = int(len(log_p) * train_pct / 100)
        train, test = log_p.iloc[:split], log_p.iloc[split:]
        split_date = test.index[0]
        st.caption(f"Training: {train.index[0]:%b %d, %Y} → {train.index[-1]:%b %d, %Y}  ·  "
                   f"Testing (out-of-sample): {test.index[0]:%b %d, %Y} → {test.index[-1]:%b %d, %Y}")

        if len(train) < 60 or len(test) < 30:
            st.warning("Not enough data for a train/test split. Choose a longer period (2y or 5y).")
        else:
            # --- 1. Scan pairs on the TRAINING period only ---
            @st.cache_data(ttl=3600)
            def scan_pairs(log_p):
                rows = []
                for a, b in itertools.combinations(log_p.columns, 2):
                    rows.append({"a": a, "b": b, "p-value": coint(log_p[a], log_p[b])[1]})
                return pd.DataFrame(rows).sort_values("p-value")


            pairs = scan_pairs(train)
            st.subheader("1. Pair scanner (training period)")
            table = pairs.assign(Pair=[f"{label(a)} / {label(b)}" for a, b in zip(pairs["a"], pairs["b"])])
            st.dataframe(table[["Pair", "p-value"]].style.format({"p-value": "{:.3f}"}),
                         hide_index=True, width="stretch")
            st.caption(f"Engle-Granger test on the training period only. With {len(pairs)} pairs tested, "
                       f"about {len(pairs) * 0.05:.0f} could fall below 0.05 by pure chance.")

            # --- 2. Backtest one pair ---
            st.subheader("2. Backtest a pair")
            cols_list = list(prices.columns)
            c1, c2 = st.columns(2)
            a = c1.selectbox("Asset A", cols_list, index=cols_list.index(pairs.iloc[0]["a"]), format_func=label)
            b = c2.selectbox("Asset B", cols_list, index=cols_list.index(pairs.iloc[0]["b"]), format_func=label)

            if a == b:
                st.warning("Pick two different assets.")
            else:
                s1, s2, s3, s4 = st.columns(4)
                window = s1.slider("Z-score window (days)", 10, 120, 40, step=5)
                entry = s2.slider("Entry threshold (z)", 1.0, 3.0, 2.0, step=0.25)
                exit_z = s3.slider("Exit threshold (z)", 0.0, 1.0, 0.5, step=0.25)
                cost_bps = s4.slider("Cost per trade (bps)", 0, 50, 10, step=5)

                # Hedge ratio and half-life estimated on the TRAINING period only
                beta = fm.hedge_ratio(train[a], train[b])
                spread = log_p[a] - beta * log_p[b]
                s_tr = spread.loc[train.index]
                half_life = fm.half_life(s_tr)

                # The rolling z-score only uses past data, so it can be computed everywhere
                z = (spread - spread.rolling(window).mean()) / spread.rolling(window).std()

                position = pd.Series(np.nan, index=z.index)
                position[z > entry] = -1
                position[z < -entry] = 1
                position[z.abs() < exit_z] = 0
                position = position.ffill().fillna(0)
                position[position.index < split_date] = 0  # trade only in the test period

                # Trade on the NEXT day, and pay costs on both legs whenever the position changes
                spread_ret = returns[a] - beta * returns[b]
                held = position.shift(1).reindex(spread_ret.index).fillna(0)
                turnover = held.diff().abs().fillna(0)
                costs = turnover * (1 + abs(beta)) * cost_bps / 10_000
                strat = (held * spread_ret - costs).loc[split_date:]
                equity = (1 + strat).cumprod() * 100
                trades = int((turnover.loc[split_date:] > 0).sum())
                oos_sharpe = strat.mean() / strat.std() * 252 ** 0.5 if strat.std() > 0 else float("nan")
                p_train = coint(train[a], train[b])[1]
                p_test = coint(test[a], test[b])[1]

                m1, m2, m3 = st.columns(3)
                m1.metric("Cointegration p-value (train)", f"{p_train:.3f}")
                m2.metric("Cointegration p-value (test)", f"{p_test:.3f}")
                m3.metric("Hedge ratio β (train)", f"{beta:.2f}")
                m4, m5, m6 = st.columns(3)
                m4.metric("Half-life (train)", f"{half_life:.0f} days" if half_life == half_life else "—")
                m5.metric("Out-of-sample return (after costs)", f"{equity.iloc[-1] / 100 - 1:+.1%}")
                m6.metric("Out-of-sample Sharpe / trades", f"{oos_sharpe:.2f} / {trades}")

                if p_train < 0.05 and p_test > 0.10:
                    st.warning("The pair looked cointegrated in training but not in the test period: "
                               "the relationship may have broken down. This is the main risk of pairs trading.")

                shade = dict(x0=log_p.index[0], x1=split_date, fillcolor="grey", opacity=0.15, line_width=0)

                rebased_pair = named_prices[[label(a), label(b)]] / named_prices[[label(a), label(b)]].iloc[0] * 100
                fig_p = px.line(rebased_pair, title=f"{label(a)} vs {label(b)} (grey = training period)")
                fig_p.add_vrect(**shade)
                ui.chart(fig_p, width="stretch")

                fig_z = px.line(z, title="Z-score of the spread (trading only happens outside the grey area)")
                fig_z.add_vrect(**shade)
                for level in (entry, -entry):
                    fig_z.add_hline(y=level, line_dash="dash", line_color="red")
                for level in (exit_z, -exit_z):
                    fig_z.add_hline(y=level, line_dash="dot", line_color="grey")
                fig_z.update_layout(showlegend=False)
                ui.chart(fig_z, width="stretch")

                fig_e = px.line(equity, title="Out-of-sample equity after costs (100 invested)")
                fig_e.update_layout(showlegend=False)
                ui.chart(fig_e, width="stretch")
                st.caption("Costs are charged on both legs each time the position changes. "
                           "Borrowing costs for the short leg are not included.")

with tab7:
    st.header("Methodology")
    st.write("How every number in this dashboard is calculated.")

    with st.expander("Returns and volatility", expanded=True):
        st.latex(r"r_t = \frac{P_t}{P_{t-1}} - 1")
        st.write("Daily simple return, from adjusted closing prices (dividends and splits included).")
        st.latex(r"\sigma_{\text{annual}} = \sigma_{\text{daily}} \times \sqrt{252}")
        st.write("Volatility is annualized with √252, the number of trading days in a year, "
                 "because the variances of independent daily returns add up over time.")

    with st.expander("Sharpe and Sortino ratios"):
        st.latex(r"\text{Sharpe} = \frac{\overline{r - r_f}}{\sigma_{\text{daily}}} \times \sqrt{252}")
        st.latex(r"\text{Sortino} = \frac{\overline{r - r_f} \times 252}{\sigma_{\text{down}}}, \qquad "
                 r"\sigma_{\text{down}} = \sqrt{\overline{\min(r - r_f,\, 0)^2}} \times \sqrt{252}")
        st.write(f"The risk-free rate is the average 3-month US T-bill yield over the period "
                 f"({rf_annual:.2%} a year). Sortino only penalizes returns below the risk-free rate.")

    with st.expander("Maximum drawdown"):
        st.latex(r"DD_t = \frac{P_t}{\max_{s \le t} P_s} - 1, \qquad \text{MDD} = \min_t DD_t")
        st.write("The worst fall from a running peak to a subsequent trough over the period.")

    with st.expander("Beta and alpha (CAPM)"):
        st.latex(r"\beta = \frac{\operatorname{Cov}(r, r_m)}{\operatorname{Var}(r_m)}")
        st.latex(r"\alpha = \left[\, \overline{r - r_f} - \beta \, \overline{r_m - r_f} \,\right] \times 252")
        st.write("The market is the S&P 500 (SPY). Alpha is the annual return not explained by "
                 "the asset's exposure to the market.")

    with st.expander("Correlation and portfolio"):
        st.write("Correlations are Pearson correlations of daily returns.")
        st.latex(r"V_t = 100 \times \sum_i w_i \, \frac{P_{i,t}}{P_{i,0}}")
        st.write("The portfolio is buy and hold: invested once at the start and never rebalanced. "
                 "Currency movements between assets are ignored.")

    with st.expander("Statistical arbitrage"):
        st.latex(r"s_t = \ln P^A_t - \beta \, \ln P^B_t")
        st.latex(r"z_t = \frac{s_t - \mu^{(w)}_t}{\sigma^{(w)}_t}")
        st.latex(r"\Delta s_t = c + \lambda \, s_{t-1} + \varepsilon_t, \qquad "
                 r"\text{half-life} = -\frac{\ln 2}{\lambda}")
        st.write("Pairs are scanned and fitted on a training period only (cointegration test, hedge ratio, "
                 "half-life), then traded on the later, unseen test period. The strategy shorts the spread "
                 "when z exceeds the entry threshold, buys it below minus the threshold, and closes inside "
                 "the exit band. Signals are traded the next day, and transaction costs are charged on both "
                 "legs at each position change. Remaining limitations: the hedge ratio stays fixed after "
                 "training, and borrowing costs for the short leg are ignored.")

    with st.expander("Data and limitations"):
        st.write(f"""
- Source: Yahoo Finance (via yfinance), refreshed at most once an hour. Last data point: {prices.index[-1]:%B %d, %Y}.
- Weekdays only; exchange holidays are filled with the last available price.
- Prices are in each asset's own currency.
- Past performance does not predict future results.
""")

    st.warning("This dashboard is an educational project and does not constitute investment advice.")

ui.footer("Educational project, not investment advice · Data: Yahoo Finance · Built with Python and Streamlit")
