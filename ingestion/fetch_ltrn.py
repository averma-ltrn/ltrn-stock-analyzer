import yfinance as yf
import pandas as pd
from datetime import datetime
import os
import json

# ── Config ──────────────────────────────────────────────
TICKER = "LTRN"
PERIOD = "2y"  # 2 years of daily history
RAW_DIR = "data/raw"

# ── Helpers ─────────────────────────────────────────────
def ensure_dirs():
    os.makedirs(RAW_DIR, exist_ok=True)

def timestamp():
    return datetime.now().strftime("%Y-%m-%d")

# ── Fetch price + volume history ─────────────────────────
def fetch_price_history():
    print(f"[{timestamp()}] Fetching price history for {TICKER}...")
    ticker = yf.Ticker(TICKER)
    df = ticker.history(period=PERIOD)

    if df.empty:
        print("  ERROR: No price data returned. Check ticker symbol.")
        return None

    # Clean up index
    df.index = pd.to_datetime(df.index).tz_localize(None)
    df.index.name = "date"

    # Keep only the columns we need
    df = df[["Open", "High", "Low", "Close", "Volume"]].copy()
    df.columns = ["open", "high", "low", "close", "volume"]

    # Add ticker column
    df.insert(0, "ticker", TICKER)

    print(f"  ✓ {len(df)} trading days retrieved")
    print(f"  ✓ Date range: {df.index.min().date()} → {df.index.max().date()}")

    return df

# ── Fetch fundamentals snapshot ──────────────────────────
def fetch_fundamentals():
    print(f"[{timestamp()}] Fetching fundamentals for {TICKER}...")
    ticker = yf.Ticker(TICKER)
    info = ticker.info

    fundamentals = {
        "ticker": TICKER,
        "fetched_at": timestamp(),
        "current_price": info.get("currentPrice"),
        "market_cap": info.get("marketCap"),
        "shares_outstanding": info.get("sharesOutstanding"),
        "eps_ttm": info.get("trailingEps"),
        "cash": info.get("totalCash"),
        "total_debt": info.get("totalDebt"),
        "revenue": info.get("totalRevenue"),
        "52w_high": info.get("fiftyTwoWeekHigh"),
        "52w_low": info.get("fiftyTwoWeekLow"),
        "avg_volume_30d": info.get("averageVolume30Day"),
        "beta": info.get("beta"),
        "sector": info.get("sector"),
        "industry": info.get("industry"),
    }

    df = pd.DataFrame([fundamentals])
    print(f"  ✓ Fundamentals snapshot captured")
    print(f"  ✓ Current price: ${fundamentals.get('current_price')}")
    print(f"  ✓ Market cap: ${fundamentals.get('market_cap'):,}" if fundamentals.get("market_cap") else "  ✓ Market cap: N/A")

    return df, yf.Ticker(TICKER)

# ── Fetch holder data ─────────────────────────────────────
def fetch_holders(ticker_obj):
    print(f"[{timestamp()}] Fetching holder data for {TICKER}...")

    institutional_holders = []
    mutualfund_holders    = []

    def parse_holders_df(df):
        rows = []
        if df is None or df.empty:
            return rows
        for _, row in df.iterrows():
            rows.append({
                "organization": str(row.get("Holder", row.iloc[0])).strip(),
                "shares":       int(row.get("Shares", 0)) if pd.notna(row.get("Shares", None)) else None,
                "date_reported": str(row.get("Date Reported", ""))[:10] if pd.notna(row.get("Date Reported", None)) else None,
                "pct_held":     float(row.get("pctHeld", row.get("% Out", 0))) if pd.notna(row.get("pctHeld", row.get("% Out", None))) else None,
                "value":        int(row.get("Value", 0)) if pd.notna(row.get("Value", None)) else None,
            })
        return rows

    try:
        ih = ticker_obj.institutional_holders
        institutional_holders = parse_holders_df(ih)
        print(f"  ✓ Institutional holders: {len(institutional_holders)} rows")
    except Exception as e:
        print(f"  ⚠ Institutional holders fetch failed: {e}")

    try:
        mf = ticker_obj.mutualfund_holders
        mutualfund_holders = parse_holders_df(mf)
        print(f"  ✓ Mutual fund holders: {len(mutualfund_holders)} rows")
    except Exception as e:
        print(f"  ⚠ Mutual fund holders fetch failed: {e}")

    return institutional_holders, mutualfund_holders

# ── Write market snapshot JSON for CFO Assistant ─────────
def write_market_snapshot(prices_df, fundamentals_df, institutional_holders, mutualfund_holders):
    print(f"[{timestamp()}] Writing market snapshot JSON...")

    info = fundamentals_df.iloc[0].to_dict()

    # Pull prev close and today's volume from the last two rows of price history
    price      = info.get("current_price")
    prev_close = None
    volume     = None
    change     = None
    change_pct = None

    if prices_df is not None and len(prices_df) >= 2:
        prev_close = float(prices_df["close"].iloc[-2])
        volume     = int(prices_df["volume"].iloc[-1])
        if price is not None and prev_close is not None:
            change     = round(price - prev_close, 4)
            change_pct = round((change / prev_close) * 100, 4)

    snapshot = {
        "ticker":              TICKER,
        "fetched_at":          datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "price":               price,
        "previous_close":      prev_close,
        "change":              change,
        "change_pct":          change_pct,
        "volume":              volume,
        "market_cap":          info.get("market_cap"),
        "fifty_two_week_high": info.get("52w_high"),
        "fifty_two_week_low":  info.get("52w_low"),
        "shares_outstanding":  info.get("shares_outstanding"),
        "avg_volume_30d":      info.get("avg_volume_30d"),
        "currency":            "USD",
        "institutional_holders": institutional_holders,
        "mutualfund_holders":    mutualfund_holders,
    }

    path = os.path.join(RAW_DIR, "ltrn_market_snapshot.json")
    with open(path, "w") as f:
        json.dump(snapshot, f, indent=2, default=str)

    print(f"  ✓ Saved to {path}")
    return snapshot

# ── Save to CSV ──────────────────────────────────────────
def save(df, filename):
    path = os.path.join(RAW_DIR, filename)
    df.to_csv(path)
    print(f"  ✓ Saved to {path}")

# ── Main ─────────────────────────────────────────────────
def main():
    print("=" * 50)
    print("  LTRN Data Ingestion Pipeline")
    print("=" * 50)

    ensure_dirs()

    # Price history
    prices = fetch_price_history()
    if prices is not None:
        save(prices, "ltrn_prices_raw.csv")

    print()

    # Fundamentals — also returns the ticker object so we reuse it for holders
    fundamentals, ticker_obj = fetch_fundamentals()
    if fundamentals is not None:
        save(fundamentals, "ltrn_fundamentals_raw.csv")

    print()

    # Holder data
    institutional_holders, mutualfund_holders = fetch_holders(ticker_obj)

    print()

    # Market snapshot JSON — for CFO Assistant equity tab
    if prices is not None and fundamentals is not None:
        write_market_snapshot(prices, fundamentals, institutional_holders, mutualfund_holders)

    print()
    print("=" * 50)
    print("  Ingestion complete.")
    print("=" * 50)

if __name__ == "__main__":
    main()