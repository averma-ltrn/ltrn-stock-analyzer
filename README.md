# LTRN Stock Analytics Dashboard

A production-grade equity analytics pipeline and interactive dashboard built for Lantern Pharma (NASDAQ: LTRN). Ingests daily market data, calculates technical indicators, and surfaces institutional-quality analysis through a hosted web application — updated automatically every weekday.

**Live dashboard:** [ltrn-stock-analyzer.streamlit.app](https://ltrn-stock-analyzer.streamlit.app)

---

## Overview

This project replaces manual stock monitoring with a fully automated data pipeline. Raw price and fundamental data is pulled from Yahoo Finance each evening after market close, transformed into analysis-ready metrics, and committed back to the repository. The Streamlit dashboard reads from these files and serves current data to any stakeholder with the link — no login, no software, no manual updates required.

---

## Features

### Dashboard
- **Price & Volume** — Interactive candlestick/line chart with optional 20/50-day moving averages and Bollinger Bands. Color-coded volume panel with elevated volume day detection and tabular breakdown of sessions exceeding 2 standard deviations above the 30-day average
- **Technical Indicators** — RSI (14-day) with overbought/oversold thresholds, Bollinger Bands with price overlay, current signal reading
- **Volatility & Drawdown** — Rolling drawdown from peak, 30-day rolling volatility, distribution of daily returns histogram, risk summary metrics
- **Fundamentals** — Market cap, cash position, total debt, EPS (TTM), 52-week range, shares outstanding, beta, indexed price performance chart

### Pipeline
- Incremental daily ingestion via `yfinance`
- 19 calculated columns including RSI, Bollinger Bands, moving averages, volume z-score, drawdown, rolling volatility, indexed price
- Automated daily refresh via GitHub Actions (weekdays at 6pm ET)
- Data committed back to repository on each run — full audit trail via git history

---

## Tech Stack

| Layer | Technology |
|---|---|
| Data ingestion | Python, yfinance, pandas |
| Transformation | pandas, numpy |
| Scheduling | GitHub Actions |
| Dashboard | Streamlit, Plotly |
| Hosting | Streamlit Community Cloud |
| Version control | GitHub |

---

## Project Structure

```
ltrn-stock-analyzer/
├── .github/
│   └── workflows/
│       └── update_data.yml       # GitHub Actions daily pipeline
├── data/
│   ├── raw/
│   │   ├── ltrn_prices_raw.csv   # Raw OHLCV from yfinance
│   │   └── ltrn_fundamentals_raw.csv
│   └── processed/
│       └── ltrn_indicators.csv   # Transformed data with all indicators
├── ingestion/
│   └── fetch_ltrn.py             # Pulls price history and fundamentals
├── transformation/
│   └── transform_ltrn.py         # Calculates all technical indicators
├── app/
│   └── dashboard.py              # Streamlit application
├── requirements.txt
└── README.md
```

---

## Calculated Indicators

| Indicator | Description |
|---|---|
| `ma_20` | 20-day simple moving average |
| `ma_50` | 50-day simple moving average |
| `rsi_14` | 14-day Relative Strength Index |
| `bb_upper` | Bollinger Band upper (20-day, 2 std dev) |
| `bb_lower` | Bollinger Band lower (20-day, 2 std dev) |
| `bb_mid` | Bollinger Band midline |
| `pct_return` | Daily percentage return |
| `cumulative_return` | Cumulative return from start of dataset |
| `indexed_price` | Price indexed to 100 from start of dataset |
| `volume_zscore` | Volume z-score relative to 30-day rolling mean |
| `volume_spike` | Boolean flag: volume z-score > 2.0 |
| `drawdown_pct` | Percentage drawdown from rolling peak |
| `volatility_30d` | 30-day rolling standard deviation of daily returns |

---

## Running Locally

**Prerequisites:** Python 3.9+

```bash
# Clone the repository
git clone https://github.com/averma-ltrn/ltrn-stock-analyzer.git
cd ltrn-stock-analyzer

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the data pipeline
python3 ingestion/fetch_ltrn.py
python3 transformation/transform_ltrn.py

# Launch the dashboard
streamlit run app/dashboard.py
```

---

## Automated Pipeline

The GitHub Actions workflow (`.github/workflows/update_data.yml`) runs Monday through Friday at 6pm ET — approximately 30 minutes after US market close. Each run:

1. Checks out the repository
2. Installs Python dependencies
3. Runs `fetch_ltrn.py` to pull the latest price and fundamental data
4. Runs `transform_ltrn.py` to recalculate all indicators
5. Commits the updated data files back to `main` with a timestamped commit message

The workflow can also be triggered manually from the GitHub Actions tab at any time.

---

## Data Source

All market data is sourced from Yahoo Finance via the `yfinance` library. Fundamentals are snapshotted at time of each pipeline run. This project is intended for internal analysis and informational purposes only — not for investment advice.

---

## Background

Built as an internal equity monitoring tool for Lantern Pharma's executive team. The pipeline architecture mirrors production data engineering workflows used at financial data vendors and asset managers: a scheduled ingestion layer, a structured transformation layer, and a visualization layer served through a hosted application.

---

*Lantern Pharma Inc. (NASDAQ: LTRN) is an AI-driven clinical-stage precision oncology company. This dashboard is an independent analytics tool and is not affiliated with or endorsed by Lantern Pharma.*