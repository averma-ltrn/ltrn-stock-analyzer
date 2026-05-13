import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
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
        html, body, [class*="css"] {
            font-family: 'Inter', 'Segoe UI', sans-serif;
        }
        .main { background-color: #0E1623; }
        .block-container { padding-top: 2rem; padding-bottom: 2rem; }

        section[data-testid="stSidebar"] {
            background-color: #0b1220;
            border-right: 1px solid #1c2a3e;
        }

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

        div[data-testid="metric-container"] {
            background-color: #111f30;
            border: 1px solid #1c2a3e;
            border-radius: 4px;
            padding: 18px 20px;
        }
        div[data-testid="metric-container"] label {
            color: #6b8aad !important;
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

        button[data-baseweb="tab"] {
            font-size: 12px !important;
            font-weight: 500 !important;
            letter-spacing: 0.5px;
            text-transform: uppercase;
            color: #6b8aad !important;
            border-bottom: 2px solid transparent;
            padding: 10px 20px !important;
        }
        button[data-baseweb="tab"][aria-selected="true"] {
            color: #ffffff !important;
            border-bottom: 2px solid #c84b0a !important;
        }

        hr { border-color: #1c2a3e !important; margin: 1.2rem 0; }
        .stDataFrame { border: 1px solid #1c2a3e; border-radius: 4px; }
        .stCaption { color: #4b6a8a !important; font-size: 11px !important; }
    </style>
""", unsafe_allow_html=True)

# ── Chart theme ───────────────────────────────────────────
CHART_THEME = dict(
    template="plotly_dark",
    paper_bgcolor="#0E1623",
    plot_bgcolor="#0E1623",
    font=dict(family="Inter, Segoe UI, sans-serif", color="#8aa4c0", size=11),
)

LEGEND = dict(
    orientation="h",
    yanchor="bottom", y=1.01,
    xanchor="left", x=0,
    bgcolor="rgba(0,0,0,0)",
    font=dict(size=11, color="#8aa4c0")
)

LTRN_COLOR    = "#c84b0a"
COMP1_COLOR   = "#3b82f6"
COMP2_COLOR   = "#10b981"
DOWN_COLOR    = "#ef4444"
UP_COLOR      = "#22c55e"
NEUTRAL_COLOR = "#4b6a8a"
GRID_COLOR    = "#162030"

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
            <div style='font-size: 11px; color: #6b8aad; letter-spacing: 1px; text-transform: uppercase; font-weight: 500;'>Stock Price Analytics</div>
            <div style='font-size: 18px; color: #ffffff; font-weight: 600; margin-top: 4px;'>Lantern Pharma</div>
            <div style='font-size: 12px; color: #6b8aad; margin-top: 2px;'>NASDAQ: LTRN</div>
        </div>
    """, unsafe_allow_html=True)
    st.markdown("---")

    st.markdown("<div style='font-size:11px;color:#6b8aad;letter-spacing:0.8px;text-transform:uppercase;font-weight:500;margin-bottom:8px;'>Display Settings</div>", unsafe_allow_html=True)

    timeframe = st.selectbox(
        "Timeframe",
        ["1 Month", "3 Months", "6 Months", "1 Year", "2 Years"],
        index=3,
        label_visibility="collapsed"
    )
    st.markdown("<div style='font-size:11px;color:#6b8aad;margin-bottom:12px;'>Selected period</div>", unsafe_allow_html=True)

    show_ma     = st.checkbox("Moving Averages (MA20 / MA50)", value=True)
    show_bb     = st.checkbox("Bollinger Bands", value=False)
    show_volume = st.checkbox("Volume Panel", value=True)

    st.markdown("---")
    st.markdown("""
        <div style='font-size:11px;color:#4b6a8a;line-height:1.6;'>
            Data source: Yahoo Finance<br>
            Refreshed daily via automated pipeline
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
    st.markdown("<h1 style='margin-bottom:2px;'>Lantern Pharma &nbsp;·&nbsp; NASDAQ: LTRN</h1>", unsafe_allow_html=True)
with col_date:
    st.markdown(f"""
        <div style='text-align:right;padding-top:12px;font-size:11px;color:#6b8aad;letter-spacing:0.5px;'>
            Data through {df.index.max().strftime('%B %d, %Y')}
        </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ── KPI Cards ─────────────────────────────────────────────
current_price    = df["close"].iloc[-1]
prev_price       = df["close"].iloc[-2]
price_change_pct = ((current_price - prev_price) / prev_price) * 100
high_52w         = df["close"].tail(252).max()
low_52w          = df["close"].tail(252).min()
pct_from_high    = ((current_price - high_52w) / high_52w) * 100
current_rsi      = df["rsi_14"].iloc[-1]
max_drawdown     = df["drawdown_pct"].min()
period_return    = df_filtered["cumulative_return"].iloc[-1] - df_filtered["cumulative_return"].iloc[0]

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
    st.metric("Period Return", f"{period_return:+.1f}%", timeframe)

st.markdown("---")

# ── Tabs ──────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "Price & Volume",
    "Technical Indicators",
    "Volatility & Drawdown",
    "Fundamentals",
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
            fill="tonexty", fillcolor="rgba(75,106,138,0.08)",
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
        margin=dict(l=0, r=0, t=40, b=0),
        legend=LEGEND,
        hovermode="x unified"
    )
    fig.update_yaxes(title_text="Price (USD)", row=1, col=1, gridcolor=GRID_COLOR)
    fig.update_yaxes(title_text="Volume", row=2, col=1, gridcolor=GRID_COLOR)
    fig.update_xaxes(gridcolor=GRID_COLOR, showgrid=True)
    st.plotly_chart(fig, use_container_width=True)

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
        margin=dict(l=0, r=0, t=40, b=0),
        hovermode="x unified",
        legend=LEGEND
    )
    fig2.update_yaxes(gridcolor=GRID_COLOR)
    fig2.update_xaxes(gridcolor=GRID_COLOR)
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
            fill="tozeroy", fillcolor="rgba(239,68,68,0.10)",
            line=dict(color=DOWN_COLOR, width=1.5), name="Drawdown",
            hovertemplate="<b>%{x|%b %d, %Y}</b><br>Drawdown: %{y:.2f}%<extra></extra>"
        ))
        fig3a.update_layout(
            **CHART_THEME,
            title=dict(text="Drawdown from Rolling Peak (%)", font=dict(size=12, color="#8aa4c0")),
            height=340, margin=dict(l=0, r=0, t=40, b=0),
            yaxis=dict(gridcolor=GRID_COLOR),
            xaxis=dict(gridcolor=GRID_COLOR)
        )
        st.plotly_chart(fig3a, use_container_width=True)

    with c2:
        fig3b = go.Figure()
        fig3b.add_trace(go.Scatter(
            x=df_filtered.index, y=df_filtered["volatility_30d"],
            fill="tozeroy", fillcolor="rgba(200,75,10,0.08)",
            line=dict(color=LTRN_COLOR, width=1.5), name="30D Volatility",
            hovertemplate="<b>%{x|%b %d, %Y}</b><br>Volatility: %{y:.2f}%<extra></extra>"
        ))
        fig3b.update_layout(
            **CHART_THEME,
            title=dict(text="30-Day Rolling Volatility (%)", font=dict(size=12, color="#8aa4c0")),
            height=340, margin=dict(l=0, r=0, t=40, b=0),
            yaxis=dict(gridcolor=GRID_COLOR),
            xaxis=dict(gridcolor=GRID_COLOR)
        )
        st.plotly_chart(fig3b, use_container_width=True)

    fig3c = go.Figure()
    fig3c.add_trace(go.Histogram(
        x=df_filtered["pct_return"].dropna(), nbinsx=50,
        marker_color=LTRN_COLOR, opacity=0.7, name="Daily Returns"
    ))
    fig3c.add_vline(x=0, line_dash="dash", line_color="#4b6a8a", opacity=0.8)
    fig3c.update_layout(
        **CHART_THEME,
        title=dict(text="Distribution of Daily Returns (%)", font=dict(size=12, color="#8aa4c0")),
        height=300, margin=dict(l=0, r=0, t=40, b=0),
        xaxis=dict(title="Daily Return (%)", gridcolor=GRID_COLOR),
        yaxis=dict(title="Frequency", gridcolor=GRID_COLOR)
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
    fig4.add_hline(y=100, line_dash="dash", line_color="#1c2a3e", opacity=1.0,
                   annotation_text="Base period (100)", annotation_font_size=10)
    fig4.update_layout(
        **CHART_THEME,
        height=340, margin=dict(l=0, r=0, t=10, b=0),
        yaxis=dict(title="Indexed Price", gridcolor=GRID_COLOR),
        xaxis=dict(gridcolor=GRID_COLOR)
    )
    st.plotly_chart(fig4, use_container_width=True)

    st.markdown("---")
    st.caption(f"Fundamentals as of {f.get('fetched_at', 'unknown date')}   ·   Source: Yahoo Finance")