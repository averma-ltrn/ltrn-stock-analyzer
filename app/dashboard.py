import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import os

# ── Page Config ──────────────────────────────────────────
st.set_page_config(
    page_title="LTRN Stock Analyzer",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Styling ───────────────────────────────────────────────
st.markdown("""
    <style>
        .main { background-color: #0f1117; }
        .stMetric { background-color: #1c1f2e; border-radius: 8px; padding: 12px; }
        .stMetric label { color: #a0a0b0 !important; font-size: 13px !important; }
        .stMetric [data-testid="metric-container"] { background-color: #1c1f2e; border-radius: 8px; padding: 16px; }
        div[data-testid="metric-container"] { background-color: #1c1f2e; border: 1px solid #2a2d3e; border-radius: 8px; padding: 16px; }
        .block-container { padding-top: 2rem; }
        h1 { color: #ff6b2b !important; }
        h2, h3 { color: #ffffff !important; }
        .sidebar .sidebar-content { background-color: #1c1f2e; }
    </style>
""", unsafe_allow_html=True)

# ── Load Data ─────────────────────────────────────────────
@st.cache_data(ttl=3600)
def load_indicators():
    path = os.path.join("data", "processed", "ltrn_indicators.csv")
    df = pd.read_csv(path, index_col="date", parse_dates=True)
    return df.sort_index()

@st.cache_data(ttl=3600)
def load_fundamentals():
    path = os.path.join("data", "raw", "ltrn_fundamentals_raw.csv")
    return pd.read_csv(path)

# ── Sidebar ───────────────────────────────────────────────
with st.sidebar:
    st.image("https://www.lanternpharma.com/images/lantern-logo.png", width=160)
    st.markdown("---")
    st.markdown("### Filters")

    timeframe = st.selectbox(
        "Timeframe",
        ["1 Month", "3 Months", "6 Months", "1 Year", "2 Years"],
        index=3
    )

    show_ma = st.checkbox("Show Moving Averages", value=True)
    show_bb = st.checkbox("Show Bollinger Bands", value=False)
    show_volume = st.checkbox("Show Volume", value=True)

    st.markdown("---")
    st.markdown("### About")
    st.markdown("Live equity analytics dashboard for **Lantern Pharma (NASDAQ: LTRN)**")
    st.markdown("Data refreshed daily via yfinance.")

# ── Load ──────────────────────────────────────────────────
try:
    df = load_indicators()
    fundamentals = load_fundamentals()
except FileNotFoundError:
    st.error("Data files not found. Run the ingestion and transformation scripts first.")
    st.stop()

# ── Filter by Timeframe ───────────────────────────────────
timeframe_map = {
    "1 Month": 21,
    "3 Months": 63,
    "6 Months": 126,
    "1 Year": 252,
    "2 Years": 504
}
days = timeframe_map[timeframe]
df_filtered = df.tail(days).copy()

# ── Header ────────────────────────────────────────────────
st.title("Lantern Pharma · NASDAQ: LTRN")
st.markdown(f"*Data through {df.index.max().strftime('%B %d, %Y')}*")
st.markdown("---")

# ── KPI Cards ─────────────────────────────────────────────
current_price = df["close"].iloc[-1]
prev_price = df["close"].iloc[-2]
price_change = current_price - prev_price
price_change_pct = (price_change / prev_price) * 100

high_52w = df["close"].tail(252).max()
low_52w = df["close"].tail(252).min()
pct_from_high = ((current_price - high_52w) / high_52w) * 100
current_rsi = df["rsi_14"].iloc[-1]
max_drawdown = df["drawdown_pct"].min()
cumulative_return = df_filtered["cumulative_return"].iloc[-1] - df_filtered["cumulative_return"].iloc[0]

col1, col2, col3, col4, col5, col6 = st.columns(6)

with col1:
    st.metric("Current Price", f"${current_price:.2f}", f"{price_change_pct:+.2f}%")
with col2:
    st.metric("52W High", f"${high_52w:.2f}", f"{pct_from_high:.1f}% from high")
with col3:
    st.metric("52W Low", f"${low_52w:.2f}")
with col4:
    st.metric("RSI (14)", f"{current_rsi:.1f}", "Neutral" if 40 < current_rsi < 60 else ("Overbought" if current_rsi >= 70 else "Oversold"))
with col5:
    st.metric("Max Drawdown", f"{max_drawdown:.1f}%")
with col6:
    st.metric(f"Return ({timeframe})", f"{cumulative_return:+.1f}%")

st.markdown("---")

# ── Page Tabs ─────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "📈 Price & Volume",
    "📊 Technical Indicators",
    "🌊 Volatility & Drawdown",
    "🏦 Fundamentals"
])

# ════════════════════════════════════════════════════════════
# TAB 1 — Price & Volume
# ════════════════════════════════════════════════════════════
with tab1:
    rows = 2 if show_volume else 1
    row_heights = [0.7, 0.3] if show_volume else [1.0]

    fig = make_subplots(
        rows=rows, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.06,
        row_heights=row_heights
    )

    # Price line
    fig.add_trace(go.Scatter(
        x=df_filtered.index,
        y=df_filtered["close"],
        name="Close Price",
        line=dict(color="#ff6b2b", width=2),
        hovertemplate="<b>%{x|%b %d, %Y}</b><br>Close: $%{y:.2f}<extra></extra>"
    ), row=1, col=1)

    # Moving averages
    if show_ma:
        fig.add_trace(go.Scatter(
            x=df_filtered.index, y=df_filtered["ma_20"],
            name="MA 20", line=dict(color="#00bfff", width=1.5, dash="dot"),
            hovertemplate="MA20: $%{y:.2f}<extra></extra>"
        ), row=1, col=1)

        fig.add_trace(go.Scatter(
            x=df_filtered.index, y=df_filtered["ma_50"],
            name="MA 50", line=dict(color="#ffd700", width=1.5, dash="dot"),
            hovertemplate="MA50: $%{y:.2f}<extra></extra>"
        ), row=1, col=1)

    # Bollinger Bands
    if show_bb:
        fig.add_trace(go.Scatter(
            x=df_filtered.index, y=df_filtered["bb_upper"],
            name="BB Upper", line=dict(color="#888", width=1, dash="dash"),
            hovertemplate="BB Upper: $%{y:.2f}<extra></extra>"
        ), row=1, col=1)

        fig.add_trace(go.Scatter(
            x=df_filtered.index, y=df_filtered["bb_lower"],
            name="BB Lower", line=dict(color="#888", width=1, dash="dash"),
            fill="tonexty", fillcolor="rgba(136,136,136,0.08)",
            hovertemplate="BB Lower: $%{y:.2f}<extra></extra>"
        ), row=1, col=1)

    # Volume bars
    if show_volume:
        colors = ["#ff4444" if r < 0 else "#00c853" for r in df_filtered["pct_return"]]
        fig.add_trace(go.Bar(
            x=df_filtered.index,
            y=df_filtered["volume"],
            name="Volume",
            marker_color=colors,
            opacity=0.7,
            hovertemplate="<b>%{x|%b %d, %Y}</b><br>Volume: %{y:,.0f}<extra></extra>"
        ), row=2, col=1)

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#0f1117",
        plot_bgcolor="#0f1117",
        height=550,
        margin=dict(l=0, r=0, t=20, b=0),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified"
    )
    fig.update_yaxes(title_text="Price (USD)", row=1, col=1, gridcolor="#1e2130")
    fig.update_yaxes(title_text="Volume", row=2, col=1, gridcolor="#1e2130")
    fig.update_xaxes(gridcolor="#1e2130", showgrid=True)

    st.plotly_chart(fig, use_container_width=True)

    # Volume spike table
    spikes = df_filtered[df_filtered["volume_spike"] == True][["close", "volume", "pct_return", "volume_zscore"]].copy()
    spikes.columns = ["Close", "Volume", "% Return", "Volume Z-Score"]
    spikes["Close"] = spikes["Close"].map("${:.2f}".format)
    spikes["Volume"] = spikes["Volume"].map("{:,.0f}".format)
    spikes["% Return"] = spikes["% Return"].map("{:+.2f}%".format)
    spikes["Volume Z-Score"] = spikes["Volume Z-Score"].map("{:.2f}".format)

    if not spikes.empty:
        st.markdown(f"#### 🔺 Volume Spike Days ({len(spikes)} detected in timeframe)")
        st.dataframe(spikes, use_container_width=True)

# ════════════════════════════════════════════════════════════
# TAB 2 — Technical Indicators
# ════════════════════════════════════════════════════════════
with tab2:
    fig2 = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.1,
        subplot_titles=("RSI (14-Day)", "Bollinger Bands")
    )

    # RSI
    fig2.add_trace(go.Scatter(
        x=df_filtered.index, y=df_filtered["rsi_14"],
        name="RSI", line=dict(color="#ff6b2b", width=2),
        hovertemplate="RSI: %{y:.2f}<extra></extra>"
    ), row=1, col=1)

    fig2.add_hline(y=70, line_dash="dash", line_color="#ff4444", annotation_text="Overbought (70)", row=1, col=1)
    fig2.add_hline(y=30, line_dash="dash", line_color="#00c853", annotation_text="Oversold (30)", row=1, col=1)
    fig2.add_hrect(y0=30, y1=70, fillcolor="rgba(255,255,255,0.03)", row=1, col=1)

    # Bollinger Bands with price
    fig2.add_trace(go.Scatter(
        x=df_filtered.index, y=df_filtered["close"],
        name="Close", line=dict(color="#ff6b2b", width=1.5),
        hovertemplate="Close: $%{y:.2f}<extra></extra>"
    ), row=2, col=1)

    fig2.add_trace(go.Scatter(
        x=df_filtered.index, y=df_filtered["bb_upper"],
        name="BB Upper", line=dict(color="#00bfff", width=1, dash="dash"),
        hovertemplate="BB Upper: $%{y:.2f}<extra></extra>"
    ), row=2, col=1)

    fig2.add_trace(go.Scatter(
        x=df_filtered.index, y=df_filtered["bb_lower"],
        name="BB Lower", line=dict(color="#00bfff", width=1, dash="dash"),
        fill="tonexty", fillcolor="rgba(0,191,255,0.07)",
        hovertemplate="BB Lower: $%{y:.2f}<extra></extra>"
    ), row=2, col=1)

    fig2.update_layout(
        template="plotly_dark",
        paper_bgcolor="#0f1117",
        plot_bgcolor="#0f1117",
        height=550,
        margin=dict(l=0, r=0, t=40, b=0),
        hovermode="x unified"
    )
    fig2.update_yaxes(gridcolor="#1e2130")
    fig2.update_xaxes(gridcolor="#1e2130")

    st.plotly_chart(fig2, use_container_width=True)

    # RSI signal
    st.markdown("#### RSI Signal")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Current RSI", f"{current_rsi:.2f}")
    with col2:
        if current_rsi >= 70:
            st.metric("Signal", "⚠️ Overbought")
        elif current_rsi <= 30:
            st.metric("Signal", "🟢 Oversold")
        else:
            st.metric("Signal", "⚪ Neutral")
    with col3:
        st.metric("RSI Range (Period)", f"{df_filtered['rsi_14'].min():.1f} – {df_filtered['rsi_14'].max():.1f}")

# ════════════════════════════════════════════════════════════
# TAB 3 — Volatility & Drawdown
# ════════════════════════════════════════════════════════════
with tab3:
    col1, col2 = st.columns(2)

    with col1:
        # Drawdown chart
        fig3a = go.Figure()
        fig3a.add_trace(go.Scatter(
            x=df_filtered.index,
            y=df_filtered["drawdown_pct"],
            fill="tozeroy",
            fillcolor="rgba(255,68,68,0.2)",
            line=dict(color="#ff4444", width=1.5),
            name="Drawdown %",
            hovertemplate="<b>%{x|%b %d, %Y}</b><br>Drawdown: %{y:.2f}%<extra></extra>"
        ))
        fig3a.update_layout(
            title="Drawdown from Peak (%)",
            template="plotly_dark",
            paper_bgcolor="#0f1117",
            plot_bgcolor="#0f1117",
            height=350,
            margin=dict(l=0, r=0, t=40, b=0),
            yaxis=dict(gridcolor="#1e2130"),
            xaxis=dict(gridcolor="#1e2130")
        )
        st.plotly_chart(fig3a, use_container_width=True)

    with col2:
        # Rolling volatility
        fig3b = go.Figure()
        fig3b.add_trace(go.Scatter(
            x=df_filtered.index,
            y=df_filtered["volatility_30d"],
            fill="tozeroy",
            fillcolor="rgba(255,107,43,0.15)",
            line=dict(color="#ff6b2b", width=1.5),
            name="30D Volatility",
            hovertemplate="<b>%{x|%b %d, %Y}</b><br>Volatility: %{y:.2f}%<extra></extra>"
        ))
        fig3b.update_layout(
            title="30-Day Rolling Volatility (%)",
            template="plotly_dark",
            paper_bgcolor="#0f1117",
            plot_bgcolor="#0f1117",
            height=350,
            margin=dict(l=0, r=0, t=40, b=0),
            yaxis=dict(gridcolor="#1e2130"),
            xaxis=dict(gridcolor="#1e2130")
        )
        st.plotly_chart(fig3b, use_container_width=True)

    # Daily returns histogram
    fig3c = go.Figure()
    fig3c.add_trace(go.Histogram(
        x=df_filtered["pct_return"].dropna(),
        nbinsx=50,
        marker_color="#ff6b2b",
        opacity=0.75,
        name="Daily Returns"
    ))
    fig3c.add_vline(x=0, line_dash="dash", line_color="white", opacity=0.5)
    fig3c.update_layout(
        title="Distribution of Daily Returns (%)",
        template="plotly_dark",
        paper_bgcolor="#0f1117",
        plot_bgcolor="#0f1117",
        height=320,
        margin=dict(l=0, r=0, t=40, b=0),
        xaxis=dict(title="Daily Return (%)", gridcolor="#1e2130"),
        yaxis=dict(title="Frequency", gridcolor="#1e2130")
    )
    st.plotly_chart(fig3c, use_container_width=True)

    # Stats row
    st.markdown("#### Volatility Stats")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Max Drawdown", f"{df_filtered['drawdown_pct'].min():.2f}%")
    with col2:
        st.metric("Avg Daily Return", f"{df_filtered['pct_return'].mean():.2f}%")
    with col3:
        st.metric("Best Day", f"{df_filtered['pct_return'].max():+.2f}%")
    with col4:
        st.metric("Worst Day", f"{df_filtered['pct_return'].min():+.2f}%")

# ════════════════════════════════════════════════════════════
# TAB 4 — Fundamentals
# ════════════════════════════════════════════════════════════
with tab4:
    f = fundamentals.iloc[0]

    st.markdown("#### Balance Sheet Snapshot")
    col1, col2, col3, col4 = st.columns(4)

    def fmt_millions(val):
        try:
            return f"${float(val)/1e6:.1f}M"
        except:
            return "N/A"

    def fmt_currency(val):
        try:
            return f"${float(val):.2f}"
        except:
            return "N/A"

    with col1:
        st.metric("Market Cap", fmt_millions(f.get("market_cap")))
    with col2:
        st.metric("Cash on Hand", fmt_millions(f.get("cash")))
    with col3:
        st.metric("Total Debt", fmt_millions(f.get("total_debt")))
    with col4:
        st.metric("EPS (TTM)", fmt_currency(f.get("eps_ttm")))

    st.markdown("---")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("52W High", fmt_currency(f.get("52w_high")))
    with col2:
        st.metric("52W Low", fmt_currency(f.get("52w_low")))
    with col3:
        st.metric("Shares Outstanding", f"{float(f.get('shares_outstanding', 0)):,.0f}" if f.get("shares_outstanding") else "N/A")
    with col4:
        st.metric("Beta", f"{float(f.get('beta')):.2f}" if f.get("beta") else "N/A")

    st.markdown("---")
    st.markdown("#### Indexed Price Performance")

    fig4 = go.Figure()
    fig4.add_trace(go.Scatter(
        x=df_filtered.index,
        y=df_filtered["indexed_price"],
        fill="tozeroy",
        fillcolor="rgba(255,107,43,0.1)",
        line=dict(color="#ff6b2b", width=2),
        name="Indexed Price (base 100)",
        hovertemplate="<b>%{x|%b %d, %Y}</b><br>Index: %{y:.1f}<extra></extra>"
    ))
    fig4.add_hline(y=100, line_dash="dash", line_color="white", opacity=0.3, annotation_text="Base (start of period)")
    fig4.update_layout(
        template="plotly_dark",
        paper_bgcolor="#0f1117",
        plot_bgcolor="#0f1117",
        height=350,
        margin=dict(l=0, r=0, t=20, b=0),
        yaxis=dict(title="Indexed Price", gridcolor="#1e2130"),
        xaxis=dict(gridcolor="#1e2130")
    )
    st.plotly_chart(fig4, use_container_width=True)

    st.markdown("---")
    st.caption(f"Fundamentals last fetched: {f.get('fetched_at', 'Unknown')} · Source: Yahoo Finance via yfinance")