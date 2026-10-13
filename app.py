import pandas as pd
import yfinance as yf
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Market Analytics Dashboard", layout="wide")
st.title("Market Analytics Dashboard")

# --- Controls in the sidebar ---
tickers = st.sidebar.multiselect("Assets", ["SPY", "QQQ", "IWM", "GLD", "EWQ", "TLT"],
                                 default=["SPY", "QQQ", "IWM", "GLD"])
period = st.sidebar.selectbox("Period", ["6mo", "1y", "2y", "5y"], index=1)
if not tickers:
    st.warning("Pick at least one asset.")
    st.stop()

# --- Data (cached for 1 hour) ---
@st.cache_data(ttl=3600)
def load_prices(tickers, period):
    return yf.download(tickers, period=period)["Close"]

prices = load_prices(tickers, period)
returns = prices.pct_change().dropna()

# --- Metrics (your step 3) ---
total_return = prices.iloc[-1] / prices.iloc[0] - 1
volatility = returns.std() * 252 ** 0.5
sharpe = returns.mean() / returns.std() * 252 ** 0.5
drawdown = prices / prices.cummax() - 1
summary = pd.DataFrame({"Total return": total_return, "Volatility": volatility,
                        "Sharpe": sharpe, "Max drawdown": drawdown.min()})

# --- KPI cards ---
cols = st.columns(len(tickers))
for col, t in zip(cols, prices.columns):
    col.metric(t, f"${prices[t].iloc[-1]:,.2f}", f"{total_return[t]:+.1%}")

# --- Charts (your step 4) ---
left, right = st.columns(2)
rebased = prices / prices.iloc[0] * 100
left.plotly_chart(px.line(rebased, title="Performance, rebased to 100"), use_container_width=True)
right.plotly_chart(px.line(drawdown, title="Drawdown from peak"), use_container_width=True)

st.subheader("Risk and return")
st.dataframe(summary.style.format({"Total return": "{:.1%}", "Volatility": "{:.1%}",
                                   "Sharpe": "{:.2f}", "Max drawdown": "{:.1%}"}))

st.plotly_chart(px.imshow(returns.corr(), text_auto=".2f", color_continuous_scale="RdBu_r",
                          zmin=-1, zmax=1, title="Correlation of daily returns"))
# --- KPI cards ---
cols = st.columns(len(tickers))
for col, t in zip(cols, prices.columns):
    col.metric(t, f"${prices[t].iloc[-1]:,.2f}", f"{total_return[t]:+.1%}")

# --- Automatic insight ---
best = summary["Sharpe"].idxmax()
riskiest = summary["Volatility"].idxmax()
st.info(f"Best risk-adjusted asset: **{best}** (Sharpe {summary.loc[best, 'Sharpe']:.2f}). "
        f"Most volatile: **{riskiest}** ({summary.loc[riskiest, 'Volatility']:.1%} a year).")

tab1, tab2, tab3 = st.tabs(["📈 Performance", "⚠️ Risk", "🔗 Correlation"])

with tab1:
    rebased = prices / prices.iloc[0] * 100
    st.plotly_chart(px.line(rebased, title="Value of 100 invested"), use_container_width=True)
    st.caption("Every asset starts at 100, so they can be compared on the same scale.")

with tab2:
    st.plotly_chart(px.line(drawdown, title="Drawdown from peak"), use_container_width=True)
    rolling_vol = returns.rolling(30).std() * 252 ** 0.5
    st.plotly_chart(px.line(rolling_vol, title="30-day rolling volatility (annualized)"),
                    use_container_width=True)
    st.subheader("Risk and return")
    st.dataframe(summary.style.format({"Total return": "{:.1%}", "Volatility": "{:.1%}",
                                       "Sharpe": "{:.2f}", "Max drawdown": "{:.1%}"}))

with tab3:
    st.plotly_chart(px.imshow(returns.corr(), text_auto=".2f", color_continuous_scale="RdBu_r",
                              zmin=-1, zmax=1, title="Correlation of daily returns"),
                    use_container_width=True)
    st.caption("Close to 1 = they move together. Low or negative = good diversification.")
