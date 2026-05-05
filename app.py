import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import sys
import os

sys.path.append(os.path.dirname(__file__))
from utils.windsor import (
    get_windsor_data, safe_num, fmt_currency, fmt_number, fmt_pct
)

# ── PAGE CONFIG ──────────────────────────────────────────
st.set_page_config(
    page_title="Raneen Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── COLORS ───────────────────────────────────────────────
C = {
    "blue":   "#3266AD",
    "green":  "#1D9E75",
    "red":    "#D85A30",
    "amber":  "#EF9F27",
    "purple": "#7F77DD",
    "gray":   "#888780",
    "dark":   "#0F1117",
    "card":   "#1A1F2E",
    "border": "#2A3050",
    "text":   "#E8E8E8",
    "muted":  "#9A9A8E",
}

# ── CUSTOM CSS ───────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@300;400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'IBM Plex Sans Arabic', sans-serif;
}

/* Hide Streamlit branding */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 1.2rem 2rem 2rem; max-width: 1400px; }

/* Sidebar */
section[data-testid="stSidebar"] {
    background: #111827;
    border-right: 1px solid #1E2A3A;
}
section[data-testid="stSidebar"] .stSelectbox label,
section[data-testid="stSidebar"] .stTextInput label {
    color: #9A9A8E !important;
    font-size: 12px;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: .05em;
}

/* KPI Cards */
.kpi-card {
    background: #1A1F2E;
    border: 1px solid #2A3050;
    border-radius: 12px;
    padding: 18px 20px;
    position: relative;
    overflow: hidden;
    transition: border-color .2s;
}
.kpi-card:hover { border-color: #3266AD; }
.kpi-accent { position: absolute; top: 0; left: 0; right: 0; height: 3px; border-radius: 12px 12px 0 0; }
.kpi-label { font-size: 11px; color: #9A9A8E; font-weight: 500; text-transform: uppercase; letter-spacing: .06em; margin-bottom: 8px; }
.kpi-value { font-size: 26px; font-weight: 600; color: #E8E8E8; line-height: 1; margin-bottom: 6px; }
.kpi-change { font-size: 12px; }
.kpi-sub { font-size: 11px; color: #9A9A8E; margin-top: 2px; }
.up   { color: #1D9E75; }
.down { color: #D85A30; }
.warn { color: #EF9F27; }
.neu  { color: #888780; }

/* Section headers */
.section-header {
    display: flex; align-items: center; gap: 10px;
    padding: 6px 0 10px;
    border-bottom: 1px solid #2A3050;
    margin-bottom: 16px;
}
.section-dot { width: 8px; height: 8px; border-radius: 50%; }
.section-title { font-size: 15px; font-weight: 600; color: #E8E8E8; }
.section-sub { font-size: 11px; color: #9A9A8E; margin-left: auto; }

/* Insight cards */
.insight-card {
    border-radius: 8px; padding: 12px 14px;
    margin-bottom: 8px; font-size: 13px; line-height: 1.6;
    border-left: 4px solid;
}
.insight-red    { background: rgba(216,90,48,.12); border-color: #D85A30; color: #F4A87A; }
.insight-amber  { background: rgba(239,159,39,.10); border-color: #EF9F27; color: #F4C87A; }
.insight-green  { background: rgba(29,158,117,.10); border-color: #1D9E75; color: #7AE0C1; }
.insight-blue   { background: rgba(50,102,173,.12); border-color: #3266AD; color: #82B0E8; }

/* Top bar */
.top-bar {
    display: flex; align-items: center; justify-content: space-between;
    padding: 10px 0 16px;
    border-bottom: 1px solid #2A3050;
    margin-bottom: 20px;
}
.brand-name { font-size: 22px; font-weight: 700; color: #E8E8E8; }
.brand-name span { color: #3266AD; }
.live-badge {
    display: inline-flex; align-items: center; gap: 6px;
    background: rgba(29,158,117,.15); border: 1px solid rgba(29,158,117,.3);
    border-radius: 20px; padding: 4px 12px;
    font-size: 11px; font-weight: 500; color: #1D9E75;
}
.live-dot { width: 6px; height: 6px; border-radius: 50%; background: #1D9E75;
            animation: blink 2s ease-in-out infinite; display: inline-block; }
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:.3} }

/* Funnel bars */
.funnel-row {
    display: flex; align-items: center; gap: 12px;
    margin-bottom: 10px;
}
.funnel-label { font-size: 12px; color: #9A9A8E; min-width: 120px; }
.funnel-track {
    flex: 1; height: 28px; background: #1A1F2E;
    border-radius: 4px; overflow: hidden; position: relative;
}
.funnel-fill {
    height: 100%; border-radius: 4px;
    display: flex; align-items: center; padding-left: 10px;
    font-size: 11px; font-weight: 600; color: #fff;
}
.funnel-pct { font-size: 12px; min-width: 45px; text-align: right; font-weight: 600; }

/* Horizontal bar rows */
.bar-row { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }
.bar-name { font-size: 12px; color: #9A9A8E; min-width: 130px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.bar-track { flex: 1; height: 8px; background: #1A1F2E; border-radius: 4px; overflow: hidden; }
.bar-fill  { height: 100%; border-radius: 4px; }
.bar-val   { font-size: 12px; color: #E8E8E8; min-width: 70px; text-align: right; font-weight: 500; }

/* Tables */
.styled-table { width: 100%; border-collapse: collapse; font-size: 12px; }
.styled-table th {
    background: #111827; color: #9A9A8E; font-weight: 500;
    font-size: 11px; text-transform: uppercase; letter-spacing: .05em;
    padding: 8px 10px; border-bottom: 1px solid #2A3050; text-align: left;
}
.styled-table td {
    padding: 9px 10px; border-bottom: 1px solid #1E2A3A;
    color: #E8E8E8; vertical-align: middle;
}
.styled-table tr:hover td { background: rgba(50,102,173,.06); }
.badge { display: inline-block; font-size: 10px; padding: 2px 8px; border-radius: 10px; font-weight: 600; }
.badge-green  { background: rgba(29,158,117,.2);  color: #1D9E75; }
.badge-red    { background: rgba(216,90,48,.2);   color: #D85A30; }
.badge-amber  { background: rgba(239,159,39,.2);  color: #EF9F27; }
.badge-blue   { background: rgba(50,102,173,.2);  color: #3266AD; }
.badge-purple { background: rgba(127,119,221,.2); color: #7F77DD; }
.badge-gray   { background: rgba(136,135,128,.2); color: #888780; }
</style>
""", unsafe_allow_html=True)

# ── PLOTLY THEME ─────────────────────────────────────────
PLOT_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="IBM Plex Sans Arabic", color="#9A9A8E", size=11),
    margin=dict(l=0, r=0, t=10, b=0),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                font=dict(size=11), bgcolor="rgba(0,0,0,0)"),
    xaxis=dict(gridcolor="#1E2A3A", linecolor="#2A3050", tickfont=dict(size=10)),
    yaxis=dict(gridcolor="#1E2A3A", linecolor="#2A3050", tickfont=dict(size=10)),
)

# ── SIDEBAR ───────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding:16px 0 20px">
      <div style="font-size:18px;font-weight:700;color:#E8E8E8">
        <span style="color:#3266AD">●</span> Raneen
      </div>
      <div style="font-size:11px;color:#9A9A8E;margin-top:4px">Analytics Dashboard</div>
    </div>
    """, unsafe_allow_html=True)

    api_key = st.text_input(
        "Windsor API Key",
        type="password",
        placeholder="wnd_xxxxxxxxxxxx",
        help="Get it from windsor.ai → Settings → API Keys",
    )

    st.markdown("---")

    date_preset = st.selectbox(
        "Date Range",
        ["last_30d", "last_7d", "last_14d", "last_90d", "this_month", "last_month"],
        format_func=lambda x: {
            "last_7d": "Last 7 Days",
            "last_14d": "Last 14 Days",
            "last_30d": "Last 30 Days",
            "last_90d": "Last 90 Days",
            "this_month": "This Month",
            "last_month": "Last Month",
        }.get(x, x),
    )

    st.markdown("---")

    active_tab = st.radio(
        "Section",
        ["Overview", "Funnel", "Traffic", "Devices", "E-Commerce", "Campaigns", "Insights"],
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown(
        '<div style="font-size:10px;color:#9A9A8E;line-height:1.6">'
        'Data source: Google Analytics 4<br>'
        'via Windsor.ai Connector<br>'
        '<span style="color:#1D9E75">● Live</span> — refreshes on load'
        "</div>",
        unsafe_allow_html=True,
    )

# ── TOP BAR ───────────────────────────────────────────────
st.markdown("""
<div class="top-bar">
  <div class="brand-name"><span>Raneen</span>.com Analytics</div>
  <div class="live-badge"><span class="live-dot"></span> Live via Windsor · GA4</div>
</div>
""", unsafe_allow_html=True)

# ── GATE: need API key ────────────────────────────────────
if not api_key:
    st.markdown("""
    <div style="text-align:center;padding:60px 20px">
      <div style="font-size:48px;margin-bottom:16px">🔑</div>
      <div style="font-size:20px;font-weight:600;color:#E8E8E8;margin-bottom:8px">
        Enter Your Windsor API Key
      </div>
      <div style="font-size:14px;color:#9A9A8E;max-width:400px;margin:0 auto">
        Get your API key from <b style="color:#3266AD">windsor.ai → Settings → API Keys</b>
        and paste it in the sidebar to load your live GA4 data.
      </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ── LOAD DATA ─────────────────────────────────────────────
@st.cache_data(ttl=300, show_spinner=False)
def load_overview(key, preset):
    return get_windsor_data(key, [
        "date", "sessions", "active_users", "purchase_revenue",
        "transactions", "bounce_rate", "add_to_carts",
        "checkouts", "average_session_duration",
    ], date_preset=preset)

@st.cache_data(ttl=300, show_spinner=False)
def load_channels(key, preset):
    return get_windsor_data(key, [
        "session_default_channel_group", "sessions",
        "purchase_revenue", "transactions", "add_to_carts", "checkouts",
    ], date_preset=preset)

@st.cache_data(ttl=300, show_spinner=False)
def load_devices(key, preset):
    return get_windsor_data(key, [
        "devicecategory", "sessions", "purchase_revenue",
        "transactions", "bounce_rate", "engagement_rate",
    ], date_preset=preset)

@st.cache_data(ttl=300, show_spinner=False)
def load_new_returning(key, preset):
    return get_windsor_data(key, [
        "new_vs_returning", "sessions",
        "active_users", "purchase_revenue", "transactions",
    ], date_preset=preset)

@st.cache_data(ttl=300, show_spinner=False)
def load_campaigns(key, preset):
    return get_windsor_data(key, [
        "session_google_ads_campaign_name", "sessions",
        "purchase_revenue", "transactions", "add_to_carts", "checkouts",
    ], date_preset=preset)

@st.cache_data(ttl=300, show_spinner=False)
def load_categories(key, preset):
    return get_windsor_data(key, [
        "item_category", "gross_item_revenue",
        "items_purchased", "items_viewed", "items_added_to_cart",
    ], date_preset=preset)

@st.cache_data(ttl=300, show_spinner=False)
def load_products(key, preset):
    return get_windsor_data(key, [
        "item_name", "item_revenue",
        "items_purchased", "items_viewed", "items_added_to_cart",
    ], date_preset=preset)

with st.spinner("Loading data from Windsor..."):
    df_ov  = load_overview(api_key, date_preset)
    df_ch  = load_channels(api_key, date_preset)
    df_dv  = load_devices(api_key, date_preset)
    df_nr  = load_new_returning(api_key, date_preset)
    df_cp  = load_campaigns(api_key, date_preset)

if df_ov.empty:
    st.error("❌ Could not load data. Check your API key and try again.")
    st.stop()

# ── COMPUTE TOTALS ────────────────────────────────────────
tot_sessions  = safe_num(df_ov["sessions"].sum()) if "sessions" in df_ov else 0
tot_revenue   = safe_num(df_ov["purchase_revenue"].sum()) if "purchase_revenue" in df_ov else 0
tot_orders    = safe_num(df_ov["transactions"].sum()) if "transactions" in df_ov else 0
tot_carts     = safe_num(df_ov["add_to_carts"].sum()) if "add_to_carts" in df_ov else 0
tot_checkouts = safe_num(df_ov["checkouts"].sum()) if "checkouts" in df_ov else 0
avg_bounce    = safe_num(df_ov["bounce_rate"].mean()) * 100 if "bounce_rate" in df_ov else 0
avg_session   = safe_num(df_ov["average_session_duration"].mean()) if "average_session_duration" in df_ov else 0
aov           = tot_revenue / tot_orders if tot_orders > 0 else 0
cvr           = (tot_orders / tot_sessions * 100) if tot_sessions > 0 else 0
cart_abandon  = (1 - tot_orders / tot_carts) * 100 if tot_carts > 0 else 0
avg_session_m = int(avg_session // 60)
avg_session_s = int(avg_session % 60)

# ── HELPERS ───────────────────────────────────────────────
def kpi_card(label, value, change_txt, change_cls, sub="", accent_color="#3266AD"):
    return f"""
    <div class="kpi-card">
      <div class="kpi-accent" style="background:{accent_color}"></div>
      <div class="kpi-label">{label}</div>
      <div class="kpi-value">{value}</div>
      <div class="kpi-change {change_cls}">{change_txt}</div>
      {'<div class="kpi-sub">'+sub+'</div>' if sub else ''}
    </div>"""

def section_header(title, sub="", color="#3266AD"):
    return f"""
    <div class="section-header">
      <div class="section-dot" style="background:{color}"></div>
      <div class="section-title">{title}</div>
      {'<div class="section-sub">'+sub+'</div>' if sub else ''}
    </div>"""

def bar_html(name, pct, color, val_str):
    fill = max(pct, 1)
    return f"""
    <div class="bar-row">
      <div class="bar-name">{name}</div>
      <div class="bar-track"><div class="bar-fill" style="width:{fill}%;background:{color}"></div></div>
      <div class="bar-val">{val_str}</div>
    </div>"""

def insight(icon, title, body, cls):
    return f'<div class="insight-card {cls}"><b>{icon} {title}</b><br/>{body}</div>'

# ═════════════════════════════════════════════════════════
# ── OVERVIEW TAB ─────────────────────────────────────────
# ═════════════════════════════════════════════════════════
if active_tab == "Overview":
    st.markdown(section_header("Overview", "Key Performance Indicators", "#3266AD"), unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(kpi_card("Sessions", fmt_number(tot_sessions), "▲ Live GA4 Data", "up", accent_color="#3266AD"), unsafe_allow_html=True)
    with c2:
        st.markdown(kpi_card("Revenue", fmt_currency(tot_revenue), "▲ Purchase Revenue", "up", accent_color="#1D9E75"), unsafe_allow_html=True)
    with c3:
        st.markdown(kpi_card("Orders", fmt_number(tot_orders), "▲ Transactions", "up", accent_color="#1D9E75"), unsafe_allow_html=True)
    with c4:
        st.markdown(kpi_card("AOV", fmt_currency(aov, 0), "متوسط قيمة الطلب", "neu", accent_color="#3266AD"), unsafe_allow_html=True)

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    c5, c6, c7, c8 = st.columns(4)
    with c5:
        st.markdown(kpi_card("Add to Cart", fmt_number(tot_carts), f"⚠ Cart Abandon {cart_abandon:.1f}%", "warn", accent_color="#EF9F27"), unsafe_allow_html=True)
    with c6:
        st.markdown(kpi_card("Bounce Rate", fmt_pct(avg_bounce), "▼ Monitor carefully", "down" if avg_bounce > 50 else "warn", accent_color="#D85A30"), unsafe_allow_html=True)
    with c7:
        st.markdown(kpi_card("Avg Session", f"{avg_session_m}:{avg_session_s:02d} min", "▲ Engagement", "up", accent_color="#7F77DD"), unsafe_allow_html=True)
    with c8:
        st.markdown(kpi_card("CVR", fmt_pct(cvr, 2), "⚠ Needs improvement" if cvr < 1 else "▲ Good", "warn" if cvr < 1 else "up", accent_color="#D85A30" if cvr < 1 else "#1D9E75"), unsafe_allow_html=True)

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    # Time series charts
    if "date" in df_ov.columns:
        df_ts = df_ov.copy()
        df_ts["date"] = pd.to_datetime(df_ts["date"], errors="coerce")
        df_ts = df_ts.dropna(subset=["date"]).sort_values("date")

        col_l, col_r = st.columns(2)
        with col_l:
            st.markdown(section_header("Revenue Over Time", "", "#1D9E75"), unsafe_allow_html=True)
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            fig.add_trace(go.Bar(
                x=df_ts["date"], y=df_ts["purchase_revenue"] / 1000,
                name="Revenue (K ج)", marker_color="#3266AD", opacity=0.8,
            ), secondary_y=False)
            fig.add_trace(go.Scatter(
                x=df_ts["date"], y=df_ts["transactions"],
                name="Orders", line=dict(color="#1D9E75", width=2),
                mode="lines+markers", marker_size=4,
            ), secondary_y=True)
            fig.update_layout(**PLOT_LAYOUT, height=260)
            fig.update_yaxes(title_text="Revenue (K ج)", secondary_y=False, tickformat=".0f")
            fig.update_yaxes(title_text="Orders", secondary_y=True)
            st.plotly_chart(fig, use_container_width=True)

        with col_r:
            st.markdown(section_header("Sessions & Bounce Rate", "", "#D85A30"), unsafe_allow_html=True)
            fig2 = make_subplots(specs=[[{"secondary_y": True}]])
            fig2.add_trace(go.Bar(
                x=df_ts["date"], y=df_ts["sessions"] / 1000,
                name="Sessions (K)", marker_color="rgba(50,102,173,0.7)",
            ), secondary_y=False)
            if "bounce_rate" in df_ts.columns:
                fig2.add_trace(go.Scatter(
                    x=df_ts["date"], y=df_ts["bounce_rate"] * 100,
                    name="Bounce %", line=dict(color="#D85A30", width=2),
                    mode="lines", fill="tozeroy", fillcolor="rgba(216,90,48,0.1)",
                ), secondary_y=True)
            fig2.update_layout(**PLOT_LAYOUT, height=260)
            fig2.update_yaxes(title_text="Sessions (K)", secondary_y=False)
            fig2.update_yaxes(title_text="Bounce %", secondary_y=True, ticksuffix="%")
            st.plotly_chart(fig2, use_container_width=True)

    # New vs Returning
    st.markdown(section_header("New vs Returning Users", "Revenue Split", "#7F77DD"), unsafe_allow_html=True)
    if not df_nr.empty and "new_vs_returning" in df_nr.columns:
        nr = df_nr[df_nr["new_vs_returning"].isin(["new", "returning"])].copy()
        nr["purchase_revenue"] = nr["purchase_revenue"].apply(safe_num)
        nr["sessions"] = nr["sessions"].apply(safe_num)
        nr["transactions"] = nr["transactions"].apply(safe_num)

        ret = nr[nr["new_vs_returning"] == "returning"]
        new = nr[nr["new_vs_returning"] == "new"]

        ret_rev = ret["purchase_revenue"].sum()
        new_rev = new["purchase_revenue"].sum()
        tot_rev_nr = ret_rev + new_rev
        ret_pct = ret_rev / tot_rev_nr * 100 if tot_rev_nr > 0 else 0

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(kpi_card("Returning Sessions", fmt_number(ret["sessions"].sum()), "Loyal customers", "neu", accent_color="#1D9E75"), unsafe_allow_html=True)
        with c2:
            st.markdown(kpi_card("Returning Revenue", fmt_currency(ret_rev), f"▲ {ret_pct:.1f}% of total", "up", accent_color="#1D9E75"), unsafe_allow_html=True)
        with c3:
            ret_cvr = ret["transactions"].sum() / ret["sessions"].sum() * 100 if ret["sessions"].sum() > 0 else 0
            st.markdown(kpi_card("Returning CVR", fmt_pct(ret_cvr, 2), "vs New users", "up", accent_color="#1D9E75"), unsafe_allow_html=True)
        with c4:
            new_cvr = new["transactions"].sum() / new["sessions"].sum() * 100 if new["sessions"].sum() > 0 else 0
            st.markdown(kpi_card("New Users CVR", fmt_pct(new_cvr, 2), "Lower than returning", "warn", accent_color="#3266AD"), unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════
# ── FUNNEL TAB ───────────────────────────────────────────
# ═════════════════════════════════════════════════════════
elif active_tab == "Funnel":
    st.markdown(section_header("Sales Funnel", "Session → Purchase", "#3266AD"), unsafe_allow_html=True)

    steps = [
        ("Sessions",       tot_sessions, 100.0,  "#3266AD"),
        ("Add to Cart",    tot_carts,    tot_carts / tot_sessions * 100 if tot_sessions else 0, "#378ADD"),
        ("Checkout Start", tot_checkouts, tot_checkouts / tot_sessions * 100 if tot_sessions else 0, "#85B7EB"),
        ("Purchase",       tot_orders,   cvr, "#1D9E75"),
    ]

    for label, count, pct, color in steps:
        bar_w = max(pct, 0.5)
        st.markdown(f"""
        <div class="funnel-row">
          <div class="funnel-label">{label}</div>
          <div class="funnel-track">
            <div class="funnel-fill" style="width:{bar_w}%;background:{color}">
              {'&nbsp;'+fmt_number(count) if bar_w > 8 else ''}
            </div>
          </div>
          <div class="funnel-pct" style="color:{color}">{pct:.2f}%</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    cart_drop = (1 - tot_carts / tot_sessions) * 100 if tot_sessions else 0
    checkout_drop = (1 - tot_checkouts / tot_carts) * 100 if tot_carts else 0
    purchase_drop = (1 - tot_orders / tot_checkouts) * 100 if tot_checkouts else 0

    with c1:
        st.markdown(kpi_card("Session → Cart", fmt_pct(100 - cart_drop, 1), f"⚠ {cart_drop:.1f}% drop off", "warn", accent_color="#EF9F27"), unsafe_allow_html=True)
    with c2:
        st.markdown(kpi_card("Cart → Checkout", fmt_pct(100 - checkout_drop, 1), f"⚠ {checkout_drop:.1f}% abandon cart", "down", accent_color="#D85A30"), unsafe_allow_html=True)
    with c3:
        st.markdown(kpi_card("Checkout → Purchase", fmt_pct(100 - purchase_drop, 1), f"⚠ {purchase_drop:.1f}% drop at checkout", "down" if purchase_drop > 50 else "warn", accent_color="#D85A30"), unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # Funnel chart
    fig = go.Figure(go.Funnel(
        y=["Sessions", "Add to Cart", "Checkout", "Purchase"],
        x=[tot_sessions, tot_carts, tot_checkouts, tot_orders],
        textinfo="value+percent initial",
        marker=dict(color=["#3266AD", "#378ADD", "#85B7EB", "#1D9E75"]),
        connector=dict(line=dict(color="#2A3050", width=1)),
    ))
    fig.update_layout(**PLOT_LAYOUT, height=320)
    st.plotly_chart(fig, use_container_width=True)

    # New vs Returning funnel table
    if not df_nr.empty and "new_vs_returning" in df_nr.columns:
        st.markdown(section_header("New vs Returning — Funnel Comparison", "", "#7F77DD"), unsafe_allow_html=True)
        nr = df_nr[df_nr["new_vs_returning"].isin(["new", "returning"])].copy()
        for col in ["sessions", "purchase_revenue", "transactions"]:
            if col in nr.columns:
                nr[col] = nr[col].apply(safe_num)

        rows = []
        for seg in ["returning", "new"]:
            d = nr[nr["new_vs_returning"] == seg]
            ses = d["sessions"].sum()
            rev = d["purchase_revenue"].sum()
            txn = d["transactions"].sum()
            _cvr = txn / ses * 100 if ses > 0 else 0
            _aov = rev / txn if txn > 0 else 0
            badge_cls = "badge-green" if seg == "returning" else "badge-blue"
            badge_lbl = "Returning" if seg == "returning" else "New"
            rows.append(f"""
            <tr>
              <td><span class="badge {badge_cls}">{badge_lbl}</span></td>
              <td>{fmt_number(ses)}</td>
              <td>{fmt_currency(rev)}</td>
              <td>{fmt_number(txn)}</td>
              <td><b style="color:{'#1D9E75' if seg=='returning' else '#EF9F27'}">{fmt_pct(_cvr,2)}</b></td>
              <td>{fmt_currency(_aov, 0)}</td>
            </tr>""")

        st.markdown(f"""
        <table class="styled-table">
          <thead><tr><th>Segment</th><th>Sessions</th><th>Revenue</th><th>Orders</th><th>CVR</th><th>AOV</th></tr></thead>
          <tbody>{''.join(rows)}</tbody>
        </table>""", unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════
# ── TRAFFIC TAB ──────────────────────────────────────────
# ═════════════════════════════════════════════════════════
elif active_tab == "Traffic":
    st.markdown(section_header("Traffic Sources", "Sessions & Revenue by Channel", "#3266AD"), unsafe_allow_html=True)

    if not df_ch.empty and "session_default_channel_group" in df_ch.columns:
        for col in ["sessions", "purchase_revenue", "transactions", "add_to_carts"]:
            if col in df_ch.columns:
                df_ch[col] = df_ch[col].apply(safe_num)

        df_ch = df_ch[df_ch["session_default_channel_group"].notna()]
        df_ch = df_ch[df_ch["session_default_channel_group"] != ""]
        df_ch_g = df_ch.groupby("session_default_channel_group").sum().reset_index()
        df_ch_g = df_ch_g[df_ch_g["sessions"] > 10].sort_values("purchase_revenue", ascending=False)

        col_l, col_r = st.columns(2)
        with col_l:
            st.markdown("**Sessions by Channel**", unsafe_allow_html=False)
            max_ses = df_ch_g["sessions"].max()
            colors_ch = ["#3266AD", "#378ADD", "#85B7EB", "#1D9E75", "#5DCAA5", "#EF9F27", "#888780", "#7F77DD"]
            for i, row in df_ch_g.head(8).iterrows():
                pct = row["sessions"] / max_ses * 100 if max_ses else 0
                col = colors_ch[i % len(colors_ch)] if i < len(colors_ch) else "#888780"
                st.markdown(bar_html(row["session_default_channel_group"], pct, col, fmt_number(row["sessions"])), unsafe_allow_html=True)

        with col_r:
            st.markdown("**Revenue by Channel**", unsafe_allow_html=False)
            max_rev = df_ch_g["purchase_revenue"].max()
            rev_colors = ["#1D9E75", "#5DCAA5", "#9FE1CB", "#EF9F27", "#3266AD", "#888780", "#7F77DD", "#D85A30"]
            for i, row in df_ch_g.sort_values("purchase_revenue", ascending=False).head(8).iterrows():
                pct = row["purchase_revenue"] / max_rev * 100 if max_rev else 0
                col = rev_colors[i % len(rev_colors)] if i < len(rev_colors) else "#888780"
                st.markdown(bar_html(row["session_default_channel_group"], pct, col, fmt_currency(row["purchase_revenue"])), unsafe_allow_html=True)

        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
        st.markdown(section_header("Channel Efficiency", "CVR & Revenue per Session", "#EF9F27"), unsafe_allow_html=True)

        rows = []
        for _, row in df_ch_g.iterrows():
            ses = row["sessions"]
            rev = row["purchase_revenue"]
            txn = row["transactions"]
            _cvr = txn / ses * 100 if ses > 0 else 0
            rps = rev / ses if ses > 0 else 0
            if _cvr >= 1.5:
                badge = '<span class="badge badge-green">الأقوى</span>'
            elif _cvr >= 0.8:
                badge = '<span class="badge badge-blue">جيد</span>'
            elif _cvr >= 0.4:
                badge = '<span class="badge badge-amber">راجع</span>'
            else:
                badge = '<span class="badge badge-red">ضعيف</span>'
            rows.append(f"""
            <tr>
              <td><b>{row['session_default_channel_group']}</b></td>
              <td>{fmt_number(ses)}</td>
              <td>{fmt_currency(rev)}</td>
              <td>{fmt_number(txn)}</td>
              <td><b style="color:{'#1D9E75' if _cvr>=1 else '#EF9F27' if _cvr>=0.5 else '#D85A30'}">{fmt_pct(_cvr,2)}</b></td>
              <td>{fmt_currency(rps, 1)}</td>
              <td>{badge}</td>
            </tr>""")

        st.markdown(f"""
        <table class="styled-table">
          <thead><tr><th>Channel</th><th>Sessions</th><th>Revenue</th><th>Orders</th><th>CVR</th><th>Rev/Session</th><th>Rating</th></tr></thead>
          <tbody>{''.join(rows)}</tbody>
        </table>""", unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════
# ── DEVICES TAB ──────────────────────────────────────────
# ═════════════════════════════════════════════════════════
elif active_tab == "Devices":
    st.markdown(section_header("Device Performance", "Mobile vs Desktop vs Tablet", "#7F77DD"), unsafe_allow_html=True)

    if not df_dv.empty and "devicecategory" in df_dv.columns:
        for col in ["sessions", "purchase_revenue", "transactions", "bounce_rate"]:
            if col in df_dv.columns:
                df_dv[col] = df_dv[col].apply(safe_num)

        dev_colors = {"mobile": "#3266AD", "desktop": "#888780", "tablet": "#1D9E75"}
        main_devs = df_dv[df_dv["devicecategory"].isin(["mobile", "desktop", "tablet"])]

        cols = st.columns(len(main_devs))
        for i, (_, row) in enumerate(main_devs.iterrows()):
            dev = row["devicecategory"]
            col = dev_colors.get(dev, "#888780")
            ses = row["sessions"]
            rev = row["purchase_revenue"]
            br = row["bounce_rate"] * 100
            tot_ses_dv = main_devs["sessions"].sum()
            ses_pct = ses / tot_ses_dv * 100 if tot_ses_dv else 0

            with cols[i]:
                st.markdown(kpi_card(
                    dev.title(),
                    f"{ses_pct:.1f}%",
                    f"Bounce: {br:.1f}%",
                    "down" if br > 55 else "warn" if br > 45 else "up",
                    f"Sessions: {fmt_number(ses)} · Rev: {fmt_currency(rev)}",
                    accent_color=col,
                ), unsafe_allow_html=True)

        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

        col_l, col_r = st.columns(2)
        with col_l:
            st.markdown(section_header("Revenue Split", "", "#1D9E75"), unsafe_allow_html=True)
            fig = go.Figure(go.Pie(
                labels=main_devs["devicecategory"].str.title(),
                values=main_devs["purchase_revenue"],
                marker_colors=[dev_colors.get(d, "#888780") for d in main_devs["devicecategory"]],
                hole=0.6, textinfo="label+percent",
                textfont_size=11,
            ))
            fig.update_layout(**PLOT_LAYOUT, height=260)
            st.plotly_chart(fig, use_container_width=True)

        with col_r:
            st.markdown(section_header("Bounce Rate by Device", "", "#D85A30"), unsafe_allow_html=True)
            fig2 = go.Figure(go.Bar(
                x=main_devs["devicecategory"].str.title(),
                y=main_devs["bounce_rate"] * 100,
                marker_color=[dev_colors.get(d, "#888780") for d in main_devs["devicecategory"]],
                text=[f"{r*100:.1f}%" for r in main_devs["bounce_rate"]],
                textposition="outside",
            ))
            fig2.update_layout(**PLOT_LAYOUT, height=260,
                               yaxis=dict(ticksuffix="%", range=[0, 80], gridcolor="#1E2A3A"))
            st.plotly_chart(fig2, use_container_width=True)


# ═════════════════════════════════════════════════════════
# ── E-COMMERCE TAB ───────────────────────────────────────
# ═════════════════════════════════════════════════════════
elif active_tab == "E-Commerce":
    st.markdown(section_header("E-Commerce Insights", "Products & Categories", "#1D9E75"), unsafe_allow_html=True)

    with st.spinner("Loading e-commerce data..."):
        df_cat = load_categories(api_key, date_preset)
        df_prod = load_products(api_key, date_preset)

    if not df_cat.empty and "item_category" in df_cat.columns:
        for col in ["gross_item_revenue", "items_purchased", "items_viewed", "items_added_to_cart"]:
            if col in df_cat.columns:
                df_cat[col] = df_cat[col].apply(safe_num)

        raneen_cats = ["الأجهزة المنزلية", "الأثاث", "الإلكترونيات", "المطبخ", "موبايلات",
                       "المفروشات", "عروض رنين", "المنزل", "المنتجات العائلية", "الأزياء و الموضة"]
        df_cat_f = df_cat[df_cat["item_category"].isin(raneen_cats)].sort_values("gross_item_revenue", ascending=False)

        tot_item_rev = df_cat_f["gross_item_revenue"].sum()
        tot_item_units = df_cat_f["items_purchased"].sum()

        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(kpi_card("Item Revenue", fmt_currency(tot_item_rev), "All categories", "up", accent_color="#1D9E75"), unsafe_allow_html=True)
        with c2:
            st.markdown(kpi_card("Units Sold", fmt_number(tot_item_units), "Total items purchased", "up", accent_color="#3266AD"), unsafe_allow_html=True)
        with c3:
            avg_price = tot_item_rev / tot_item_units if tot_item_units else 0
            st.markdown(kpi_card("Avg Unit Price", fmt_currency(avg_price, 0), "Revenue / Units", "neu", accent_color="#7F77DD"), unsafe_allow_html=True)

        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

        col_l, col_r = st.columns(2)
        with col_l:
            st.markdown(section_header("Revenue by Category", "", "#1D9E75"), unsafe_allow_html=True)
            max_rev = df_cat_f["gross_item_revenue"].max()
            cat_colors = ["#3266AD", "#378ADD", "#85B7EB", "#1D9E75", "#5DCAA5", "#EF9F27", "#7F77DD", "#D85A30", "#888780", "#B5D4F4"]
            for i, (_, row) in enumerate(df_cat_f.head(8).iterrows()):
                pct = row["gross_item_revenue"] / max_rev * 100 if max_rev else 0
                col = cat_colors[i % len(cat_colors)]
                st.markdown(bar_html(row["item_category"], pct, col, fmt_currency(row["gross_item_revenue"])), unsafe_allow_html=True)

        with col_r:
            st.markdown(section_header("Cart-to-View Rate", "", "#EF9F27"), unsafe_allow_html=True)
            df_cat_f["cart_rate"] = df_cat_f.apply(
                lambda r: r["items_added_to_cart"] / r["items_viewed"] * 100 if r["items_viewed"] > 0 else 0, axis=1)
            df_cat_sorted = df_cat_f.sort_values("cart_rate", ascending=False)
            max_cr = df_cat_sorted["cart_rate"].max()
            for i, (_, row) in enumerate(df_cat_sorted.head(8).iterrows()):
                pct = row["cart_rate"] / max_cr * 100 if max_cr else 0
                col = "#1D9E75" if row["cart_rate"] > 6 else "#EF9F27" if row["cart_rate"] > 3 else "#D85A30"
                st.markdown(bar_html(row["item_category"], pct, col, f"{row['cart_rate']:.1f}%"), unsafe_allow_html=True)

    # Top products table
    if not df_prod.empty and "item_name" in df_prod.columns:
        for col in ["item_revenue", "items_purchased", "items_viewed", "items_added_to_cart"]:
            if col in df_prod.columns:
                df_prod[col] = df_prod[col].apply(safe_num)

        df_top = df_prod[df_prod["item_revenue"] > 0].sort_values("item_revenue", ascending=False).head(10)

        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
        st.markdown(section_header("Top 10 Products by Revenue", "", "#3266AD"), unsafe_allow_html=True)

        rows = []
        for i, (_, row) in enumerate(df_top.iterrows(), 1):
            name = str(row["item_name"])[:55] + ("..." if len(str(row["item_name"])) > 55 else "")
            views = safe_num(row.get("items_viewed", 0))
            carts = safe_num(row.get("items_added_to_cart", 0))
            cart_r = carts / views * 100 if views > 0 else 0
            badge_cls = "badge-green" if cart_r > 8 else "badge-amber" if cart_r > 4 else "badge-red"
            rows.append(f"""
            <tr>
              <td style="color:#9A9A8E">{i}</td>
              <td>{name}</td>
              <td><b style="color:#1D9E75">{fmt_currency(row['item_revenue'])}</b></td>
              <td>{int(row['items_purchased'])}</td>
              <td>{fmt_number(views)}</td>
              <td><span class="badge {badge_cls}">{cart_r:.1f}%</span></td>
            </tr>""")

        st.markdown(f"""
        <table class="styled-table">
          <thead><tr><th>#</th><th>Product</th><th>Revenue</th><th>Units</th><th>Views</th><th>Cart%</th></tr></thead>
          <tbody>{''.join(rows)}</tbody>
        </table>""", unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════
# ── CAMPAIGNS TAB ────────────────────────────────────────
# ═════════════════════════════════════════════════════════
elif active_tab == "Campaigns":
    st.markdown(section_header("Campaigns Performance", "Google Ads Analysis", "#3266AD"), unsafe_allow_html=True)

    if not df_cp.empty and "session_google_ads_campaign_name" in df_cp.columns:
        for col in ["sessions", "purchase_revenue", "transactions", "add_to_carts", "checkouts"]:
            if col in df_cp.columns:
                df_cp[col] = df_cp[col].apply(safe_num)

        df_paid = df_cp[
            df_cp["session_google_ads_campaign_name"].notna() &
            (df_cp["session_google_ads_campaign_name"] != "(not set)") &
            (df_cp["sessions"] > 100)
        ].copy()
        df_paid["cvr"] = df_paid.apply(
            lambda r: r["transactions"] / r["sessions"] * 100 if r["sessions"] > 0 else 0, axis=1)
        df_paid["rps"] = df_paid.apply(
            lambda r: r["purchase_revenue"] / r["sessions"] if r["sessions"] > 0 else 0, axis=1)
        df_paid = df_paid.sort_values("purchase_revenue", ascending=False)

        # KPIs
        best = df_paid.loc[df_paid["purchase_revenue"].idxmax()] if not df_paid.empty else None
        worst = df_paid.loc[df_paid["cvr"].idxmin()] if not df_paid.empty else None
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(kpi_card("Best Campaign", best["session_google_ads_campaign_name"].split("-")[-1] if best is not None else "—", fmt_currency(best["purchase_revenue"]) if best is not None else "—", "up", accent_color="#3266AD"), unsafe_allow_html=True)
        with c2:
            best_cvr = df_paid.loc[df_paid["cvr"].idxmax()] if not df_paid.empty else None
            st.markdown(kpi_card("Highest CVR", best_cvr["session_google_ads_campaign_name"].split("-")[-1] if best_cvr is not None else "—", fmt_pct(best_cvr["cvr"], 2) if best_cvr is not None else "—", "up", accent_color="#1D9E75"), unsafe_allow_html=True)
        with c3:
            st.markdown(kpi_card("Total Paid Sessions", fmt_number(df_paid["sessions"].sum()), "Google Ads campaigns", "neu", accent_color="#7F77DD"), unsafe_allow_html=True)
        with c4:
            st.markdown(kpi_card("Worst CVR", worst["session_google_ads_campaign_name"].split("-")[-1] if worst is not None else "—", fmt_pct(worst["cvr"], 2) if worst is not None else "—", "down", accent_color="#D85A30"), unsafe_allow_html=True)

        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

        # RPS chart
        col_l, col_r = st.columns(2)
        with col_l:
            st.markdown(section_header("Revenue per Session", "Campaign Efficiency", "#EF9F27"), unsafe_allow_html=True)
            df_rps = df_paid.sort_values("rps", ascending=False).head(10)
            max_rps = df_rps["rps"].max()
            for _, row in df_rps.iterrows():
                pct = row["rps"] / max_rps * 100 if max_rps else 0
                col = "#1D9E75" if pct > 70 else "#EF9F27" if pct > 30 else "#D85A30"
                name = str(row["session_google_ads_campaign_name"])[-28:]
                st.markdown(bar_html(name, pct, col, fmt_currency(row["rps"], 1)), unsafe_allow_html=True)

        with col_r:
            st.markdown(section_header("Sessions vs Revenue", "Bubble View", "#3266AD"), unsafe_allow_html=True)
            fig = px.scatter(
                df_paid.head(12),
                x="sessions", y="purchase_revenue",
                size="transactions", color="cvr",
                hover_name="session_google_ads_campaign_name",
                color_continuous_scale=["#D85A30", "#EF9F27", "#1D9E75"],
                size_max=40,
                labels={"sessions": "Sessions", "purchase_revenue": "Revenue (ج)", "cvr": "CVR %"},
            )
            fig.update_layout(**PLOT_LAYOUT, height=280,
                              coloraxis_colorbar=dict(title="CVR%", tickfont=dict(size=10)))
            st.plotly_chart(fig, use_container_width=True)

        # Full table
        st.markdown(section_header("All Campaigns — Full Analysis", "", "#2A3050"), unsafe_allow_html=True)
        rows = []
        for _, row in df_paid.iterrows():
            cvr_val = row["cvr"]
            if cvr_val >= 1.5:
                badge = '<span class="badge badge-green">الأقوى</span>'
            elif cvr_val >= 0.8:
                badge = '<span class="badge badge-blue">جيد</span>'
            elif cvr_val >= 0.3:
                badge = '<span class="badge badge-amber">راجع</span>'
            else:
                badge = '<span class="badge badge-red">ضعيف</span>'
            name = str(row["session_google_ads_campaign_name"])
            rows.append(f"""
            <tr>
              <td style="font-size:11px">{name}</td>
              <td>{fmt_number(row['sessions'])}</td>
              <td><b style="color:#1D9E75">{fmt_currency(row['purchase_revenue'])}</b></td>
              <td>{int(row['transactions'])}</td>
              <td><b style="color:{'#1D9E75' if cvr_val>=1 else '#EF9F27' if cvr_val>=0.5 else '#D85A30'}">{fmt_pct(cvr_val,2)}</b></td>
              <td>{fmt_currency(row['rps'],1)}</td>
              <td>{badge}</td>
            </tr>""")

        st.markdown(f"""
        <table class="styled-table">
          <thead><tr><th>Campaign</th><th>Sessions</th><th>Revenue</th><th>Orders</th><th>CVR</th><th>Rev/Ses</th><th>Rating</th></tr></thead>
          <tbody>{''.join(rows)}</tbody>
        </table>""", unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════
# ── INSIGHTS TAB ─────────────────────────────────────────
# ═════════════════════════════════════════════════════════
elif active_tab == "Insights":
    st.markdown(section_header("Strategic Insights & Action Plan", "Prioritized Recommendations", "#D85A30"), unsafe_allow_html=True)

    st.markdown("### 🔴 P1 — فوري (هذا الأسبوع)")
    st.markdown(insight("🔴", f"Cart Abandonment {cart_abandon:.1f}%",
        f"من {fmt_number(tot_carts)} add-to-cart، بس {fmt_number(tot_orders)} اشتروا. "
        "Abandoned Cart Email Series + Exit-intent popup = ممكن ترفع revenue 15-20%.", "insight-red"), unsafe_allow_html=True)

    if avg_bounce > 55:
        st.markdown(insight("🔴", f"Bounce Rate مرتفع جداً {avg_bounce:.1f}%",
            "الـ Bounce Rate فوق المقبول بشكل كبير. راجع الـ Landing Pages وسرعة التحميل فوراً.", "insight-red"), unsafe_allow_html=True)

    if not df_cp.empty and "session_google_ads_campaign_name" in df_cp.columns:
        for col in ["sessions", "purchase_revenue", "transactions"]:
            if col in df_cp.columns:
                df_cp[col] = df_cp[col].apply(safe_num)
        weak = df_cp[
            (df_cp["sessions"] > 50000) &
            (df_cp["session_google_ads_campaign_name"] != "(not set)") &
            (df_cp["transactions"] / df_cp["sessions"].replace(0, 1) < 0.002)
        ]
        for _, row in weak.head(2).iterrows():
            _cvr = row["transactions"] / row["sessions"] * 100 if row["sessions"] > 0 else 0
            st.markdown(insight("🔴", f"Campaign ضعيف جداً: {row['session_google_ads_campaign_name']}",
                f"{fmt_number(row['sessions'])} session بـ CVR {_cvr:.2f}% فقط. راجع الـ targeting والـ landing pages فوراً.", "insight-red"), unsafe_allow_html=True)

    st.markdown("### ⚠ P2 — مهم (هذا الشهر)")

    if not df_dv.empty and "devicecategory" in df_dv.columns:
        df_dv_c = df_dv.copy()
        df_dv_c["bounce_rate"] = df_dv_c["bounce_rate"].apply(safe_num)
        desktop = df_dv_c[df_dv_c["devicecategory"] == "desktop"]
        mobile  = df_dv_c[df_dv_c["devicecategory"] == "mobile"]
        if not desktop.empty and not mobile.empty:
            d_br = desktop["bounce_rate"].mean() * 100
            m_br = mobile["bounce_rate"].mean() * 100
            if d_br > m_br + 5:
                st.markdown(insight("⚠", f"Bounce Rate Desktop أعلى بـ {d_br-m_br:.1f}% من Mobile",
                    f"Desktop: {d_br:.1f}% vs Mobile: {m_br:.1f}%. تحسين الـ Desktop UX ممكن يضيف إيرادات كبيرة.", "insight-amber"), unsafe_allow_html=True)

    if not df_ch.empty and "session_default_channel_group" in df_ch.columns:
        df_ch_c = df_ch.copy()
        for col in ["sessions", "purchase_revenue", "transactions"]:
            if col in df_ch_c.columns:
                df_ch_c[col] = df_ch_c[col].apply(safe_num)
        paid_s = df_ch_c[df_ch_c["session_default_channel_group"] == "Paid Social"]
        paid_q = df_ch_c[df_ch_c["session_default_channel_group"] == "Paid Search"]
        if not paid_s.empty and not paid_q.empty:
            ps_cvr = paid_s["transactions"].sum() / paid_s["sessions"].sum() * 100 if paid_s["sessions"].sum() > 0 else 0
            pq_cvr = paid_q["transactions"].sum() / paid_q["sessions"].sum() * 100 if paid_q["sessions"].sum() > 0 else 0
            if pq_cvr > ps_cvr * 1.5:
                st.markdown(insight("⚠", f"Paid Search CVR ({pq_cvr:.2f}%) أعلى بكتير من Paid Social ({ps_cvr:.2f}%)",
                    "إعادة توزيع جزء من الـ Paid Social budget لـ Paid Search ممكن يحسن الـ ROAS بشكل كبير.", "insight-amber"), unsafe_allow_html=True)

    st.markdown("### ✅ P3 — فرص نمو (هذا الربع)")

    if not df_nr.empty and "new_vs_returning" in df_nr.columns:
        df_nr_c = df_nr.copy()
        for col in ["sessions", "purchase_revenue", "transactions"]:
            if col in df_nr_c.columns:
                df_nr_c[col] = df_nr_c[col].apply(safe_num)
        ret = df_nr_c[df_nr_c["new_vs_returning"] == "returning"]
        if not ret.empty:
            ret_rev_pct = ret["purchase_revenue"].sum() / tot_revenue * 100 if tot_revenue else 0
            st.markdown(insight("✅", f"Returning Users = {ret_rev_pct:.1f}% من الإيرادات",
                "الـ brand loyalty قوية. Loyalty Program + Personalized offers للـ returning users = رفع LTV.", "insight-green"), unsafe_allow_html=True)

    st.markdown(insight("✅", f"AOV مرتفع {fmt_currency(aov, 0)}",
        "High-ticket customers موجودين. Installment plans مع messaging واضح = رفع CVR بشكل ملحوظ.", "insight-green"), unsafe_allow_html=True)

    st.markdown(insight("▲", "Cart Rate مرتفع — Checkout Rate منخفض",
        f"Cart: {fmt_number(tot_carts)} → Checkout: {fmt_number(tot_checkouts)} → Purchase: {fmt_number(tot_orders)}. "
        "الناس مهتمة بالمنتجات بس بتوقف قبل الدفع. Streamline الـ checkout = quick win.", "insight-blue"), unsafe_allow_html=True)

    # Summary metrics
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    st.markdown(section_header("Summary Metrics", "", "#2A3050"), unsafe_allow_html=True)

    summary_data = {
        "Metric": ["Total Sessions", "Total Revenue", "Total Orders", "AOV", "CVR", "Bounce Rate", "Cart Abandonment", "Avg Session Duration"],
        "Value": [fmt_number(tot_sessions), fmt_currency(tot_revenue), fmt_number(tot_orders),
                  fmt_currency(aov, 0), fmt_pct(cvr, 2), fmt_pct(avg_bounce),
                  fmt_pct(cart_abandon), f"{avg_session_m}:{avg_session_s:02d} min"],
        "Status": ["✅", "✅", "✅", "✅",
                   "⚠" if cvr < 1 else "✅",
                   "⚠" if avg_bounce > 50 else "✅",
                   "🔴" if cart_abandon > 85 else "⚠",
                   "✅"],
    }
    st.dataframe(pd.DataFrame(summary_data), use_container_width=True, hide_index=True)
