import pandas as pd
import numpy as np
import os

# ── Config ───────────────────────────────────────────────
RAW_DIR = "data/raw"
PROCESSED_DIR = "data/processed"

# ── Helpers ──────────────────────────────────────────────
def ensure_dirs():
    os.makedirs(PROCESSED_DIR, exist_ok=True)

def load_raw_prices():
    path = os.path.join(RAW_DIR, "ltrn_prices_raw.csv")
    df = pd.read_csv(path, index_col="date", parse_dates=True)
    df = df.sort_index()
    print(f"  ✓ Loaded {len(df)} rows from {path}")
    return df

# ── Technical Indicators ─────────────────────────────────

def calc_moving_averages(df):
    df["ma_20"] = df["close"].rolling(window=20).mean().round(4)
    df["ma_50"] = df["close"].rolling(window=50).mean().round(4)
    print("  ✓ Moving averages calculated (20-day, 50-day)")
    return df

def calc_rsi(df, period=14):
    delta = df["close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()

    rs = avg_gain / avg_loss
    df["rsi_14"] = (100 - (100 / (1 + rs))).round(2)
    print("  ✓ RSI calculated (14-day)")
    return df

def calc_bollinger_bands(df, period=20):
    rolling_mean = df["close"].rolling(window=period).mean()
    rolling_std = df["close"].rolling(window=period).std()

    df["bb_upper"] = (rolling_mean + (2 * rolling_std)).round(4)
    df["bb_lower"] = (rolling_mean - (2 * rolling_std)).round(4)
    df["bb_mid"] = rolling_mean.round(4)
    print("  ✓ Bollinger Bands calculated (20-day, 2 std)")
    return df

def calc_returns(df):
    # Daily % return
    df["pct_return"] = (df["close"].pct_change() * 100).round(4)

    # Cumulative % return from start
    df["cumulative_return"] = ((df["close"] / df["close"].iloc[0] - 1) * 100).round(4)

    # Indexed to 100 from start (for peer comparison later)
    df["indexed_price"] = ((df["close"] / df["close"].iloc[0]) * 100).round(4)

    print("  ✓ Returns calculated (daily, cumulative, indexed)")
    return df

def calc_volume_zscore(df, window=30):
    rolling_mean = df["volume"].rolling(window=window).mean()
    rolling_std = df["volume"].rolling(window=window).std()

    df["volume_zscore"] = ((df["volume"] - rolling_mean) / rolling_std).round(4)
    df["volume_spike"] = df["volume_zscore"] > 2.0
    print("  ✓ Volume z-score calculated (30-day window)")
    print(f"    → {df['volume_spike'].sum()} volume spike days detected")
    return df

def calc_drawdown(df):
    rolling_max = df["close"].cummax()
    df["drawdown_pct"] = ((df["close"] - rolling_max) / rolling_max * 100).round(4)
    print(f"  ✓ Drawdown calculated")
    print(f"    → Max drawdown: {df['drawdown_pct'].min():.2f}%")
    return df

def calc_volatility(df, window=30):
    df["volatility_30d"] = (df["pct_return"].rolling(window=window).std()).round(4)
    print("  ✓ Rolling 30-day volatility calculated")
    return df

# ── Summary Stats ────────────────────────────────────────
def print_summary(df):
    print()
    print("  ── Summary ──────────────────────────────")
    print(f"  Date range:        {df.index.min().date()} → {df.index.max().date()}")
    print(f"  Current close:     ${df['close'].iloc[-1]:.4f}")
    print(f"  52w high:          ${df['close'].tail(252).max():.4f}")
    print(f"  52w low:           ${df['close'].tail(252).min():.4f}")
    print(f"  Cumulative return: {df['cumulative_return'].iloc[-1]:.2f}%")
    print(f"  Current RSI:       {df['rsi_14'].iloc[-1]:.2f}")
    print(f"  Current MA20:      ${df['ma_20'].iloc[-1]:.4f}")
    print(f"  Current MA50:      ${df['ma_50'].iloc[-1]:.4f}")
    print(f"  Max drawdown:      {df['drawdown_pct'].min():.2f}%")
    print("  ─────────────────────────────────────────")

# ── Main ─────────────────────────────────────────────────
def main():
    print("=" * 50)
    print("  LTRN Transformation Pipeline")
    print("=" * 50)

    ensure_dirs()

    print("\n[1] Loading raw data...")
    df = load_raw_prices()

    print("\n[2] Calculating indicators...")
    df = calc_moving_averages(df)
    df = calc_rsi(df)
    df = calc_bollinger_bands(df)
    df = calc_returns(df)
    df = calc_volume_zscore(df)
    df = calc_drawdown(df)
    df = calc_volatility(df)

    print_summary(df)

    print("\n[3] Saving processed data...")
    output_path = os.path.join(PROCESSED_DIR, "ltrn_indicators.csv")
    df.to_csv(output_path)
    print(f"  ✓ Saved to {output_path}")
    print(f"  ✓ {len(df.columns)} columns, {len(df)} rows")

    print()
    print("=" * 50)
    print("  Transformation complete.")
    print("=" * 50)

if __name__ == "__main__":
    main()