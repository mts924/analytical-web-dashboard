# 📈 Market Analytics Dashboard

**Live app → https://analytical-web-dashboard-motevally.streamlit.app **

An interactive web dashboard to analyze the performance, risk and relationships of 40+ assets
(ETFs, US / European / Asian stocks, bonds, commodities and crypto), built in Python with Streamlit.

![Dashboard overview]
<img width="1464" height="832" alt="Capture d’écran 2026-10-21 à 21 18 05" src="https://github.com/user-attachments/assets/3aa13f2f-561c-4583-9165-46529dac24ce" />


## Features

| Tab | What it does |
|---|---|
| 📈 Performance | KPI cards and performance rebased to 100, with an automatic insight |
| ⚠️ Risk | Drawdowns, 30-day rolling volatility, Sharpe, Sortino, max drawdown, CAPM beta and alpha |
| 🔗 Correlation | Correlation heatmap of daily returns |
| 🧺 Portfolio | Custom-weight portfolio builder showing the diversification benefit |
| 🏢 Company | Fundamentals: market cap, P/E, beta, 52-week range, business description |
| ⚖️ Stat arb | Pairs trading: cointegration scanner and out-of-sample backtest with transaction costs |
| 📘 Methodology | Every formula used in the app |

![Statistical arbitrage tab]
<img width="1464" height="832" alt="Capture d’écran 2026-10-21 à 21 21 01" src="https://github.com/user-attachments/assets/612006b3-387e-4179-b92b-74a6b86df42c" />


## Methodology highlights

- **Risk-adjusted metrics** use the 3-month US T-bill as the risk-free rate.
- **Beta and alpha** are estimated against the S&P 500 (CAPM).
- **Pairs trading** follows the Engle-Granger approach: the pair is selected and fitted on a training
  period only, then traded on unseen data with next-day execution and transaction costs,
  to avoid look-ahead and selection bias.

## Tech stack

Python · pandas · NumPy · statsmodels · Plotly · Streamlit · yfinance

## Run it locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Limitations

Data comes from Yahoo Finance and may contain gaps. Prices are in each asset's own currency, and the
portfolio ignores exchange-rate movements. Short-selling borrowing costs are not modeled.

*This is an educational project and does not constitute investment advice.*

## Author

**Julia Motevally**: [LinkedIn](https://linkedin.com/in/julia-motevally-b25b482b5)
