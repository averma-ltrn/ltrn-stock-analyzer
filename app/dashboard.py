import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
import os

# ── Page Config ──────────────────────────────────────────
st.set_page_config(
    page_title="LTRN Equity Analytics",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Corporate Styling ─────────────────────────────────────
st.markdown("""
    <style>
        /* Base */
        html, body, [class*="css"] {
            font-family: 'Inter', 'Segoe UI', sans-serif;
        }
        .main { background-color: #0a0c10; }
        .block-container { padding-top: 2rem; padding-bottom: 2rem; }

        /* Sidebar */
        section[data-testid="stSidebar"] {
            background-color: #0f1117;
            border-right: 1px solid #1e2130;
        }

        /* Header */
        h1 {
            color: #ffffff !important;
            font-size: 1.6rem !important;
            font-weight: 600 !important;
            letter-spacing: -0.3px;
        }
        h2, h3, h4 {
            color: #e0e0e0 !important;
            font-weight: 500 !important;
        }

        /* KPI Cards */
        div[data-testid="metric-container"] {
            background-color: #0f1117;
            border: 1px solid #1e2130;
            border-radius: 4px;
            padding: 18px 20px;
        }
        div[data-testid="metric-container"] label {
            color: #6b7280 !important;
            font-size: 11px !important;
            font-weight: 500 !important;
            letter-spacing: 0.8px;
            text-transform: uppercase;
        }
        div[data-testid="metric-container"] [data-testid="metric-value"] {
            color: #ffffff !important;
            font-size: 1.5rem !important;
            font-weight: 600 !important;
        }
        div[data-testid="metric-container"] [data-testid="metric-delta"] {
            font-size: 12px !important;
        }

        /* Tabs */
        button[data-baseweb="tab"] {
            font-size: 12px !important;
            font-weight: 500 !important;
            letter-spacing: 0.5px;
            text-transform: uppercase;
            color: #6b7280 !important;
            border-bottom: 2px solid transparent;
            padding: 10px 20px !important;
        }
        button[data-baseweb="tab"][aria-selected="true"] {
            color: #ffffff !important;
            border-bottom: 2px solid #c84b0a !important;
        }

        /* Dividers */
        hr { border-color: #1e2130 !important; margin: 1.2rem 0; }

        /* Dataframe */
        .stDataFrame { border: 1px solid #1e2130; border-radius: 4px; }

        /* Input fields */
        .stTextInput input {
            background-color: #0f1117 !important;
            border: 1px solid #1e2130 !important;
            color: #ffffff !important;
            border-radius: 4px;
            font-size: 13px;
        }
        .stSelectbox select {
            background-color: #0f1117 !important;
            border: 1px solid #1e2130 !important;
            color: #ffffff !important;
        }

        /* Warnings */
        .stWarning { border-left: 3px solid #c84b0a; }

        /* Caption */
        .stCaption { color: #4b5563 !important; font-size: 11px !important; }
    </style>
""", unsafe_allow_html=True)

# ── Chart theme ───────────────────────────────────────────
CHART_THEME = dict(
    template="plotly_dark",
    paper_bgcolor="#0a0c10",
    plot_bgcolor="#0a0c10",
    font=dict(family="Inter, Segoe UI, sans-serif", color="#9ca3af", size=11),
)

LTRN_COLOR   = "#c84b0a"
COMP1_COLOR  = "#3b82f6"
COMP2_COLOR  = "#10b981"
DOWN_COLOR   = "#ef4444"
UP_COLOR     = "#22c55e"
NEUTRAL_COLOR = "#6b7280"

# ── Data loaders ──────────────────────────────────────────
@st.cache_data(ttl=3600)
def load_indicators():
    path = os.path.join("data", "processed", "ltrn_indicators.csv")
    df = pd.read_csv(path, index_col="date", parse_dates=True)
    return df.sort_index()

@st.cache_data(ttl=3600)
def load_fundamentals():
    path = os.path.join("data", "raw", "ltrn_fundamentals_raw.csv")
    return pd.read_csv(path)

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_comparison_ticker(ticker):
    try:
        t = yf.Ticker(ticker)
        df = t.history(period="2y")
        if df.empty:
            return None, None
        df.index = pd.to_datetime(df.index).tz_localize(None)
        df.index.name = "date"
        df = df[["Close", "Volume"]].copy()
        df.columns = ["close", "volume"]
        info = t.info
        name = info.get("longName", ticker)
        return df, name
    except:
        return None, None

# ── Formatting helpers ────────────────────────────────────
def fmt_millions(val):
    try:
        v = float(val)
        if v >= 1e9:
            return f"${v/1e9:.2f}B"
        return f"${v/1e6:.1f}M"
    except:
        return "N/A"

def fmt_currency(val):
    try:
        return f"${float(val):.2f}"
    except:
        return "N/A"

# ── Sidebar ───────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
        <div style='padding: 8px 0 16px 0;'>
            <div style='font-size: 11px; color: #6b7280; letter-spacing: 1px; text-transform: uppercase; font-weight: 500;'>Stock Price Analytics</div>
            <div style='font-size: 18px; color: #ffffff; font-weight: 600; margin-top: 4px;'>Lantern Pharma</div>
            <div style='font-size: 12px; color: #6b7280; margin-top: 2px;'>NASDAQ: LTRN</div>
        </div>
    """, unsafe_allow_html=True)
    st.markdown("---")

    st.markdown("<div style='font-size:11px;color:#6b7280;letter-spacing:0.8px;text-transform:uppercase;font-weight:500;margin-bottom:8px;'>Display Settings</div>", unsafe_allow_html=True)

    timeframe = st.selectbox(
        "Timeframe",
        ["1 Month", "3 Months", "6 Months", "1 Year", "2 Years"],
        index=3,
        label_visibility="collapsed"
    )
    st.markdown("<div style='font-size:11px;color:#6b7280;margin-bottom:12px;'>Selected period</div>", unsafe_allow_html=True)

    show_ma = st.checkbox("Moving Averages (MA20 / MA50)", value=True)
    show_bb = st.checkbox("Bollinger Bands", value=False)
    show_volume = st.checkbox("Volume Panel", value=True)

    st.markdown("---")
    st.markdown("""
        <div style='font-size:11px;color:#4b5563;line-height:1.6;'>
            Data source: Yahoo Finance<br>
            Refreshed daily via automated pipeline<br>
        </div>
    """, unsafe_allow_html=True)

# ── Load data ─────────────────────────────────────────────
try:
    df = load_indicators()
    fundamentals = load_fundamentals()
except FileNotFoundError:
    st.error("Data files not found. Run the ingestion and transformation scripts first.")
    st.stop()

timeframe_map = {
    "1 Month": 21, "3 Months": 63, "6 Months": 126,
    "1 Year": 252, "2 Years": 504
}
days = timeframe_map[timeframe]
df_filtered = df.tail(days).copy()

# ── Header ────────────────────────────────────────────────
col_title, col_date = st.columns([3, 1])
with col_title:
    st.markdown("""
        <h1 style='margin-bottom:2px;'>Lantern Pharma &nbsp;·&nbsp; NASDAQ: LTRN</h1>
    """, unsafe_allow_html=True)
with col_date:
    st.markdown(f"""
        <div style='text-align:right;padding-top:12px;font-size:11px;color:#6b7280;letter-spacing:0.5px;'>
            Data through {df.index.max().strftime('%B %d, %Y')}
        </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ── KPI Cards ─────────────────────────────────────────────
current_price   = df["close"].iloc[-1]
prev_price      = df["close"].iloc[-2]
price_change_pct = ((current_price - prev_price) / prev_price) * 100
high_52w        = df["close"].tail(252).max()
low_52w         = df["close"].tail(252).min()
pct_from_high   = ((current_price - high_52w) / high_52w) * 100
current_rsi     = df["rsi_14"].iloc[-1]
max_drawdown    = df["drawdown_pct"].min()
period_return   = df_filtered["cumulative_return"].iloc[-1] - df_filtered["cumulative_return"].iloc[0]

if current_rsi >= 70:
    rsi_label = "Overbought"
elif current_rsi <= 30:
    rsi_label = "Oversold"
else:
    rsi_label = "Neutral"

c1, c2, c3, c4, c5, c6 = st.columns(6)
with c1:
    st.metric("Last Close", f"${current_price:.2f}", f"{price_change_pct:+.2f}% today")
with c2:
    st.metric("52-Week High", f"${high_52w:.2f}", f"{pct_from_high:.1f}% from high")
with c3:
    st.metric("52-Week Low", f"${low_52w:.2f}")
with c4:
    st.metric("RSI (14-Day)", f"{current_rsi:.1f}", rsi_label)
with c5:
    st.metric("Max Drawdown", f"{max_drawdown:.1f}%")
with c6:
    st.metric(f"Period Return", f"{period_return:+.1f}%", timeframe)

st.markdown("---")

# ── Tabs ──────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Price & Volume",
    "Technical Indicators",
    "Volatility & Drawdown",
    "Fundamentals",
    "Comparisons"
])

# ════════════════════════════════════════════════════════════
# TAB 1 — Price & Volume
# ════════════════════════════════════════════════════════════
with tab1:
    rows = 2 if show_volume else 1
    row_heights = [0.72, 0.28] if show_volume else [1.0]

    fig = make_subplots(
        rows=rows, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.04,
        row_heights=row_heights
    )

    fig.add_trace(go.Scatter(
        x=df_filtered.index, y=df_filtered["close"],
        name="Close", line=dict(color=LTRN_COLOR, width=1.8),
        hovertemplate="<b>%{x|%b %d, %Y}</b><br>Close: $%{y:.2f}<extra></extra>"
    ), row=1, col=1)

    if show_ma:
        fig.add_trace(go.Scatter(
            x=df_filtered.index, y=df_filtered["ma_20"],
            name="MA 20", line=dict(color=COMP1_COLOR, width=1.2, dash="dot"),
            hovertemplate="MA20: $%{y:.2f}<extra></extra>"
        ), row=1, col=1)
        fig.add_trace(go.Scatter(
            x=df_filtered.index, y=df_filtered["ma_50"],
            name="MA 50", line=dict(color=COMP2_COLOR, width=1.2, dash="dot"),
            hovertemplate="MA50: $%{y:.2f}<extra></extra>"
        ), row=1, col=1)

    if show_bb:
        fig.add_trace(go.Scatter(
            x=df_filtered.index, y=df_filtered["bb_upper"],
            name="BB Upper", line=dict(color=NEUTRAL_COLOR, width=1, dash="dash"),
            hovertemplate="BB Upper: $%{y:.2f}<extra></extra>"
        ), row=1, col=1)
        fig.add_trace(go.Scatter(
            x=df_filtered.index, y=df_filtered["bb_lower"],
            name="BB Lower", line=dict(color=NEUTRAL_COLOR, width=1, dash="dash"),
            fill="tonexty", fillcolor="rgba(107,114,128,0.06)",
            hovertemplate="BB Lower: $%{y:.2f}<extra></extra>"
        ), row=1, col=1)

    if show_volume:
        bar_colors = [DOWN_COLOR if r < 0 else UP_COLOR for r in df_filtered["pct_return"]]
        fig.add_trace(go.Bar(
            x=df_filtered.index, y=df_filtered["volume"],
            name="Volume", marker_color=bar_colors, opacity=0.6,
            hovertemplate="<b>%{x|%b %d, %Y}</b><br>Volume: %{y:,.0f}<extra></extra>"
        ), row=2, col=1)

    fig.update_layout(
        **CHART_THEME,
        height=520,
        margin=dict(l=0, r=0, t=10, b=0),
        legend=dict(
            orientation="h", yanchor="bottom", y=1.01,
            xanchor="right", x=1,
            bgcolor="rgba(0,0,0,0)", font=dict(size=11, color="#9ca3af")
        ),
        hovermode="x unified"
    )
    fig.update_yaxes(title_text="Price (USD)", row=1, col=1, gridcolor="#1a1d27")
    fig.update_yaxes(title_text="Volume", row=2, col=1, gridcolor="#1a1d27")
    fig.update_xaxes(gridcolor="#1a1d27", showgrid=True)
    st.plotly_chart(fig, use_container_width=True)

    # Volume spike table
    spikes = df_filtered[df_filtered["volume_spike"] == True][
        ["close", "volume", "pct_return", "volume_zscore"]
    ].copy()
    spikes.columns = ["Close", "Volume", "Daily Return (%)", "Volume Z-Score"]
    spikes["Close"] = spikes["Close"].map("${:.2f}".format)
    spikes["Volume"] = spikes["Volume"].map("{:,.0f}".format)
    spikes["Daily Return (%)"] = spikes["Daily Return (%)"].map("{:+.2f}%".format)
    spikes["Volume Z-Score"] = spikes["Volume Z-Score"].map("{:.2f}".format)

    if not spikes.empty:
        st.markdown("---")
        st.markdown(f"**Elevated Volume Days** — {len(spikes)} sessions with volume exceeding 2 standard deviations above the 30-day average")
        st.dataframe(spikes, use_container_width=True)

# ════════════════════════════════════════════════════════════
# TAB 2 — Technical Indicators
# ════════════════════════════════════════════════════════════
with tab2:
    fig2 = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.1,
        subplot_titles=("Relative Strength Index — RSI (14-Day)", "Bollinger Bands (20-Day, 2 Std Dev)")
    )

    fig2.add_trace(go.Scatter(
        x=df_filtered.index, y=df_filtered["rsi_14"],
        name="RSI", line=dict(color=LTRN_COLOR, width=1.8),
        hovertemplate="RSI: %{y:.2f}<extra></extra>"
    ), row=1, col=1)
    fig2.add_hline(y=70, line_dash="dash", line_color=DOWN_COLOR, opacity=0.6,
                   annotation_text="Overbought  70", annotation_font_size=10, row=1, col=1)
    fig2.add_hline(y=30, line_dash="dash", line_color=UP_COLOR, opacity=0.6,
                   annotation_text="Oversold  30", annotation_font_size=10, row=1, col=1)
    fig2.add_hrect(y0=30, y1=70, fillcolor="rgba(255,255,255,0.02)", row=1, col=1)

    fig2.add_trace(go.Scatter(
        x=df_filtered.index, y=df_filtered["close"],
        name="Close", line=dict(color=LTRN_COLOR, width=1.8),
        hovertemplate="Close: $%{y:.2f}<extra></extra>"
    ), row=2, col=1)
    fig2.add_trace(go.Scatter(
        x=df_filtered.index, y=df_filtered["bb_upper"],
        name="Upper Band", line=dict(color=COMP1_COLOR, width=1, dash="dash"),
        hovertemplate="Upper: $%{y:.2f}<extra></extra>"
    ), row=2, col=1)
    fig2.add_trace(go.Scatter(
        x=df_filtered.index, y=df_filtered["bb_lower"],
        name="Lower Band", line=dict(color=COMP1_COLOR, width=1, dash="dash"),
        fill="tonexty", fillcolor="rgba(59,130,246,0.05)",
        hovertemplate="Lower: $%{y:.2f}<extra></extra>"
    ), row=2, col=1)

    fig2.update_layout(
        **CHART_THEME,
        height=520,
        margin=dict(l=0, r=0, t=30, b=0),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="right", x=1,
                    bgcolor="rgba(0,0,0,0)", font=dict(size=11, color="#9ca3af"))
    )
    fig2.update_yaxes(gridcolor="#1a1d27")
    fig2.update_xaxes(gridcolor="#1a1d27")
    st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")
    st.markdown("**RSI Reading**")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Current RSI", f"{current_rsi:.2f}")
    with c2:
        st.metric("Signal", rsi_label)
    with c3:
        st.metric("RSI Range (Period)", f"{df_filtered['rsi_14'].min():.1f} – {df_filtered['rsi_14'].max():.1f}")

# ════════════════════════════════════════════════════════════
# TAB 3 — Volatility & Drawdown
# ════════════════════════════════════════════════════════════
with tab3:
    c1, c2 = st.columns(2)

    with c1:
        fig3a = go.Figure()
        fig3a.add_trace(go.Scatter(
            x=df_filtered.index, y=df_filtered["drawdown_pct"],
            fill="tozeroy", fillcolor="rgba(239,68,68,0.12)",
            line=dict(color=DOWN_COLOR, width=1.5), name="Drawdown",
            hovertemplate="<b>%{x|%b %d, %Y}</b><br>Drawdown: %{y:.2f}%<extra></extra>"
        ))
        fig3a.update_layout(
            **CHART_THEME,
            title=dict(text="Drawdown from Rolling Peak (%)", font=dict(size=12, color="#9ca3af")),
            height=340, margin=dict(l=0, r=0, t=40, b=0)
        )
        st.plotly_chart(fig3a, use_container_width=True)

    with c2:
        fig3b = go.Figure()
        fig3b.add_trace(go.Scatter(
            x=df_filtered.index, y=df_filtered["volatility_30d"],
            fill="tozeroy", fillcolor="rgba(200,75,10,0.1)",
            line=dict(color=LTRN_COLOR, width=1.5), name="30D Volatility",
            hovertemplate="<b>%{x|%b %d, %Y}</b><br>Volatility: %{y:.2f}%<extra></extra>"
        ))
        fig3b.update_layout(
            **CHART_THEME,
            title=dict(text="30-Day Rolling Volatility (%)", font=dict(size=12, color="#9ca3af")),
            height=340, margin=dict(l=0, r=0, t=40, b=0)
        )
        st.plotly_chart(fig3b, use_container_width=True)

    fig3c = go.Figure()
    fig3c.add_trace(go.Histogram(
        x=df_filtered["pct_return"].dropna(), nbinsx=50,
        marker_color=LTRN_COLOR, opacity=0.7, name="Daily Returns"
    ))
    fig3c.add_vline(x=0, line_dash="dash", line_color="#6b7280", opacity=0.6)
    fig3c.update_layout(
        **CHART_THEME,
        title=dict(text="Distribution of Daily Returns (%)", font=dict(size=12, color="#9ca3af")),
        height=300, margin=dict(l=0, r=0, t=40, b=0),
        xaxis=dict(title="Daily Return (%)", gridcolor="#1a1d27"),
        yaxis=dict(title="Frequency", gridcolor="#1a1d27")
    )
    st.plotly_chart(fig3c, use_container_width=True)

    st.markdown("---")
    st.markdown("**Risk Summary**")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Max Drawdown", f"{df_filtered['drawdown_pct'].min():.2f}%")
    with c2:
        st.metric("Avg Daily Return", f"{df_filtered['pct_return'].mean():.2f}%")
    with c3:
        st.metric("Best Single Day", f"{df_filtered['pct_return'].max():+.2f}%")
    with c4:
        st.metric("Worst Single Day", f"{df_filtered['pct_return'].min():+.2f}%")

# ════════════════════════════════════════════════════════════
# TAB 4 — Fundamentals
# ════════════════════════════════════════════════════════════
with tab4:
    f = fundamentals.iloc[0]

    st.markdown("**Balance Sheet**")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Market Cap", fmt_millions(f.get("market_cap")))
    with c2:
        st.metric("Cash & Equivalents", fmt_millions(f.get("cash")))
    with c3:
        st.metric("Total Debt", fmt_millions(f.get("total_debt")))
    with c4:
        st.metric("EPS (TTM)", fmt_currency(f.get("eps_ttm")))

    st.markdown("---")
    st.markdown("**Market Data**")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("52-Week High", fmt_currency(f.get("52w_high")))
    with c2:
        st.metric("52-Week Low", fmt_currency(f.get("52w_low")))
    with c3:
        shares = f.get("shares_outstanding")
        st.metric("Shares Outstanding", f"{float(shares):,.0f}" if shares else "N/A")
    with c4:
        beta = f.get("beta")
        st.metric("Beta", f"{float(beta):.2f}" if beta else "N/A")

    st.markdown("---")
    st.markdown("**Indexed Price Performance**")

    fig4 = go.Figure()
    fig4.add_trace(go.Scatter(
        x=df_filtered.index, y=df_filtered["indexed_price"],
        fill="tozeroy", fillcolor="rgba(200,75,10,0.07)",
        line=dict(color=LTRN_COLOR, width=1.8), name="Indexed Price",
        hovertemplate="<b>%{x|%b %d, %Y}</b><br>Index: %{y:.1f}<extra></extra>"
    ))
    fig4.add_hline(y=100, line_dash="dash", line_color="#374151", opacity=0.8,
                   annotation_text="Base period (100)", annotation_font_size=10)
    fig4.update_layout(
        **CHART_THEME,
        height=340, margin=dict(l=0, r=0, t=10, b=0),
        yaxis=dict(title="Indexed Price", gridcolor="#1a1d27"),
        xaxis=dict(gridcolor="#1a1d27")
    )
    st.plotly_chart(fig4, use_container_width=True)

    st.markdown("---")
    st.caption(f"Fundamentals as of {f.get('fetched_at', 'unknown date')}   ·   Source: Yahoo Finance")

# ════════════════════════════════════════════════════════════
# TAB 5 — Comparisons
# ════════════════════════════════════════════════════════════
with tab5:
    st.markdown("**Comparative Analysis**")
    st.markdown(
        "<div style='font-size:12px;color:#6b7280;margin-bottom:16px;'>"
        "LTRN is fixed as the base. Enter one or two additional tickers to compare. "
        "Leave Ticker 2 blank for a 1v1 comparison."
        "</div>",
        unsafe_allow_html=True
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            "<div style='font-size:11px;color:#6b7280;letter-spacing:0.8px;text-transform:uppercase;"
            "font-weight:500;margin-bottom:6px;'>Base Ticker</div>"
            "<div style='font-size:14px;color:#ffffff;font-weight:600;padding:10px 12px;"
            "background:#0f1117;border:1px solid #1e2130;border-radius:4px;'>"
            "LTRN &nbsp;·&nbsp; Lantern Pharma</div>",
            unsafe_allow_html=True
        )
    with c2:
        ticker2 = st.text_input(
            "Comparison Ticker 1",
            value="PSTV",
            placeholder="e.g. AAPL, MSFT, PSTV"
        ).strip().upper()
    with c3:
        ticker3 = st.text_input(
            "Comparison Ticker 2 (optional)",
            value="",
            placeholder="e.g. RENB, GRCE"
        ).strip().upper()

    comp_timeframe = st.selectbox(
        "Comparison Period",
        ["1 Month", "3 Months", "6 Months", "1 Year", "2 Years"],
        index=3,
        key="comp_timeframe"
    )
    comp_days = timeframe_map[comp_timeframe]

    st.markdown("---")

    # Build dataset
    color_map = {"LTRN": LTRN_COLOR}
    comp_data  = {}
    comp_names = {}

    ltrn_slice = df.tail(comp_days)[["close", "volume"]].copy()
    comp_data["LTRN"]  = ltrn_slice
    comp_names["LTRN"] = "Lantern Pharma (LTRN)"

    if ticker2 and ticker2 != "LTRN":
        with st.spinner(f"Retrieving data for {ticker2}..."):
            df2, name2 = fetch_comparison_ticker(ticker2)
        if df2 is not None:
            comp_data[ticker2]  = df2.tail(comp_days)
            comp_names[ticker2] = f"{name2} ({ticker2})" if name2 else ticker2
            color_map[ticker2]  = COMP1_COLOR
        else:
            st.warning(f"No data returned for {ticker2}. Verify the ticker symbol.")

    if ticker3 and ticker3 not in ["LTRN", ticker2]:
        with st.spinner(f"Retrieving data for {ticker3}..."):
            df3, name3 = fetch_comparison_ticker(ticker3)
        if df3 is not None:
            comp_data[ticker3]  = df3.tail(comp_days)
            comp_names[ticker3] = f"{name3} ({ticker3})" if name3 else ticker3
            color_map[ticker3]  = COMP2_COLOR
        else:
            st.warning(f"No data returned for {ticker3}. Verify the ticker symbol.")

    # Indexed price chart
    st.markdown("**Indexed Price Performance — Base 100**")
    st.caption("All series indexed to 100 at the start of the selected period. Reflects percentage return regardless of absolute share price.")

    fig5a = go.Figure()
    for ticker, data in comp_data.items():
        if data is None or data.empty:
            continue
        indexed = (data["close"] / data["close"].iloc[0]) * 100
        fig5a.add_trace(go.Scatter(
            x=indexed.index, y=indexed.values,
            name=comp_names[ticker],
            line=dict(color=color_map.get(ticker, NEUTRAL_COLOR), width=2),
            hovertemplate=f"<b>{comp_names[ticker]}</b><br>%{{x|%b %d, %Y}}<br>Index: %{{y:.1f}}<extra></extra>"
        ))

    fig5a.add_hline(y=100, line_dash="dash", line_color="#374151", opacity=0.8,
                    annotation_text="Base (100)", annotation_font_size=10)
    fig5a.update_layout(
        **CHART_THEME,
        height=420, margin=dict(l=0, r=0, t=10, b=0),
        legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="left", x=0,
                    bgcolor="rgba(0,0,0,0)", font=dict(size=11, color="#9ca3af")),
        hovermode="x unified",
        yaxis=dict(title="Indexed Price", gridcolor="#1a1d27"),
        xaxis=dict(gridcolor="#1a1d27")
    )
    st.plotly_chart(fig5a, use_container_width=True)

    # Volume panel
    st.markdown("**Volume by Security**")
    n = len(comp_data)
    fig5b = make_subplots(
        rows=n, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.06,
        subplot_titles=[comp_names[t] for t in comp_data.keys()]
    )
    for i, (ticker, data) in enumerate(comp_data.items()):
        if data is None or data.empty:
            continue
        fig5b.add_trace(go.Bar(
            x=data.index, y=data["volume"],
            name=comp_names[ticker],
            marker_color=color_map.get(ticker, NEUTRAL_COLOR),
            opacity=0.65,
            hovertemplate=f"{ticker}  %{{x|%b %d, %Y}}<br>Volume: %{{y:,.0f}}<extra></extra>"
        ), row=i+1, col=1)

    fig5b.update_layout(
        **CHART_THEME,
        height=max(260, 130 * n),
        margin=dict(l=0, r=0, t=30, b=0),
        showlegend=False
    )
    fig5b.update_yaxes(gridcolor="#1a1d27")
    fig5b.update_xaxes(gridcolor="#1a1d27")
    st.plotly_chart(fig5b, use_container_width=True)

    # Fundamentals table
    st.markdown("**Fundamentals**")
    fund_rows = []
    for ticker in comp_data.keys():
        try:
            info = yf.Ticker(ticker).info
            fund_rows.append({
                "Ticker": ticker,
                "Company": info.get("longName", ticker),
                "Price": fmt_currency(info.get("currentPrice")),
                "Market Cap": fmt_millions(info.get("marketCap")),
                "Cash": fmt_millions(info.get("totalCash")),
                "EPS (TTM)": fmt_currency(info.get("trailingEps")),
                "52W High": fmt_currency(info.get("fiftyTwoWeekHigh")),
                "52W Low": fmt_currency(info.get("fiftyTwoWeekLow")),
                "Beta": f"{round(float(info.get('beta', 0)), 2)}" if info.get("beta") else "N/A",
            })
        except:
            fund_rows.append({"Ticker": ticker, "Company": ticker})

    if fund_rows:
        st.dataframe(pd.DataFrame(fund_rows).set_index("Ticker"), use_container_width=True)

    # Return summary
    st.markdown("---")
    st.markdown("**Return Summary**")
    ret_cols = st.columns(len(comp_data))
    for i, (ticker, data) in enumerate(comp_data.items()):
        if data is None or data.empty:
            continue
        total_ret  = ((data["close"].iloc[-1] / data["close"].iloc[0]) - 1) * 100
        best_day   = data["close"].pct_change().max() * 100
        worst_day  = data["close"].pct_change().min() * 100
        with ret_cols[i]:
            st.markdown(f"<div style='font-size:12px;color:#9ca3af;margin-bottom:8px;'>{comp_names[ticker]}</div>", unsafe_allow_html=True)
            st.metric(f"Return ({comp_timeframe})", f"{total_ret:+.1f}%")
            st.metric("Best Session", f"{best_day:+.2f}%")
            st.metric("Worst Session", f"{worst_day:+.2f}%")