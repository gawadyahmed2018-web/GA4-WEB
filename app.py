import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import requests

# ── WINDSOR HELPERS (inline) ─────────────────────────────
WINDSOR_KEY = "07860593d1fd31be68db99f090568a1202be"
WINDSOR_BASE = "https://connectors.windsor.ai/googleanalytics4"

def _preset_to_dates(preset):
    from datetime import date, timedelta
    today = date.today()
    mapping = {
        "last_7d":    (today - timedelta(days=7),  today - timedelta(days=1)),
        "last_14d":   (today - timedelta(days=14), today - timedelta(days=1)),
        "last_30d":   (today - timedelta(days=30), today - timedelta(days=1)),
        "last_90d":   (today - timedelta(days=90), today - timedelta(days=1)),
        "this_month": (today.replace(day=1),        today - timedelta(days=1)),
        "last_month": ((today.replace(day=1) - timedelta(days=1)).replace(day=1),
                       today.replace(day=1) - timedelta(days=1)),
    }
    df, dt = mapping.get(preset, (today - timedelta(days=30), today - timedelta(days=1)))
    return str(df), str(dt)

def get_windsor_data(fields, date_preset="last_30d", date_from=None, date_to=None, timeout=30):
    if not date_from or not date_to:
        date_from, date_to = _preset_to_dates(date_preset)
    params = {
        "api_key":   WINDSOR_KEY,
        "fields":    ",".join(fields),
        "date_from": str(date_from),
        "date_to":   str(date_to),
    }
    try:
        r = requests.get(WINDSOR_BASE, params=params, timeout=timeout)
        r.raise_for_status()
        data = r.json()
        rows = data["data"] if isinstance(data, dict) and "data" in data else (data if isinstance(data, list) else [])
        return pd.DataFrame(rows) if rows else pd.DataFrame()
    except Exception as e:
        st.error(f"Windsor API Error: {e}")
        return pd.DataFrame()

def safe_num(val, default=0):
    try: return float(val) if val is not None else default
    except: return default

def fmt_currency(val, decimals=1):
    v = safe_num(val)
    if v >= 1_000_000: return f"{v/1_000_000:.{decimals}f}M ج"
    elif v >= 1_000:   return f"{v/1_000:.{decimals}f}K ج"
    return f"{v:,.0f} ج"

def fmt_number(val, decimals=0):
    v = safe_num(val)
    if v >= 1_000_000: return f"{v/1_000_000:.1f}M"
    elif v >= 1_000:   return f"{v/1_000:.1f}K"
    return f"{v:,.{decimals}f}"

def fmt_pct(val, decimals=1): return f"{safe_num(val):.{decimals}f}%"

# ── PAGE CONFIG ───────────────────────────────────────────
st.set_page_config(page_title="Raneen Analytics", page_icon="📊", layout="wide", initial_sidebar_state="expanded")

# ── CSS ───────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@300;400;500;600&display=swap');
html, body, [class*="css"] { font-family: 'IBM Plex Sans Arabic', sans-serif; }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 1.2rem 2rem 2rem; max-width: 1400px; }
section[data-testid="stSidebar"] { background: #F5F7FA; border-right: 1px solid #E2E6EA; }
section[data-testid="stSidebar"] .stSelectbox label,
section[data-testid="stSidebar"] .stTextInput label { color: #73726C !important; font-size: 12px; font-weight: 500; text-transform: uppercase; letter-spacing: .05em; }
.kpi-card { background: #FFFFFF; border: 1px solid #E2E6EA; border-radius: 12px; padding: 18px 20px; position: relative; overflow: hidden; transition: border-color .2s; }
.kpi-card:hover { border-color: #3266AD; }
.kpi-accent { position: absolute; top: 0; left: 0; right: 0; height: 3px; border-radius: 12px 12px 0 0; }
.kpi-label { font-size: 11px; color: #73726C; font-weight: 500; text-transform: uppercase; letter-spacing: .06em; margin-bottom: 8px; }
.kpi-value { font-size: 26px; font-weight: 600; color: #1A1A2E; line-height: 1; margin-bottom: 6px; }
.kpi-change { font-size: 12px; } .kpi-sub { font-size: 11px; color: #9A9A8E; margin-top: 2px; }
.up { color: #1D9E75; } .down { color: #D85A30; } .warn { color: #EF9F27; } .neu { color: #888780; }
.section-header { display: flex; align-items: center; gap: 10px; padding: 6px 0 10px; border-bottom: 1px solid #E2E6EA; margin-bottom: 16px; }
.section-dot { width: 8px; height: 8px; border-radius: 50%; }
.section-title { font-size: 15px; font-weight: 600; color: #1A1A2E; }
.section-sub { font-size: 11px; color: #73726C; margin-left: auto; }
.insight-card { border-radius: 8px; padding: 12px 14px; margin-bottom: 8px; font-size: 13px; line-height: 1.6; border-left: 4px solid; }
.insight-red    { background: #FEF3EF; border-color: #D85A30; color: #A33A15; }
.insight-amber  { background: #FEF9EF; border-color: #EF9F27; color: #8A5A10; }
.insight-green  { background: #EAF7F2; border-color: #1D9E75; color: #0D6B4F; }
.insight-blue   { background: #EAF0FB; border-color: #3266AD; color: #1A4A8A; }
.top-bar { display: flex; align-items: center; justify-content: space-between; padding: 10px 0 16px; border-bottom: 1px solid #E2E6EA; margin-bottom: 20px; }
.brand-name { font-size: 22px; font-weight: 700; color: #1A1A2E; } .brand-name span { color: #3266AD; }
.live-badge { display: inline-flex; align-items: center; gap: 6px; background: #EAF7F2; border: 1px solid rgba(29,158,117,.4); border-radius: 20px; padding: 4px 12px; font-size: 11px; font-weight: 500; color: #1D9E75; }
.live-dot { width: 6px; height: 6px; border-radius: 50%; background: #1D9E75; animation: blink 2s ease-in-out infinite; display: inline-block; }
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:.3} }
.funnel-row { display: flex; align-items: center; gap: 12px; margin-bottom: 10px; }
.funnel-label { font-size: 12px; color: #73726C; min-width: 120px; }
.funnel-track { flex: 1; height: 28px; background: #F0F2F5; border-radius: 4px; overflow: hidden; }
.funnel-fill { height: 100%; border-radius: 4px; display: flex; align-items: center; padding-left: 10px; font-size: 11px; font-weight: 600; color: #fff; }
.funnel-pct { font-size: 12px; min-width: 45px; text-align: right; font-weight: 600; }
.bar-row { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }
.bar-name { font-size: 12px; color: #73726C; min-width: 130px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.bar-track { flex: 1; height: 8px; background: #F0F2F5; border-radius: 4px; overflow: hidden; }
.bar-fill  { height: 100%; border-radius: 4px; }
.bar-val   { font-size: 12px; color: #1A1A2E; min-width: 70px; text-align: right; font-weight: 500; }
.styled-table { width: 100%; border-collapse: collapse; font-size: 12px; }
.styled-table th { background: #F5F7FA; color: #73726C; font-weight: 500; font-size: 11px; text-transform: uppercase; letter-spacing: .05em; padding: 8px 10px; border-bottom: 1px solid #E2E6EA; text-align: left; }
.styled-table td { padding: 9px 10px; border-bottom: 1px solid #F0F2F5; color: #1A1A2E; vertical-align: middle; }
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

PLOT_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="IBM Plex Sans Arabic", color="#73726C", size=11),
    margin=dict(l=0, r=0, t=10, b=0),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=11), bgcolor="rgba(0,0,0,0)"),
    xaxis=dict(gridcolor="#E8EDF2", linecolor="#D0D5DD", tickfont=dict(size=10)),
    yaxis=dict(gridcolor="#E8EDF2", linecolor="#D0D5DD", tickfont=dict(size=10)),
)

# ── SIDEBAR ───────────────────────────────────────────────
with st.sidebar:
    st.markdown("""<div style="padding:16px 0 20px">
      <div style="font-size:18px;font-weight:700;color:#1A1A2E"><span style="color:#3266AD">●</span> Raneen</div>
      <div style="font-size:11px;color:#73726C;margin-top:4px">Analytics Dashboard</div>
    </div>""", unsafe_allow_html=True)
    st.success("✅ Connected to GA4", icon="📊")
    st.markdown("---")
    date_preset = st.selectbox("Date Range",
        ["last_30d","last_7d","last_14d","last_90d","this_month","last_month","custom"],
        format_func=lambda x: {"last_7d":"Last 7 Days","last_14d":"Last 14 Days","last_30d":"Last 30 Days","last_90d":"Last 90 Days","this_month":"This Month","last_month":"Last Month","custom":"Custom Range"}.get(x,x))
    if date_preset == "custom":
        from datetime import date, timedelta
        custom_from = st.date_input("From", date.today() - timedelta(days=30))
        custom_to   = st.date_input("To",   date.today() - timedelta(days=1))
    st.markdown("---")
    active_tab = st.radio("Section",
        ["Overview","Funnel","Traffic","Devices","E-Commerce","Campaigns","Users","Insights"],
        label_visibility="collapsed")
    st.markdown("---")
    st.markdown('<div style="font-size:10px;color:#9A9A8E;line-height:1.6">Data source: Google Analytics 4<br>via Windsor.ai<br><span style="color:#1D9E75">● Live</span> — refreshes on load</div>', unsafe_allow_html=True)

# ── TOP BAR ───────────────────────────────────────────────
st.markdown("""<div class="top-bar">
  <div class="brand-name"><span>Raneen</span>.com Analytics</div>
  <div class="live-badge"><span class="live-dot"></span> Live via Windsor · GA4</div>
</div>""", unsafe_allow_html=True)

# ── LOAD DATA ─────────────────────────────────────────────
@st.cache_data(ttl=300, show_spinner=False)
def load_overview(preset, d_from=None, d_to=None):
    df1 = get_windsor_data(["date","sessions","active_users","bounce_rate","average_session_duration"], preset, d_from, d_to)
    df2 = get_windsor_data(["date","purchase_revenue","transactions","add_to_carts","checkouts"], preset, d_from, d_to)
    if df1.empty and df2.empty: return pd.DataFrame()
    if df1.empty: return df2
    if df2.empty: return df1
    try: return pd.merge(df1, df2, on="date", how="outer")
    except: return df1

@st.cache_data(ttl=300, show_spinner=False)
def load_channels(preset, d_from=None, d_to=None):
    df1 = get_windsor_data(["session_default_channel_group","sessions"], preset, d_from, d_to)
    df2 = get_windsor_data(["session_default_channel_group","purchase_revenue","transactions","add_to_carts","checkouts"], preset, d_from, d_to)
    if df1.empty and df2.empty: return pd.DataFrame()
    if df1.empty: return df2
    if df2.empty: return df1
    try: return pd.merge(df1, df2, on="session_default_channel_group", how="outer")
    except: return df1

@st.cache_data(ttl=300, show_spinner=False)
def load_devices(preset, d_from=None, d_to=None):
    df1 = get_windsor_data(["devicecategory","sessions","bounce_rate","engagement_rate"], preset, d_from, d_to)
    df2 = get_windsor_data(["devicecategory","purchase_revenue","transactions"], preset, d_from, d_to)
    if df1.empty and df2.empty: return pd.DataFrame()
    if df1.empty: return df2
    if df2.empty: return df1
    try: return pd.merge(df1, df2, on="devicecategory", how="outer")
    except: return df1

@st.cache_data(ttl=300, show_spinner=False)
def load_new_returning(preset, d_from=None, d_to=None):
    df1 = get_windsor_data(["new_vs_returning","sessions","active_users"], preset, d_from, d_to)
    df2 = get_windsor_data(["new_vs_returning","purchase_revenue","transactions"], preset, d_from, d_to)
    if df1.empty and df2.empty: return pd.DataFrame()
    if df1.empty: return df2
    if df2.empty: return df1
    try: return pd.merge(df1, df2, on="new_vs_returning", how="outer")
    except: return df1

@st.cache_data(ttl=300, show_spinner=False)
def load_campaigns(preset, d_from=None, d_to=None):
    df1 = get_windsor_data(["session_google_ads_campaign_name","sessions"], preset, d_from, d_to)
    df2 = get_windsor_data(["session_google_ads_campaign_name","purchase_revenue","transactions","add_to_carts","checkouts"], preset, d_from, d_to)
    if df1.empty and df2.empty: return pd.DataFrame()
    if df1.empty: return df2
    if df2.empty: return df1
    try: return pd.merge(df1, df2, on="session_google_ads_campaign_name", how="outer")
    except: return df1

@st.cache_data(ttl=300, show_spinner=False)
def load_categories(preset, d_from=None, d_to=None):
    return get_windsor_data(["item_category","gross_item_revenue","items_purchased","items_viewed","items_added_to_cart"], preset, d_from, d_to)

@st.cache_data(ttl=300, show_spinner=False)
def load_products(preset, d_from=None, d_to=None):
    return get_windsor_data(["item_name","item_revenue","items_purchased","items_viewed","items_added_to_cart"], preset, d_from, d_to)

@st.cache_data(ttl=300, show_spinner=False)
def load_subcategory(preset, d_from=None, d_to=None):
    return get_windsor_data(["item_category","item_category2","gross_item_revenue","items_purchased","items_viewed","items_added_to_cart"], preset, d_from, d_to)

@st.cache_data(ttl=300, show_spinner=False)
def load_campaign_products(preset, d_from=None, d_to=None):
    return get_windsor_data(["session_google_ads_campaign_name","item_name","item_revenue","items_purchased"], preset, d_from, d_to)

@st.cache_data(ttl=300, show_spinner=False)
def load_meta_campaigns(preset, d_from=None, d_to=None):
    """Meta campaigns via UTM — session_manual_campaign_name."""
    return get_windsor_data([
        "session_manual_campaign_name",
        "sessions","purchase_revenue","transactions","add_to_carts"
    ], preset, d_from, d_to)

@st.cache_data(ttl=300, show_spinner=False)
def load_landing_pages(preset, d_from=None, d_to=None):
    """Landing pages — try page_path and landing_page fields."""
    for dim in ["landing_page", "page_path", "page_title"]:
        df = get_windsor_data([dim,"sessions","purchase_revenue","transactions","bounce_rate","add_to_carts"], preset, d_from, d_to, timeout=60)
        if not df.empty and "sessions" in df.columns:
            df = df.rename(columns={dim: "landing_page"})
            return df
    return pd.DataFrame()

@st.cache_data(ttl=300, show_spinner=False)
def load_utm(preset, d_from=None, d_to=None):
    """UTM — try multiple field combinations, return first that works."""
    # Try session_google_ads_campaign_name x channel (already working)
    combos = [
        ["session_default_channel_group","session_google_ads_campaign_name","sessions","purchase_revenue","transactions","bounce_rate"],
        ["session_default_channel_group","sessions","bounce_rate","purchase_revenue","transactions"],
    ]
    for fields in combos:
        df = get_windsor_data(fields, preset, d_from, d_to)
        if not df.empty:
            return df
    return pd.DataFrame()

@st.cache_data(ttl=300, show_spinner=False)
def load_category_funnel(preset, d_from=None, d_to=None):
    """Category funnel: item_category x item_category2 x item_category3 with full funnel metrics."""
    return get_windsor_data([
        "item_category","item_category2","item_category3",
        "gross_item_revenue","items_purchased",
        "items_viewed","items_added_to_cart","item_revenue"
    ], preset, d_from, d_to)

# ── Resolve custom dates ─────────────────────────
if date_preset == "custom":
    _d_from = str(custom_from)
    _d_to   = str(custom_to)
else:
    _d_from, _d_to = None, None

@st.cache_data(ttl=300, show_spinner=False)
def load_users_nr(preset, d_from=None, d_to=None):
    """New vs Returning with full metrics."""
    df1 = get_windsor_data(["new_vs_returning","sessions","active_users","bounce_rate"], preset, d_from, d_to)
    df2 = get_windsor_data(["new_vs_returning","purchase_revenue","transactions","add_to_carts","checkouts"], preset, d_from, d_to)
    if df1.empty and df2.empty: return pd.DataFrame()
    if df1.empty: return df2
    if df2.empty: return df1
    try: return pd.merge(df1, df2, on="new_vs_returning", how="outer")
    except: return df1

@st.cache_data(ttl=300, show_spinner=False)
def load_users_device(preset, d_from=None, d_to=None):
    """Device breakdown with user metrics."""
    df1 = get_windsor_data(["devicecategory","sessions","active_users","bounce_rate","average_session_duration"], preset, d_from, d_to)
    df2 = get_windsor_data(["devicecategory","purchase_revenue","transactions","add_to_carts"], preset, d_from, d_to)
    if df1.empty and df2.empty: return pd.DataFrame()
    if df1.empty: return df2
    if df2.empty: return df1
    try: return pd.merge(df1, df2, on="devicecategory", how="outer")
    except: return df1

@st.cache_data(ttl=300, show_spinner=False)
def load_users_channel(preset, d_from=None, d_to=None):
    """Channel breakdown for user acquisition."""
    df1 = get_windsor_data(["session_default_channel_group","sessions","active_users","bounce_rate"], preset, d_from, d_to)
    df2 = get_windsor_data(["session_default_channel_group","purchase_revenue","transactions"], preset, d_from, d_to)
    if df1.empty and df2.empty: return pd.DataFrame()
    if df1.empty: return df2
    if df2.empty: return df1
    try: return pd.merge(df1, df2, on="session_default_channel_group", how="outer")
    except: return df1

@st.cache_data(ttl=3600, show_spinner=False)
def load_cohort(d_from=None, d_to=None):
    """Monthly cohort: date x new_vs_returning for retention analysis — 90 days."""
    from datetime import date, timedelta
    df_from = d_from or str(date.today() - timedelta(days=90))
    df_to   = d_to   or str(date.today() - timedelta(days=1))
    df1 = get_windsor_data(["date","new_vs_returning","sessions","active_users"], "last_90d", df_from, df_to)
    df2 = get_windsor_data(["date","new_vs_returning","purchase_revenue","transactions"], "last_90d", df_from, df_to)
    if df1.empty and df2.empty: return pd.DataFrame()
    if df1.empty: return df2
    if df2.empty: return df1
    try: return pd.merge(df1, df2, on=["date","new_vs_returning"], how="outer")
    except: return df1

with st.spinner("⏳ Loading GA4 data..."):
    df_ov = load_overview(date_preset, _d_from, _d_to)
    df_ch = load_channels(date_preset, _d_from, _d_to)
    df_dv = load_devices(date_preset, _d_from, _d_to)
    df_nr = load_new_returning(date_preset, _d_from, _d_to)
    df_cp = load_campaigns(date_preset, _d_from, _d_to)

if df_ov.empty:
    st.error("❌ Could not load data. Windsor API error — check logs.")
    st.stop()

# ── TOTALS ────────────────────────────────────────────────
tot_sessions  = safe_num(df_ov["sessions"].sum())                      if "sessions"                  in df_ov else 0
tot_revenue   = safe_num(df_ov["purchase_revenue"].sum())              if "purchase_revenue"          in df_ov else 0
tot_orders    = safe_num(df_ov["transactions"].sum())                  if "transactions"              in df_ov else 0
tot_carts     = safe_num(df_ov["add_to_carts"].sum())                  if "add_to_carts"              in df_ov else 0
tot_checkouts = safe_num(df_ov["checkouts"].sum())                     if "checkouts"                 in df_ov else 0
avg_bounce    = safe_num(df_ov["bounce_rate"].mean()) * 100            if "bounce_rate"               in df_ov else 0
avg_session   = safe_num(df_ov["average_session_duration"].mean())     if "average_session_duration"  in df_ov else 0
aov           = tot_revenue / tot_orders        if tot_orders    > 0 else 0
cvr           = tot_orders  / tot_sessions * 100 if tot_sessions > 0 else 0
cart_abandon  = (1 - tot_orders / tot_carts) * 100 if tot_carts  > 0 else 0
avg_session_m = int(avg_session // 60)
avg_session_s = int(avg_session % 60)

# ── UI HELPERS ────────────────────────────────────────────
def kpi_card(label, value, change_txt, change_cls, sub="", accent_color="#3266AD"):
    return f"""<div class="kpi-card"><div class="kpi-accent" style="background:{accent_color}"></div>
    <div class="kpi-label">{label}</div><div class="kpi-value">{value}</div>
    <div class="kpi-change {change_cls}">{change_txt}</div>
    {'<div class="kpi-sub">'+sub+'</div>' if sub else ''}</div>"""

def section_header(title, sub="", color="#3266AD"):
    return f"""<div class="section-header"><div class="section-dot" style="background:{color}"></div>
    <div class="section-title">{title}</div>
    {'<div class="section-sub">'+sub+'</div>' if sub else ''}</div>"""

def bar_html(name, pct, color, val_str):
    return f"""<div class="bar-row"><div class="bar-name">{name}</div>
    <div class="bar-track"><div class="bar-fill" style="width:{max(pct,1)}%;background:{color}"></div></div>
    <div class="bar-val">{val_str}</div></div>"""

def insight(icon, title, body, cls):
    return f'<div class="insight-card {cls}"><b>{icon} {title}</b><br/>{body}</div>'


# ═══════════════════════════════════════════════════════════
# OVERVIEW
# ═══════════════════════════════════════════════════════════
if active_tab == "Overview":
    st.markdown(section_header("Overview", "Key Performance Indicators", "#3266AD"), unsafe_allow_html=True)
    c1,c2,c3,c4 = st.columns(4)
    with c1: st.markdown(kpi_card("Sessions", fmt_number(tot_sessions), "▲ Live GA4 Data", "up", accent_color="#3266AD"), unsafe_allow_html=True)
    with c2: st.markdown(kpi_card("Revenue", fmt_currency(tot_revenue), "▲ Purchase Revenue", "up", accent_color="#1D9E75"), unsafe_allow_html=True)
    with c3: st.markdown(kpi_card("Orders", fmt_number(tot_orders), "▲ Transactions", "up", accent_color="#1D9E75"), unsafe_allow_html=True)
    with c4: st.markdown(kpi_card("AOV", fmt_currency(aov, 0), "متوسط قيمة الطلب", "neu", accent_color="#3266AD"), unsafe_allow_html=True)
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    c5,c6,c7,c8 = st.columns(4)
    with c5: st.markdown(kpi_card("Add to Cart", fmt_number(tot_carts), f"⚠ Cart Abandon {cart_abandon:.1f}%", "warn", accent_color="#EF9F27"), unsafe_allow_html=True)
    with c6: st.markdown(kpi_card("Bounce Rate", fmt_pct(avg_bounce), "▼ Monitor carefully", "down" if avg_bounce > 50 else "warn", accent_color="#D85A30"), unsafe_allow_html=True)
    with c7: st.markdown(kpi_card("Avg Session", f"{avg_session_m}:{avg_session_s:02d} min", "▲ Engagement", "up", accent_color="#7F77DD"), unsafe_allow_html=True)
    with c8: st.markdown(kpi_card("CVR", fmt_pct(cvr, 2), "⚠ Needs improvement" if cvr < 1 else "▲ Good", "warn" if cvr < 1 else "up", accent_color="#D85A30" if cvr < 1 else "#1D9E75"), unsafe_allow_html=True)
    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    if "date" in df_ov.columns:
        df_ts = df_ov.copy()
        df_ts["date"] = pd.to_datetime(df_ts["date"], errors="coerce")
        df_ts = df_ts.dropna(subset=["date"]).sort_values("date")
        col_l, col_r = st.columns(2)
        with col_l:
            st.markdown(section_header("Revenue Over Time", "", "#1D9E75"), unsafe_allow_html=True)
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            fig.add_trace(go.Bar(x=df_ts["date"], y=df_ts["purchase_revenue"]/1000, name="Revenue K ج", marker_color="#3266AD", opacity=0.8), secondary_y=False)
            fig.add_trace(go.Scatter(x=df_ts["date"], y=df_ts["transactions"], name="Orders", line=dict(color="#1D9E75", width=2), mode="lines+markers", marker_size=4), secondary_y=True)
            fig.update_layout(**PLOT_LAYOUT, height=260)
            st.plotly_chart(fig, use_container_width=True)
        with col_r:
            st.markdown(section_header("Sessions & Bounce Rate", "", "#D85A30"), unsafe_allow_html=True)
            fig2 = make_subplots(specs=[[{"secondary_y": True}]])
            fig2.add_trace(go.Bar(x=df_ts["date"], y=df_ts["sessions"]/1000, name="Sessions K", marker_color="rgba(50,102,173,0.7)"), secondary_y=False)
            if "bounce_rate" in df_ts.columns:
                fig2.add_trace(go.Scatter(x=df_ts["date"], y=df_ts["bounce_rate"]*100, name="Bounce %", line=dict(color="#D85A30", width=2), mode="lines", fill="tozeroy", fillcolor="rgba(216,90,48,0.1)"), secondary_y=True)
            fig2.update_layout(**PLOT_LAYOUT, height=260)
            st.plotly_chart(fig2, use_container_width=True)

    st.markdown(section_header("New vs Returning", "Revenue Split", "#7F77DD"), unsafe_allow_html=True)
    if not df_nr.empty and "new_vs_returning" in df_nr.columns:
        nr = df_nr[df_nr["new_vs_returning"].isin(["new","returning"])].copy()
        for col in ["purchase_revenue","sessions","transactions"]:
            if col in nr.columns: nr[col] = nr[col].apply(safe_num)
        ret = nr[nr["new_vs_returning"]=="returning"]; new = nr[nr["new_vs_returning"]=="new"]
        ret_rev = ret["purchase_revenue"].sum(); new_rev = new["purchase_revenue"].sum()
        tot_r = ret_rev + new_rev; ret_pct = ret_rev/tot_r*100 if tot_r else 0
        c1,c2,c3,c4 = st.columns(4)
        with c1: st.markdown(kpi_card("Returning Sessions", fmt_number(ret["sessions"].sum()), "Loyal customers", "neu", accent_color="#1D9E75"), unsafe_allow_html=True)
        with c2: st.markdown(kpi_card("Returning Revenue", fmt_currency(ret_rev), f"▲ {ret_pct:.1f}% of total", "up", accent_color="#1D9E75"), unsafe_allow_html=True)
        with c3:
            rc = ret["transactions"].sum()/ret["sessions"].sum()*100 if ret["sessions"].sum()>0 else 0
            st.markdown(kpi_card("Returning CVR", fmt_pct(rc, 2), "vs New users", "up", accent_color="#1D9E75"), unsafe_allow_html=True)
        with c4:
            nc = new["transactions"].sum()/new["sessions"].sum()*100 if new["sessions"].sum()>0 else 0
            st.markdown(kpi_card("New Users CVR", fmt_pct(nc, 2), "Lower than returning", "warn", accent_color="#3266AD"), unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════
# FUNNEL
# ═══════════════════════════════════════════════════════════
elif active_tab == "Funnel":
    st.markdown(section_header("Sales Funnel", "Item Views → Purchase", "#3266AD"), unsafe_allow_html=True)

    # Load item views for funnel
    with st.spinner("Loading funnel data..."):
        df_funnel_items = load_categories(date_preset, _d_from, _d_to)

    tot_items_viewed = safe_num(df_funnel_items["items_viewed"].sum()) if not df_funnel_items.empty and "items_viewed" in df_funnel_items.columns else 0
    tot_items_carted = safe_num(df_funnel_items["items_added_to_cart"].sum()) if not df_funnel_items.empty and "items_added_to_cart" in df_funnel_items.columns else 0

    # Use items_viewed as base if available, else sessions
    base_val   = tot_items_viewed if tot_items_viewed > 0 else tot_sessions
    base_label = "Items Viewed" if tot_items_viewed > 0 else "Sessions"

    funnel_steps = [
        (base_label,      base_val,      100.0,                                           "#3266AD"),
        ("Add to Cart",   tot_items_carted if tot_items_carted>0 else tot_carts,
                          (tot_items_carted/base_val*100 if base_val else 0) if tot_items_carted>0 else (tot_carts/base_val*100 if base_val else 0), "#378ADD"),
        ("Checkout Start",tot_checkouts, tot_checkouts/base_val*100 if base_val else 0,   "#85B7EB"),
        ("Purchase",      tot_orders,    tot_orders/base_val*100 if base_val else 0,      "#1D9E75"),
    ]

    for label, count, pct, color in funnel_steps:
        bw = max(pct, 0.5)
        st.markdown(f"""<div class="funnel-row"><div class="funnel-label">{label}</div>
        <div class="funnel-track"><div class="funnel-fill" style="width:{bw}%;background:{color}">
        {'&nbsp;'+fmt_number(count) if bw > 8 else ''}</div></div>
        <div class="funnel-pct" style="color:{color}">{pct:.2f}%</div></div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    c1,c2,c3 = st.columns(3)
    _cart_v = tot_items_carted if tot_items_carted>0 else tot_carts
    view_drop = (1 - _cart_v/base_val)*100 if base_val else 0
    chk_drop  = (1 - tot_checkouts/_cart_v)*100 if _cart_v else 0
    pur_drop  = (1 - tot_orders/tot_checkouts)*100 if tot_checkouts else 0
    with c1: st.markdown(kpi_card("View → Cart",     fmt_pct(100-view_drop,1), f"⚠ {view_drop:.1f}% drop",    "warn", accent_color="#EF9F27"), unsafe_allow_html=True)
    with c2: st.markdown(kpi_card("Cart → Checkout", fmt_pct(100-chk_drop,1),  f"⚠ {chk_drop:.1f}% abandon",  "down", accent_color="#D85A30"), unsafe_allow_html=True)
    with c3: st.markdown(kpi_card("Checkout → Buy",  fmt_pct(100-pur_drop,1),  f"⚠ {pur_drop:.1f}% drop",     "down" if pur_drop>50 else "warn", accent_color="#D85A30"), unsafe_allow_html=True)

    fig = go.Figure(go.Funnel(
        y=[base_label,"Add to Cart","Checkout","Purchase"],
        x=[base_val, _cart_v, tot_checkouts, tot_orders],
        textinfo="value+percent initial",
        marker=dict(color=["#3266AD","#378ADD","#85B7EB","#1D9E75"])))
    fig.update_layout(**PLOT_LAYOUT, height=320)
    st.plotly_chart(fig, use_container_width=True)
    if not df_nr.empty and "new_vs_returning" in df_nr.columns:
        st.markdown(section_header("New vs Returning — Funnel Comparison", "", "#7F77DD"), unsafe_allow_html=True)
        nr = df_nr[df_nr["new_vs_returning"].isin(["new","returning"])].copy()
        for col in ["sessions","purchase_revenue","transactions"]:
            if col in nr.columns: nr[col] = nr[col].apply(safe_num)
        rows=[]
        for seg in ["returning","new"]:
            d=nr[nr["new_vs_returning"]==seg]; ses=d["sessions"].sum(); rev=d["purchase_revenue"].sum(); txn=d["transactions"].sum()
            _cvr=txn/ses*100 if ses>0 else 0; _aov=rev/txn if txn>0 else 0
            bc="badge-green" if seg=="returning" else "badge-blue"; bl=seg.title()
            rows.append(f"<tr><td><span class='badge {bc}'>{bl}</span></td><td>{fmt_number(ses)}</td><td>{fmt_currency(rev)}</td><td>{fmt_number(txn)}</td><td><b style='color:{'#1D9E75' if seg=='returning' else '#EF9F27'}'>{fmt_pct(_cvr,2)}</b></td><td>{fmt_currency(_aov,0)}</td></tr>")
        st.markdown(f"<table class='styled-table'><thead><tr><th>Segment</th><th>Sessions</th><th>Revenue</th><th>Orders</th><th>CVR</th><th>AOV</th></tr></thead><tbody>{''.join(rows)}</tbody></table>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════
# TRAFFIC
# ═══════════════════════════════════════════════════════════
elif active_tab == "Traffic":
    st.markdown(section_header("Traffic Sources", "Sessions & Revenue by Channel", "#3266AD"), unsafe_allow_html=True)
    if not df_ch.empty and "session_default_channel_group" in df_ch.columns:
        for col in ["sessions","purchase_revenue","transactions","add_to_carts"]:
            if col in df_ch.columns: df_ch[col] = df_ch[col].apply(safe_num)
        df_g = df_ch[df_ch["session_default_channel_group"].notna() & (df_ch["session_default_channel_group"]!="")]
        df_g = df_g.groupby("session_default_channel_group").sum(numeric_only=True).reset_index()
        df_g = df_g[df_g["sessions"]>10].sort_values("purchase_revenue", ascending=False)
        COLORS=["#3266AD","#378ADD","#85B7EB","#1D9E75","#5DCAA5","#EF9F27","#888780","#7F77DD"]
        col_l,col_r = st.columns(2)
        with col_l:
            st.markdown("**Sessions by Channel**")
            mx=df_g["sessions"].max()
            for i,(_,r) in enumerate(df_g.head(8).iterrows()): st.markdown(bar_html(r["session_default_channel_group"], r["sessions"]/mx*100 if mx else 0, COLORS[i%len(COLORS)], fmt_number(r["sessions"])), unsafe_allow_html=True)
        with col_r:
            st.markdown("**Revenue by Channel**")
            mx=df_g["purchase_revenue"].max()
            for i,(_,r) in enumerate(df_g.sort_values("purchase_revenue",ascending=False).head(8).iterrows()): st.markdown(bar_html(r["session_default_channel_group"], r["purchase_revenue"]/mx*100 if mx else 0, COLORS[i%len(COLORS)], fmt_currency(r["purchase_revenue"])), unsafe_allow_html=True)
        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
        st.markdown(section_header("Channel Efficiency", "CVR & Revenue per Session", "#EF9F27"), unsafe_allow_html=True)
        rows=[]
        for _,r in df_g.iterrows():
            ses=r["sessions"]; rev=r["purchase_revenue"]; txn=r["transactions"]
            _cvr=txn/ses*100 if ses>0 else 0; rps=rev/ses if ses>0 else 0
            if _cvr>=1.5: badge='<span class="badge badge-green">الأقوى</span>'
            elif _cvr>=0.8: badge='<span class="badge badge-blue">جيد</span>'
            elif _cvr>=0.4: badge='<span class="badge badge-amber">راجع</span>'
            else: badge='<span class="badge badge-red">ضعيف</span>'
            rows.append(f"<tr><td><b>{r['session_default_channel_group']}</b></td><td>{fmt_number(ses)}</td><td>{fmt_currency(rev)}</td><td>{fmt_number(txn)}</td><td><b style='color:{'#1D9E75' if _cvr>=1 else '#EF9F27' if _cvr>=0.5 else '#D85A30'}'>{fmt_pct(_cvr,2)}</b></td><td>{fmt_currency(rps,1)}</td><td>{badge}</td></tr>")
        st.markdown(f"<table class='styled-table'><thead><tr><th>Channel</th><th>Sessions</th><th>Revenue</th><th>Orders</th><th>CVR</th><th>Rev/Session</th><th>Rating</th></tr></thead><tbody>{''.join(rows)}</tbody></table>", unsafe_allow_html=True)

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    # ── UTM SOURCE / MEDIUM ──────────────────────────────────
    st.markdown(section_header("UTM Source & Medium", "أداء الـ Campaigns والبانرات", "#7F77DD"), unsafe_allow_html=True)
    with st.spinner("Loading UTM data..."):
        df_utm = load_utm(date_preset, _d_from, _d_to)

    if not df_utm.empty and "sessions" in df_utm.columns:
        for col in ["sessions","purchase_revenue","transactions","add_to_carts","bounce_rate"]:
            if col in df_utm.columns: df_utm[col] = df_utm[col].apply(safe_num)

        # Determine grouping column
        if "session_google_ads_campaign_name" in df_utm.columns:
            grp = "session_google_ads_campaign_name"
            grp_label = "Campaign"
        elif "session_default_channel_group" in df_utm.columns:
            grp = "session_default_channel_group"
            grp_label = "Channel"
        else:
            grp = df_utm.columns[0]
            grp_label = grp

        df_utm = df_utm[df_utm["sessions"]>5].sort_values("purchase_revenue", ascending=False)

        utm_search = st.text_input("🔍 Search", placeholder="google, facebook, cpc...", key="utm_search")
        if utm_search and grp in df_utm.columns:
            df_utm = df_utm[df_utm[grp].astype(str).str.contains(utm_search, case=False, na=False)]

        utm_rows = []
        for _, r in df_utm.head(30).iterrows():
            ses = r["sessions"]; rev = r["purchase_revenue"]; txn = r["transactions"]
            br  = r["bounce_rate"]*100 if "bounce_rate" in r.index else 0
            _cvr = txn/ses*100 if ses>0 else 0
            rps  = rev/ses if ses>0 else 0
            _aov = rev/txn if txn>0 else 0
            name = str(r.get(grp, "—"))
            if _cvr>=1.5: badge='<span class="badge badge-green">الأقوى</span>'
            elif _cvr>=0.8: badge='<span class="badge badge-blue">جيد</span>'
            elif _cvr>=0.3: badge='<span class="badge badge-amber">راجع</span>'
            else: badge='<span class="badge badge-red">ضعيف</span>'
            utm_rows.append(f"""<tr>
              <td style="font-size:11px"><b>{name}</b></td>
              <td>{fmt_number(ses)}</td>
              <td><b style="color:#1D9E75">{fmt_currency(rev)}</b></td>
              <td>{fmt_number(txn)}</td>
              <td><b style="color:{'#1D9E75' if _cvr>=1 else '#EF9F27' if _cvr>=0.5 else '#D85A30'}">{fmt_pct(_cvr,2)}</b></td>
              <td>{fmt_currency(rps,1)}</td>
              <td>{fmt_currency(_aov,0)}</td>
              <td style="color:{'#D85A30' if br>55 else '#EF9F27' if br>45 else '#1D9E75'}">{fmt_pct(br,1)}</td>
              <td>{badge}</td>
            </tr>""")
        st.markdown(f"""<table class='styled-table'>
          <thead><tr>
            <th>{grp_label}</th><th>Sessions</th><th>Revenue</th><th>Orders</th>
            <th>CVR</th><th>Rev/Ses</th><th>AOV</th><th>Bounce</th><th>Rating</th>
          </tr></thead>
          <tbody>{''.join(utm_rows)}</tbody>
        </table>""", unsafe_allow_html=True)
    else:
        st.info("مفيش بيانات UTM متاحة حالياً.")

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    # ── LANDING PAGES ────────────────────────────────────────
    st.markdown(section_header("Landing Pages Performance", "أداء كل صفحة على الموقع", "#1D9E75"), unsafe_allow_html=True)
    with st.spinner("Loading landing pages data..."):
        df_lp = load_landing_pages(date_preset, _d_from, _d_to)

    if not df_lp.empty and "landing_page" in df_lp.columns:
        for col in ["sessions","purchase_revenue","transactions","add_to_carts","bounce_rate","average_session_duration"]:
            if col in df_lp.columns: df_lp[col] = df_lp[col].apply(safe_num)

        df_lp = df_lp[df_lp["landing_page"].notna() & (df_lp["landing_page"]!="")].copy()
        if "sessions" not in df_lp.columns:
            st.info("مفيش بيانات Landing Pages — الـ field مش متاح في Windsor.")
        else:
            df_lp = df_lp[df_lp["sessions"]>5]

            # Sort options
            lp_col1, lp_col2 = st.columns(2)
            lp_sort = lp_col1.selectbox("Sort by", ["purchase_revenue","sessions","transactions","bounce_rate"], key="lp_sort",
                        format_func=lambda x: {"purchase_revenue":"Revenue","sessions":"Sessions","transactions":"Orders","bounce_rate":"Bounce Rate"}.get(x,x))
            lp_search = lp_col2.text_input("🔍 Search page", placeholder="/category, /product...", key="lp_search")
    
            df_lp_f = df_lp.copy()
            if lp_search:
                df_lp_f = df_lp_f[df_lp_f["landing_page"].str.contains(lp_search, case=False, na=False)]
    
            asc = lp_sort == "bounce_rate"
            df_lp_f = df_lp_f.sort_values(lp_sort, ascending=asc)
    
            # Summary KPIs
            lk1,lk2,lk3,lk4 = st.columns(4)
            with lk1: st.markdown(kpi_card("Total Pages", fmt_number(len(df_lp_f)), "Unique landing pages", "neu", accent_color="#1D9E75"), unsafe_allow_html=True)
            with lk2:
                best_lp = df_lp_f.loc[df_lp_f["purchase_revenue"].idxmax()] if not df_lp_f.empty else None
                st.markdown(kpi_card("Best Revenue Page", str(best_lp["landing_page"])[:30] if best_lp is not None else "—", fmt_currency(best_lp["purchase_revenue"]) if best_lp is not None else "—", "up", accent_color="#1D9E75"), unsafe_allow_html=True)
            with lk3:
                best_cvr_lp = df_lp_f[df_lp_f["transactions"]>0]
                best_cvr_lp = best_cvr_lp.assign(cvr=best_cvr_lp["transactions"]/best_cvr_lp["sessions"]*100)
                bc_row = best_cvr_lp.loc[best_cvr_lp["cvr"].idxmax()] if not best_cvr_lp.empty else None
                st.markdown(kpi_card("Best CVR Page", str(bc_row["landing_page"])[:30] if bc_row is not None else "—", fmt_pct(bc_row["cvr"],2) if bc_row is not None else "—", "up", accent_color="#3266AD"), unsafe_allow_html=True)
            with lk4:
                avg_lp_bounce = df_lp_f["bounce_rate"].mean()*100 if "bounce_rate" in df_lp_f.columns else 0
                st.markdown(kpi_card("Avg Bounce Rate", fmt_pct(avg_lp_bounce,1), "عبر كل الصفحات", "dn" if avg_lp_bounce>55 else "wn", accent_color="#D85A30"), unsafe_allow_html=True)
    
            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    
            lp_rows = []
            for _, r in df_lp_f.head(50).iterrows():
                ses  = r["sessions"]; rev = r["purchase_revenue"]; txn = r["transactions"]
                br   = r["bounce_rate"]*100 if "bounce_rate" in r.index else 0
                asd  = r.get("average_session_duration", 0)
                m_   = int(asd//60); s_ = int(asd%60)
                _cvr = txn/ses*100 if ses>0 else 0
                rps  = rev/ses if ses>0 else 0
                crt  = r.get("add_to_carts", 0)
                c2c  = crt/ses*100 if ses>0 else 0
    
                # Page type detection
                pg = str(r["landing_page"])
                if pg == "/" or pg == "": pg_type = "🏠 Home"
                elif "/category" in pg or "/cat" in pg: pg_type = "📂 Category"
                elif "/product" in pg or "/p/" in pg: pg_type = "🛍️ Product"
                elif "/cart" in pg: pg_type = "🛒 Cart"
                elif "/search" in pg: pg_type = "🔍 Search"
                elif "/brand" in pg: pg_type = "🏷️ Brand"
                else: pg_type = "📄 Page"
    
                br_color = "#D85A30" if br>65 else "#EF9F27" if br>50 else "#1D9E75"
                lp_rows.append(f"""<tr>
                  <td style="font-size:10px;max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">
                    <span style="font-size:9px;color:#9A9A8E">{pg_type}</span><br>
                    <b title="{pg}">{pg[:60]}{"..." if len(pg)>60 else ""}</b>
                  </td>
                  <td>{fmt_number(ses)}</td>
                  <td><b style="color:#1D9E75">{fmt_currency(rev)}</b></td>
                  <td>{fmt_number(txn)}</td>
                  <td><b style="color:{'#1D9E75' if _cvr>=1 else '#EF9F27' if _cvr>=0.3 else '#D85A30'}">{fmt_pct(_cvr,2)}</b></td>
                  <td>{fmt_pct(c2c,1)}</td>
                  <td>{fmt_currency(rps,1)}</td>
                  <td style="color:{br_color}">{fmt_pct(br,1)}</td>
                  <td>{m_}:{s_:02d}</td>
                </tr>""")
    
            st.markdown(f"""<table class='styled-table'>
              <thead><tr>
                <th>Landing Page</th><th>Sessions</th><th>Revenue</th><th>Orders</th>
                <th>CVR</th><th>Cart%</th><th>Rev/Ses</th><th>Bounce</th><th>Avg Time</th>
              </tr></thead>
              <tbody>{''.join(lp_rows)}</tbody>
            </table>""", unsafe_allow_html=True)
            st.caption(f"Showing top 50 of {len(df_lp_f)} pages")
    else:
        st.info("مفيش بيانات Landing Pages — تأكد إن الـ landing_page field متاح في Windsor.")

# ═══════════════════════════════════════════════════════════
# DEVICES
# ═══════════════════════════════════════════════════════════
elif active_tab == "Devices":
    st.markdown(section_header("Device Performance", "Mobile vs Desktop vs Tablet", "#7F77DD"), unsafe_allow_html=True)
    if not df_dv.empty and "devicecategory" in df_dv.columns:
        for col in ["sessions","purchase_revenue","transactions","bounce_rate"]:
            if col in df_dv.columns: df_dv[col] = df_dv[col].apply(safe_num)
        DC={"mobile":"#3266AD","desktop":"#888780","tablet":"#1D9E75"}
        md=df_dv[df_dv["devicecategory"].isin(["mobile","desktop","tablet"])]
        cols=st.columns(len(md))
        for i,(_,r) in enumerate(md.iterrows()):
            dev=r["devicecategory"]; c=DC.get(dev,"#888780"); br=r["bounce_rate"]*100
            sp=r["sessions"]/md["sessions"].sum()*100 if md["sessions"].sum()>0 else 0
            with cols[i]: st.markdown(kpi_card(dev.title(), f"{sp:.1f}%", f"Bounce: {br:.1f}%", "down" if br>55 else "warn" if br>45 else "up", f"Sessions: {fmt_number(r['sessions'])} · Rev: {fmt_currency(r['purchase_revenue'])}", accent_color=c), unsafe_allow_html=True)
        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
        col_l,col_r = st.columns(2)
        with col_l:
            st.markdown(section_header("Revenue Split", "", "#1D9E75"), unsafe_allow_html=True)
            fig=go.Figure(go.Pie(labels=md["devicecategory"].str.title(), values=md["purchase_revenue"], marker_colors=[DC.get(d,"#888780") for d in md["devicecategory"]], hole=0.6, textinfo="label+percent", textfont_size=11))
            fig.update_layout(**PLOT_LAYOUT, height=260); st.plotly_chart(fig, use_container_width=True)
        with col_r:
            st.markdown(section_header("Bounce Rate by Device", "", "#D85A30"), unsafe_allow_html=True)
            fig2=go.Figure(go.Bar(x=md["devicecategory"].str.title(), y=md["bounce_rate"]*100, marker_color=[DC.get(d,"#888780") for d in md["devicecategory"]], text=[f"{r*100:.1f}%" for r in md["bounce_rate"]], textposition="outside"))
            fig2.update_layout(**PLOT_LAYOUT, height=260, yaxis=dict(ticksuffix="%",range=[0,80],gridcolor="#E8EDF2")); st.plotly_chart(fig2, use_container_width=True)

# ═══════════════════════════════════════════════════════════
# E-COMMERCE
# ═══════════════════════════════════════════════════════════
elif active_tab == "E-Commerce":
    st.markdown(section_header("E-Commerce Insights", "Products & Categories", "#1D9E75"), unsafe_allow_html=True)
    with st.spinner("Loading e-commerce data..."):
        df_cat = load_categories(date_preset, _d_from, _d_to)
        df_prod = load_products(date_preset, _d_from, _d_to)
        df_sub = load_subcategory(date_preset, _d_from, _d_to)
    RANEEN_CATS=["الأجهزة المنزلية","الأثاث","الإلكترونيات","المطبخ","موبايلات","المفروشات","عروض رنين","المنزل","المنتجات العائلية","الأزياء و الموضة"]
    CAT_ICONS={"الأجهزة المنزلية":"🏠","الأثاث":"🛋️","الإلكترونيات":"📺","المطبخ":"🍳","موبايلات":"📱","المفروشات":"🛏️","عروض رنين":"🏷️","المنزل":"🪴","المنتجات العائلية":"👨‍👩‍👧","الأزياء و الموضة":"👗"}
    CAT_COLORS=["#3266AD","#378ADD","#85B7EB","#1D9E75","#5DCAA5","#EF9F27","#7F77DD","#D85A30","#888780","#B5D4F4"]
    if not df_cat.empty and "item_category" in df_cat.columns:
        for col in ["gross_item_revenue","items_purchased","items_viewed","items_added_to_cart"]:
            if col in df_cat.columns: df_cat[col] = df_cat[col].apply(safe_num)
        df_cf=df_cat[df_cat["item_category"].isin(RANEEN_CATS)].sort_values("gross_item_revenue",ascending=False)
        tir=df_cf["gross_item_revenue"].sum(); tiu=df_cf["items_purchased"].sum()
        c1,c2,c3=st.columns(3)
        with c1: st.markdown(kpi_card("Item Revenue", fmt_currency(tir), "All categories", "up", accent_color="#1D9E75"), unsafe_allow_html=True)
        with c2: st.markdown(kpi_card("Units Sold", fmt_number(tiu), "Total items purchased", "up", accent_color="#3266AD"), unsafe_allow_html=True)
        with c3: st.markdown(kpi_card("Avg Unit Price", fmt_currency(tir/tiu,0) if tiu else "—", "Revenue / Units", "neu", accent_color="#7F77DD"), unsafe_allow_html=True)
        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
        col_l,col_r=st.columns(2)
        with col_l:
            st.markdown(section_header("Revenue by Category", "", "#1D9E75"), unsafe_allow_html=True)
            mx=df_cf["gross_item_revenue"].max()
            for i,(_,r) in enumerate(df_cf.head(10).iterrows()): st.markdown(bar_html(f"{CAT_ICONS.get(r['item_category'],'')} {r['item_category']}", r["gross_item_revenue"]/mx*100 if mx else 0, CAT_COLORS[i%len(CAT_COLORS)], fmt_currency(r["gross_item_revenue"])), unsafe_allow_html=True)
        with col_r:
            st.markdown(section_header("Cart-to-View Rate", "", "#EF9F27"), unsafe_allow_html=True)
            df_cf=df_cf.copy(); df_cf["cr"]=df_cf.apply(lambda r: r["items_added_to_cart"]/r["items_viewed"]*100 if r["items_viewed"]>0 else 0, axis=1)
            mx=df_cf["cr"].max()
            for _,r in df_cf.sort_values("cr",ascending=False).head(10).iterrows():
                c="#1D9E75" if r["cr"]>6 else "#EF9F27" if r["cr"]>3 else "#D85A30"
                st.markdown(bar_html(f"{CAT_ICONS.get(r['item_category'],'')} {r['item_category']}", r["cr"]/mx*100 if mx else 0, c, f"{r['cr']:.1f}%"), unsafe_allow_html=True)
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    st.markdown(section_header("Category Drill-Down", "إيه بيباع جوه كل فئة؟", "#7F77DD"), unsafe_allow_html=True)
    sel_cat=st.selectbox("اختار الفئة", RANEEN_CATS, key="cat_dd")
    if not df_sub.empty and "item_category2" in df_sub.columns:
        for col in ["gross_item_revenue","items_purchased","items_viewed","items_added_to_cart"]:
            if col in df_sub.columns: df_sub[col] = df_sub[col].apply(safe_num)
        dsf=df_sub[(df_sub["item_category"]==sel_cat)&df_sub["item_category2"].notna()&(df_sub["item_category2"]!="")&(df_sub["item_category2"]!="(not set)")]
        dsf=dsf.groupby("item_category2").sum(numeric_only=True).reset_index()
        dsf=dsf[dsf["gross_item_revenue"]>0].sort_values("gross_item_revenue",ascending=False)
        if not dsf.empty:
            SC=["#3266AD","#1D9E75","#EF9F27","#7F77DD","#D85A30","#5DCAA5","#85B7EB","#888780"]
            col_l2,col_r2=st.columns(2); mx=dsf["gross_item_revenue"].max()
            with col_l2:
                st.markdown(f"**Revenue — {sel_cat}**")
                for i,(_,r) in enumerate(dsf.head(10).iterrows()): st.markdown(bar_html(str(r["item_category2"]), r["gross_item_revenue"]/mx*100 if mx else 0, SC[i%len(SC)], fmt_currency(r["gross_item_revenue"])), unsafe_allow_html=True)
            with col_r2:
                st.markdown(f"**Units — {sel_cat}**")
                du=dsf.sort_values("items_purchased",ascending=False); mu=du["items_purchased"].max()
                for i,(_,r) in enumerate(du.head(10).iterrows()): st.markdown(bar_html(str(r["item_category2"]), r["items_purchased"]/mu*100 if mu else 0, SC[i%len(SC)], fmt_number(r["items_purchased"])+" unit"), unsafe_allow_html=True)
        else:
            st.info(f"مفيش sub-category data لـ '{sel_cat}'")
    if not df_prod.empty and "item_name" in df_prod.columns:
        for col in ["item_revenue","items_purchased","items_viewed","items_added_to_cart"]:
            if col in df_prod.columns: df_prod[col] = df_prod[col].apply(safe_num)
        df_top=df_prod[df_prod["item_revenue"]>0].sort_values("item_revenue",ascending=False).head(15)
        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
        st.markdown(section_header("Top 15 Products by Revenue", "", "#3266AD"), unsafe_allow_html=True)
        rows=[]
        for i,(_,r) in enumerate(df_top.iterrows(),1):
            nm=str(r["item_name"])[:55]+("..." if len(str(r["item_name"]))>55 else "")
            vw=safe_num(r.get("items_viewed",0)); cr_=safe_num(r.get("items_added_to_cart",0))/vw*100 if vw>0 else 0
            bc="badge-green" if cr_>8 else "badge-amber" if cr_>4 else "badge-red"
            rows.append(f"<tr><td style='color:#9A9A8E'>{i}</td><td>{nm}</td><td><b style='color:#1D9E75'>{fmt_currency(r['item_revenue'])}</b></td><td>{int(r['items_purchased'])}</td><td>{fmt_number(vw)}</td><td><span class='badge {bc}'>{cr_:.1f}%</span></td></tr>")
        st.markdown(f"<table class='styled-table'><thead><tr><th>#</th><th>Product</th><th>Revenue</th><th>Units</th><th>Views</th><th>Cart%</th></tr></thead><tbody>{''.join(rows)}</tbody></table>", unsafe_allow_html=True)

    # ── CATEGORY FUNNEL TABLE ────────────────────────────────
    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
    st.markdown(section_header("Category Funnel", "Views → Cart → Purchase بالفئة", "#D85A30"), unsafe_allow_html=True)
    st.caption("اختار الفئة لترى الـ Funnel الكاملة جوها")

    with st.spinner("Loading category funnel..."):
        df_cfunnel = load_category_funnel(date_preset, _d_from, _d_to)

    if not df_cfunnel.empty:
        for col in ["gross_item_revenue","items_purchased","items_viewed","items_added_to_cart"]:
            if col in df_cfunnel.columns:
                df_cfunnel[col] = df_cfunnel[col].apply(safe_num)

        fc1, fc2, fc3 = st.columns(3)
        all_cat1 = ["الكل"] + sorted([x for x in df_cfunnel["item_category"].dropna().unique() if x and x != "(not set)"])
        sel_cat1 = fc1.selectbox("Category 1", all_cat1, key="cf_cat1")

        df_cf_f = df_cfunnel.copy()
        if sel_cat1 != "الكل":
            df_cf_f = df_cf_f[df_cf_f["item_category"] == sel_cat1]

        all_cat2 = ["الكل"] + sorted([x for x in df_cf_f["item_category2"].dropna().unique() if x and x != "(not set)"]) if "item_category2" in df_cf_f.columns else ["الكل"]
        sel_cat2 = fc2.selectbox("Category 2", all_cat2, key="cf_cat2")
        if sel_cat2 != "الكل" and "item_category2" in df_cf_f.columns:
            df_cf_f = df_cf_f[df_cf_f["item_category2"] == sel_cat2]

        all_cat3 = ["الكل"] + sorted([x for x in df_cf_f["item_category3"].dropna().unique() if x and x != "(not set)"]) if "item_category3" in df_cf_f.columns else ["الكل"]
        sel_cat3 = fc3.selectbox("Category 3", all_cat3, key="cf_cat3")
        if sel_cat3 != "الكل" and "item_category3" in df_cf_f.columns:
            df_cf_f = df_cf_f[df_cf_f["item_category3"] == sel_cat3]

        # Determine groupby level
        if sel_cat2 != "الكل" and "item_category3" in df_cf_f.columns and len(all_cat3) > 1:
            grp_col, grp_label = "item_category3", "Category 3"
        elif sel_cat1 != "الكل" and "item_category2" in df_cf_f.columns:
            grp_col, grp_label = "item_category2", "Category 2"
        else:
            grp_col, grp_label = "item_category", "Category 1"

        df_cf_g = df_cf_f.groupby(grp_col).sum(numeric_only=True).reset_index()
        df_cf_g = df_cf_g[df_cf_g["gross_item_revenue"] > 0].sort_values("gross_item_revenue", ascending=False)

        if not df_cf_g.empty:
            max_views = df_cf_g["items_viewed"].max()
            cat_rows = []
            for _, r in df_cf_g.iterrows():
                views = safe_num(r.get("items_viewed", 0))
                carts = safe_num(r.get("items_added_to_cart", 0))
                purch = safe_num(r.get("items_purchased", 0))
                rev   = safe_num(r.get("gross_item_revenue", 0))
                v2c   = carts/views*100 if views > 0 else 0
                c2p   = purch/carts*100 if carts > 0 else 0
                v2p   = purch/views*100 if views > 0 else 0
                aov_c = rev/purch       if purch > 0 else 0
                bar_w = views/max_views*100 if max_views > 0 else 0
                v2c_s = "color:#1D9E75;font-weight:600" if v2c>5 else "color:#EF9F27;font-weight:600" if v2c>2 else "color:#D85A30;font-weight:600"
                c2p_s = "color:#1D9E75;font-weight:600" if c2p>30 else "color:#EF9F27;font-weight:600" if c2p>15 else "color:#D85A30;font-weight:600"
                cat_rows.append(f"""<tr>
                  <td><b>{r[grp_col]}</b></td>
                  <td><div style="display:flex;align-items:center;gap:6px">
                    <div style="flex:1;height:5px;background:#F0F2F5;border-radius:3px;overflow:hidden">
                      <div style="width:{bar_w:.0f}%;height:100%;background:#3266AD;border-radius:3px"></div>
                    </div><span style="font-size:11px;min-width:40px;text-align:right">{fmt_number(views)}</span>
                  </div></td>
                  <td>{fmt_number(carts)}</td>
                  <td><span style="{v2c_s}">{v2c:.1f}%</span></td>
                  <td>{fmt_number(purch)}</td>
                  <td><span style="{c2p_s}">{c2p:.1f}%</span></td>
                  <td><span style="color:#7F77DD;font-weight:600">{v2p:.2f}%</span></td>
                  <td><b style="color:#1D9E75">{fmt_currency(rev)}</b></td>
                  <td>{fmt_currency(aov_c,0)}</td>
                </tr>""")

            st.markdown(f"""<table class='styled-table'>
              <thead><tr>
                <th>{grp_label}</th><th>Views</th><th>Carts</th>
                <th>View→Cart</th><th>Purchases</th><th>Cart→Buy</th>
                <th>View→Buy</th><th>Revenue</th><th>AOV</th>
              </tr></thead>
              <tbody>{''.join(cat_rows)}</tbody>
            </table>""", unsafe_allow_html=True)

            st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
            fig_cf = go.Figure(go.Funnel(
                y=["Items Viewed","Added to Cart","Purchased"],
                x=[df_cf_g["items_viewed"].sum(), df_cf_g["items_added_to_cart"].sum(), df_cf_g["items_purchased"].sum()],
                textinfo="value+percent initial",
                marker=dict(color=["#3266AD","#378ADD","#1D9E75"]),
            ))
            fig_cf.update_layout(**PLOT_LAYOUT, height=250)
            st.plotly_chart(fig_cf, use_container_width=True)
        else:
            st.info("مفيش بيانات للفئة دي.")
    else:
        st.info("مفيش بيانات category funnel.")

# ═══════════════════════════════════════════════════════════
# CAMPAIGNS
# ═══════════════════════════════════════════════════════════
elif active_tab == "Campaigns":
    st.markdown(section_header("Campaigns Performance", "Google Ads Analysis", "#3266AD"), unsafe_allow_html=True)
    if not df_cp.empty and "session_google_ads_campaign_name" in df_cp.columns:
        for col in ["sessions","purchase_revenue","transactions","add_to_carts","checkouts"]:
            if col in df_cp.columns: df_cp[col] = df_cp[col].apply(safe_num)
        df_p=df_cp[df_cp["session_google_ads_campaign_name"].notna()&(df_cp["session_google_ads_campaign_name"]!="(not set)")&(df_cp["sessions"]>100)].copy()
        df_p["cvr"]=df_p.apply(lambda r: r["transactions"]/r["sessions"]*100 if r["sessions"]>0 else 0, axis=1)
        df_p["rps"]=df_p.apply(lambda r: r["purchase_revenue"]/r["sessions"] if r["sessions"]>0 else 0, axis=1)
        df_p=df_p.sort_values("purchase_revenue",ascending=False)
        best=df_p.loc[df_p["purchase_revenue"].idxmax()] if not df_p.empty else None
        worst=df_p.loc[df_p["cvr"].idxmin()] if not df_p.empty else None
        bcvr=df_p.loc[df_p["cvr"].idxmax()] if not df_p.empty else None
        c1,c2,c3,c4=st.columns(4)
        with c1: st.markdown(kpi_card("Best Campaign", best["session_google_ads_campaign_name"].split("-")[-1] if best is not None else "—", fmt_currency(best["purchase_revenue"]) if best is not None else "—", "up", accent_color="#3266AD"), unsafe_allow_html=True)
        with c2: st.markdown(kpi_card("Highest CVR", bcvr["session_google_ads_campaign_name"].split("-")[-1] if bcvr is not None else "—", fmt_pct(bcvr["cvr"],2) if bcvr is not None else "—", "up", accent_color="#1D9E75"), unsafe_allow_html=True)
        with c3: st.markdown(kpi_card("Total Paid Sessions", fmt_number(df_p["sessions"].sum()), "Google Ads campaigns", "neu", accent_color="#7F77DD"), unsafe_allow_html=True)
        with c4: st.markdown(kpi_card("Worst CVR", worst["session_google_ads_campaign_name"].split("-")[-1] if worst is not None else "—", fmt_pct(worst["cvr"],2) if worst is not None else "—", "down", accent_color="#D85A30"), unsafe_allow_html=True)
        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
        col_l,col_r=st.columns(2)
        with col_l:
            st.markdown(section_header("Revenue per Session", "Campaign Efficiency", "#EF9F27"), unsafe_allow_html=True)
            dr=df_p.sort_values("rps",ascending=False).head(10); mx=dr["rps"].max()
            for _,r in dr.iterrows():
                p=r["rps"]/mx*100 if mx else 0; c="#1D9E75" if p>70 else "#EF9F27" if p>30 else "#D85A30"
                st.markdown(bar_html(str(r["session_google_ads_campaign_name"])[-28:], p, c, fmt_currency(r["rps"],1)), unsafe_allow_html=True)
        with col_r:
            st.markdown(section_header("Sessions vs Revenue", "Bubble View", "#3266AD"), unsafe_allow_html=True)
            fig=px.scatter(df_p.head(12), x="sessions", y="purchase_revenue", size="transactions", color="cvr", hover_name="session_google_ads_campaign_name", color_continuous_scale=["#D85A30","#EF9F27","#1D9E75"], size_max=40)
            fig.update_layout(**PLOT_LAYOUT, height=280); st.plotly_chart(fig, use_container_width=True)
        st.markdown(section_header("All Campaigns — Full Analysis", "", "#2A3050"), unsafe_allow_html=True)
        rows=[]
        for _,r in df_p.iterrows():
            cv=r["cvr"]
            if cv>=1.5: badge='<span class="badge badge-green">الأقوى</span>'
            elif cv>=0.8: badge='<span class="badge badge-blue">جيد</span>'
            elif cv>=0.3: badge='<span class="badge badge-amber">راجع</span>'
            else: badge='<span class="badge badge-red">ضعيف</span>'
            rows.append(f"<tr><td style='font-size:11px'>{r['session_google_ads_campaign_name']}</td><td>{fmt_number(r['sessions'])}</td><td><b style='color:#1D9E75'>{fmt_currency(r['purchase_revenue'])}</b></td><td>{int(r['transactions'])}</td><td><b style='color:{'#1D9E75' if cv>=1 else '#EF9F27' if cv>=0.5 else '#D85A30'}'>{fmt_pct(cv,2)}</b></td><td>{fmt_currency(r['rps'],1)}</td><td>{badge}</td></tr>")
        st.markdown(f"<table class='styled-table'><thead><tr><th>Campaign</th><th>Sessions</th><th>Revenue</th><th>Orders</th><th>CVR</th><th>Rev/Ses</th><th>Rating</th></tr></thead><tbody>{''.join(rows)}</tbody></table>", unsafe_allow_html=True)
        st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
        st.markdown(section_header("Campaign → Products", "إيه المنتجات اللي باعتها كل حملة؟", "#7F77DD"), unsafe_allow_html=True)
        with st.spinner("Loading campaign products..."):
            df_cpp=load_campaign_products(date_preset, _d_from, _d_to)
        camp_list=df_p["session_google_ads_campaign_name"].tolist()
        sel_camp=st.selectbox("اختار الحملة", camp_list, key="camp_sel")
        if not df_cpp.empty and "session_google_ads_campaign_name" in df_cpp.columns and "item_name" in df_cpp.columns:
            for c2 in ["item_revenue","items_purchased"]:
                if c2 in df_cpp.columns: df_cpp[c2] = df_cpp[c2].apply(safe_num)
            dcp=df_cpp[(df_cpp["session_google_ads_campaign_name"]==sel_camp)&df_cpp["item_name"].notna()&(df_cpp["item_name"]!="(not set)")&(df_cpp["item_revenue"]>0)].sort_values("item_revenue",ascending=False)
            if not dcp.empty:
                kc1,kc2,kc3=st.columns(3)
                with kc1: st.markdown(kpi_card("Campaign Revenue", fmt_currency(dcp["item_revenue"].sum()), sel_camp.split("-")[-1], "up", accent_color="#7F77DD"), unsafe_allow_html=True)
                with kc2: st.markdown(kpi_card("Units Sold", fmt_number(dcp["items_purchased"].sum()), "من الحملة دي", "up", accent_color="#3266AD"), unsafe_allow_html=True)
                with kc3: st.markdown(kpi_card("SKUs", str(len(dcp)), "منتج مختلف", "neu", accent_color="#1D9E75"), unsafe_allow_html=True)
                PC=["#7F77DD","#3266AD","#1D9E75","#EF9F27","#D85A30","#85B7EB","#5DCAA5","#888780"]
                cpl,cpr=st.columns(2); mx=dcp["item_revenue"].max()
                with cpl:
                    st.markdown("**Top Products — Revenue**")
                    for i,(_,r) in enumerate(dcp.head(10).iterrows()): st.markdown(bar_html(str(r["item_name"])[:45], r["item_revenue"]/mx*100 if mx else 0, PC[i%len(PC)], fmt_currency(r["item_revenue"])), unsafe_allow_html=True)
                with cpr:
                    st.markdown("**Top Products — Units**")
                    du=dcp.sort_values("items_purchased",ascending=False); mu=du["items_purchased"].max()
                    for i,(_,r) in enumerate(du.head(10).iterrows()): st.markdown(bar_html(str(r["item_name"])[:45], r["items_purchased"]/mu*100 if mu else 0, PC[i%len(PC)], fmt_number(r["items_purchased"])+" unit"), unsafe_allow_html=True)
            else:
                st.info("مفيش بيانات منتجات للحملة دي.")
        else:
            st.info("مفيش بيانات campaign products متاحة.")

    # ── META CAMPAIGNS ───────────────────────────────────────
    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
    st.markdown(section_header("Meta Campaigns", "أداء كامبينز Facebook & Instagram في GA4", "#1877F2"), unsafe_allow_html=True)
    st.caption("البيانات من GA4 عن طريق UTM parameters — session_manual_campaign_name")

    with st.spinner("Loading Meta campaigns..."):
        df_meta = load_meta_campaigns(date_preset, _d_from, _d_to)

    if not df_meta.empty and "session_manual_campaign_name" in df_meta.columns:
        for col in ["sessions","purchase_revenue","transactions","add_to_carts"]:
            if col in df_meta.columns: df_meta[col] = df_meta[col].apply(safe_num)

        # Filter out non-Meta (organic, not set, referral, Google)
        exclude = ["(organic)","(not set)","(referral)","(direct)"]
        df_meta_f = df_meta[
            ~df_meta["session_manual_campaign_name"].isin(exclude) &
            df_meta["session_manual_campaign_name"].notna() &
            (df_meta["sessions"] > 5)
        ].copy()

        df_meta_f["cvr"] = df_meta_f.apply(lambda r: r["transactions"]/r["sessions"]*100 if r["sessions"]>0 else 0, axis=1)
        df_meta_f["rps"] = df_meta_f.apply(lambda r: r["purchase_revenue"]/r["sessions"] if r["sessions"]>0 else 0, axis=1)
        df_meta_f["aov"] = df_meta_f.apply(lambda r: r["purchase_revenue"]/r["transactions"] if r["transactions"]>0 else 0, axis=1)
        df_meta_f = df_meta_f.sort_values("purchase_revenue", ascending=False)

        # KPIs
        tot_meta_rev = df_meta_f["purchase_revenue"].sum()
        tot_meta_ses = df_meta_f["sessions"].sum()
        tot_meta_ord = df_meta_f["transactions"].sum()
        tot_meta_crt = df_meta_f["add_to_carts"].sum()
        meta_cvr = tot_meta_ord/tot_meta_ses*100 if tot_meta_ses>0 else 0
        meta_aov = tot_meta_rev/tot_meta_ord if tot_meta_ord>0 else 0

        mk1,mk2,mk3,mk4 = st.columns(4)
        with mk1: st.markdown(kpi_card("Meta Revenue", fmt_currency(tot_meta_rev), "via UTM campaigns", "up", accent_color="#1877F2"), unsafe_allow_html=True)
        with mk2: st.markdown(kpi_card("Meta Sessions", fmt_number(tot_meta_ses), "من كل الكامبينز", "neu", accent_color="#1877F2"), unsafe_allow_html=True)
        with mk3: st.markdown(kpi_card("Meta Orders", fmt_number(tot_meta_ord), f"CVR: {fmt_pct(meta_cvr,2)}", "up" if meta_cvr>0.5 else "warn", accent_color="#1877F2"), unsafe_allow_html=True)
        with mk4: st.markdown(kpi_card("Meta AOV", fmt_currency(meta_aov,0), "متوسط قيمة الطلب", "neu", accent_color="#1877F2"), unsafe_allow_html=True)

        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

        # Search + filter
        mc1, mc2 = st.columns([3,1])
        meta_search = mc1.text_input("🔍 Search campaign", placeholder="RT, Conv, Catalog...", key="meta_search")
        meta_min_ses = mc2.number_input("Min Sessions", min_value=0, value=10, step=10, key="meta_min")

        df_meta_show = df_meta_f[df_meta_f["sessions"] >= meta_min_ses]
        if meta_search:
            df_meta_show = df_meta_show[df_meta_show["session_manual_campaign_name"].str.contains(meta_search, case=False, na=False)]

        # Revenue bars
        col_l, col_r = st.columns(2)
        with col_l:
            st.markdown("**Top 10 — Revenue**")
            mx = df_meta_show["purchase_revenue"].max()
            MCOLS = ["#1877F2","#42A5F5","#1565C0","#0D47A1","#1E88E5","#2196F3","#64B5F6","#90CAF9","#BBDEFB","#E3F2FD"]
            for i,(_,r) in enumerate(df_meta_show.head(10).iterrows()):
                pct = r["purchase_revenue"]/mx*100 if mx else 0
                nm = str(r["session_manual_campaign_name"])[:45]+("..." if len(str(r["session_manual_campaign_name"]))>45 else "")
                st.markdown(bar_html(nm, pct, MCOLS[i%len(MCOLS)], fmt_currency(r["purchase_revenue"])), unsafe_allow_html=True)

        with col_r:
            st.markdown("**Top 10 — Rev/Session**")
            df_rps_meta = df_meta_show[df_meta_show["transactions"]>0].sort_values("rps", ascending=False)
            mx_rps = df_rps_meta["rps"].max()
            for i,(_,r) in enumerate(df_rps_meta.head(10).iterrows()):
                pct = r["rps"]/mx_rps*100 if mx_rps else 0
                nm = str(r["session_manual_campaign_name"])[:45]+("..." if len(str(r["session_manual_campaign_name"]))>45 else "")
                c = "#1D9E75" if pct>70 else "#1877F2" if pct>30 else "#D85A30"
                st.markdown(bar_html(nm, pct, c, fmt_currency(r["rps"],1)), unsafe_allow_html=True)

        # Full table
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        meta_rows = []
        for _,r in df_meta_show.head(50).iterrows():
            cv = r["cvr"]; rps_ = r["rps"]
            nm = str(r["session_manual_campaign_name"])
            crt = safe_num(r.get("add_to_carts",0))
            ses = r["sessions"]
            c2c = crt/ses*100 if ses>0 else 0

            # Campaign type detection
            nm_l = nm.lower()
            if "rt |" in nm_l or nm_l.startswith("rt ") or "retention" in nm_l:
                camp_type = '<span class="badge badge-purple">🔄 Retargeting</span>'
            elif "prospective" in nm_l or "prosp" in nm_l:
                camp_type = '<span class="badge badge-blue">🎯 Prospecting</span>'
            elif "conv" in nm_l:
                camp_type = '<span class="badge badge-green">💰 Conv</span>'
            elif "traffic" in nm_l:
                camp_type = '<span class="badge badge-gray">📡 Traffic</span>'
            else:
                camp_type = '<span class="badge badge-gray">📌 Other</span>'

            if cv>=1.5: rating='<span class="badge badge-green">الأقوى</span>'
            elif cv>=0.8: rating='<span class="badge badge-blue">جيد</span>'
            elif cv>=0.3: rating='<span class="badge badge-amber">راجع</span>'
            else: rating='<span class="badge badge-red">ضعيف</span>'

            meta_rows.append(f"""<tr>
              <td style="font-size:10px;max-width:220px"><b>{nm[:60]}{"..." if len(nm)>60 else ""}</b></td>
              <td>{camp_type}</td>
              <td>{fmt_number(ses)}</td>
              <td><b style="color:#1877F2">{fmt_currency(r["purchase_revenue"])}</b></td>
              <td>{fmt_number(r["transactions"])}</td>
              <td><b style="color:{'#1D9E75' if cv>=1 else '#EF9F27' if cv>=0.3 else '#D85A30'}">{fmt_pct(cv,2)}</b></td>
              <td>{fmt_pct(c2c,1)}</td>
              <td>{fmt_currency(rps_,1)}</td>
              <td>{fmt_currency(r["aov"],0)}</td>
              <td>{rating}</td>
            </tr>""")

        st.markdown(f"""<table class='styled-table'>
          <thead><tr>
            <th>Campaign</th><th>Type</th><th>Sessions</th><th>Revenue</th>
            <th>Orders</th><th>CVR</th><th>Cart%</th><th>Rev/Ses</th><th>AOV</th><th>Rating</th>
          </tr></thead>
          <tbody>{''.join(meta_rows)}</tbody>
        </table>""", unsafe_allow_html=True)
        st.caption(f"Showing {min(50,len(df_meta_show))} of {len(df_meta_show)} Meta campaigns · (organic), (not set), (referral) excluded")
    else:
        st.info("مفيش بيانات Meta campaigns — تأكد إن الـ UTM parameters شغالة على الـ Meta ads.")

# ═══════════════════════════════════════════════════════════
# USERS
# ═══════════════════════════════════════════════════════════
elif active_tab == "Users":
    st.markdown(section_header("Users Analytics", "Demographics & Cohort Analysis", "#7F77DD"), unsafe_allow_html=True)

    with st.spinner("Loading users data..."):
        df_unr  = load_users_nr(date_preset, _d_from, _d_to)
        df_udev = load_users_device(date_preset, _d_from, _d_to)
        df_uch  = load_users_channel(date_preset, _d_from, _d_to)

    # ── KPIs ────────────────────────────────────────────────
    tot_users     = safe_num(df_unr["active_users"].sum())  if not df_unr.empty and "active_users" in df_unr.columns else 0
    tot_new_u     = safe_num(df_unr[df_unr["new_vs_returning"]=="new"]["sessions"].sum()) if not df_unr.empty and "new_vs_returning" in df_unr.columns else 0
    tot_ret_u     = safe_num(df_unr[df_unr["new_vs_returning"]=="returning"]["sessions"].sum()) if not df_unr.empty and "new_vs_returning" in df_unr.columns else 0
    ret_rev       = safe_num(df_unr[df_unr["new_vs_returning"]=="returning"]["purchase_revenue"].sum()) if not df_unr.empty and "new_vs_returning" in df_unr.columns else 0
    new_rev       = safe_num(df_unr[df_unr["new_vs_returning"]=="new"]["purchase_revenue"].sum()) if not df_unr.empty and "new_vs_returning" in df_unr.columns else 0
    tot_u_rev     = ret_rev + new_rev
    ret_pct       = ret_rev / tot_u_rev * 100 if tot_u_rev > 0 else 0
    ret_txn       = safe_num(df_unr[df_unr["new_vs_returning"]=="returning"]["transactions"].sum()) if not df_unr.empty else 0
    new_txn       = safe_num(df_unr[df_unr["new_vs_returning"]=="new"]["transactions"].sum()) if not df_unr.empty else 0
    ret_cvr       = ret_txn / tot_ret_u * 100 if tot_ret_u > 0 else 0
    new_cvr       = new_txn / tot_new_u * 100 if tot_new_u > 0 else 0
    ret_aov       = ret_rev / ret_txn if ret_txn > 0 else 0
    new_aov       = new_rev / new_txn if new_txn > 0 else 0

    c1,c2,c3,c4 = st.columns(4)
    with c1: st.markdown(kpi_card("Active Users", fmt_number(tot_users), "▲ Unique users", "up", accent_color="#7F77DD"), unsafe_allow_html=True)
    with c2: st.markdown(kpi_card("New Users", fmt_number(tot_new_u), f"CVR: {fmt_pct(new_cvr,2)}", "neu", accent_color="#3266AD"), unsafe_allow_html=True)
    with c3: st.markdown(kpi_card("Returning Users", fmt_number(tot_ret_u), f"CVR: {fmt_pct(ret_cvr,2)}", "up", accent_color="#1D9E75"), unsafe_allow_html=True)
    with c4: st.markdown(kpi_card("Returning Revenue", fmt_currency(ret_rev), f"▲ {ret_pct:.1f}% of total", "up", accent_color="#1D9E75"), unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # ── NEW VS RETURNING BREAKDOWN ───────────────────────────
    st.markdown(section_header("New vs Returning — Full Comparison", "", "#7F77DD"), unsafe_allow_html=True)

    seg_data = []
    if not df_unr.empty and "new_vs_returning" in df_unr.columns:
        for col in ["sessions","active_users","purchase_revenue","transactions","add_to_carts","checkouts","bounce_rate"]:
            if col in df_unr.columns: df_unr[col] = df_unr[col].apply(safe_num)
        for seg in ["returning","new"]:
            d = df_unr[df_unr["new_vs_returning"]==seg]
            if d.empty: continue
            ses = d["sessions"].sum(); rev = d["purchase_revenue"].sum()
            txn = d["transactions"].sum(); crt = d["add_to_carts"].sum()
            br  = d["bounce_rate"].mean()*100 if "bounce_rate" in d.columns else 0
            _cvr = txn/ses*100 if ses>0 else 0
            _aov = rev/txn if txn>0 else 0
            _ca  = (1-txn/crt)*100 if crt>0 else 0
            seg_data.append({
                "Segment": seg.title(), "Sessions": ses, "Revenue": rev,
                "Orders": txn, "CVR": _cvr, "AOV": _aov,
                "Cart Abandon": _ca, "Bounce": br,
            })

    if seg_data:
        # Visual comparison bars
        col_l, col_r = st.columns(2)
        with col_l:
            st.markdown("**Revenue Split**")
            for s in seg_data:
                mx = max(x["Revenue"] for x in seg_data)
                pct = s["Revenue"]/mx*100 if mx else 0
                c = "#1D9E75" if s["Segment"]=="Returning" else "#3266AD"
                st.markdown(bar_html(s["Segment"], pct, c, fmt_currency(s["Revenue"])), unsafe_allow_html=True)
            st.markdown("**CVR Comparison**")
            for s in seg_data:
                mx = max(x["CVR"] for x in seg_data)
                pct = s["CVR"]/mx*100 if mx else 0
                c = "#1D9E75" if s["Segment"]=="Returning" else "#3266AD"
                st.markdown(bar_html(s["Segment"], pct, c, fmt_pct(s["CVR"],2)), unsafe_allow_html=True)

        with col_r:
            st.markdown("**AOV Comparison**")
            for s in seg_data:
                mx = max(x["AOV"] for x in seg_data)
                pct = s["AOV"]/mx*100 if mx else 0
                c = "#1D9E75" if s["Segment"]=="Returning" else "#3266AD"
                st.markdown(bar_html(s["Segment"], pct, c, fmt_currency(s["AOV"],0)), unsafe_allow_html=True)
            st.markdown("**Cart Abandonment**")
            for s in seg_data:
                mx = max(x["Cart Abandon"] for x in seg_data)
                pct = s["Cart Abandon"]/mx*100 if mx else 0
                c = "#D85A30" if s["Cart Abandon"]>85 else "#EF9F27"
                st.markdown(bar_html(s["Segment"], pct, c, fmt_pct(s["Cart Abandon"],1)), unsafe_allow_html=True)

        # Full table
        seg_rows = []
        for s in seg_data:
            bc = "badge-green" if s["Segment"]=="Returning" else "badge-blue"
            seg_rows.append(f"""<tr>
              <td><span class='badge {bc}'>{s["Segment"]}</span></td>
              <td>{fmt_number(s["Sessions"])}</td>
              <td><b style='color:#1D9E75'>{fmt_currency(s["Revenue"])}</b></td>
              <td>{fmt_number(s["Orders"])}</td>
              <td><b style='color:{"#1D9E75" if s["CVR"]>0.8 else "#EF9F27"}'>{fmt_pct(s["CVR"],2)}</b></td>
              <td>{fmt_currency(s["AOV"],0)}</td>
              <td style='color:{"#D85A30" if s["Cart Abandon"]>85 else "#EF9F27"}'>{fmt_pct(s["Cart Abandon"],1)}</td>
              <td style='color:{"#D85A30" if s["Bounce"]>55 else "#EF9F27"}'>{fmt_pct(s["Bounce"],1)}</td>
            </tr>""")
        st.markdown(f"""<table class='styled-table'>
          <thead><tr><th>Segment</th><th>Sessions</th><th>Revenue</th><th>Orders</th><th>CVR</th><th>AOV</th><th>Cart Abandon</th><th>Bounce</th></tr></thead>
          <tbody>{''.join(seg_rows)}</tbody>
        </table>""", unsafe_allow_html=True)

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    # ── DEVICE USER ANALYSIS ────────────────────────────────
    st.markdown(section_header("Users by Device", "Behavior per Platform", "#3266AD"), unsafe_allow_html=True)
    if not df_udev.empty and "devicecategory" in df_udev.columns:
        for col in ["sessions","active_users","purchase_revenue","transactions","bounce_rate","average_session_duration","add_to_carts"]:
            if col in df_udev.columns: df_udev[col] = df_udev[col].apply(safe_num)
        df_udev_f = df_udev[df_udev["devicecategory"].isin(["mobile","desktop","tablet"])].copy()
        dev_rows = []
        DC = {"mobile":"badge-blue","desktop":"badge-gray","tablet":"badge-green"}
        for _,r in df_udev_f.sort_values("sessions",ascending=False).iterrows():
            ses = r["sessions"]; rev = r["purchase_revenue"]; txn = r["transactions"]
            br  = r["bounce_rate"]*100 if "bounce_rate" in r.index else 0
            _cvr= txn/ses*100 if ses>0 else 0
            _aov= rev/txn if txn>0 else 0
            rps = rev/ses if ses>0 else 0
            asd = r.get("average_session_duration",0)
            m_  = int(asd//60); s_ = int(asd%60)
            bc  = DC.get(r["devicecategory"],"badge-gray")
            dev_rows.append(f"""<tr>
              <td><span class='badge {bc}'>{r["devicecategory"].title()}</span></td>
              <td>{fmt_number(ses)}</td>
              <td><b style='color:#1D9E75'>{fmt_currency(rev)}</b></td>
              <td>{fmt_number(txn)}</td>
              <td><b style='color:{"#1D9E75" if _cvr>0.8 else "#EF9F27"}'>{fmt_pct(_cvr,2)}</b></td>
              <td>{fmt_currency(_aov,0)}</td>
              <td>{fmt_currency(rps,1)}</td>
              <td style='color:{"#D85A30" if br>55 else "#EF9F27" if br>45 else "#1D9E75"}'>{fmt_pct(br,1)}</td>
              <td>{m_}:{s_:02d} min</td>
            </tr>""")
        st.markdown(f"""<table class='styled-table'>
          <thead><tr><th>Device</th><th>Sessions</th><th>Revenue</th><th>Orders</th><th>CVR</th><th>AOV</th><th>Rev/Session</th><th>Bounce</th><th>Avg Session</th></tr></thead>
          <tbody>{''.join(dev_rows)}</tbody>
        </table>""", unsafe_allow_html=True)

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    # ── ACQUISITION CHANNEL USER ANALYSIS ───────────────────
    st.markdown(section_header("Users by Acquisition Channel", "كيف وصلوا؟", "#EF9F27"), unsafe_allow_html=True)
    if not df_uch.empty and "session_default_channel_group" in df_uch.columns:
        for col in ["sessions","active_users","purchase_revenue","transactions","bounce_rate"]:
            if col in df_uch.columns: df_uch[col] = df_uch[col].apply(safe_num)
        df_uch_f = df_uch[df_uch["session_default_channel_group"].notna() & (df_uch["session_default_channel_group"]!="")].copy()
        df_uch_f = df_uch_f.groupby("session_default_channel_group").sum(numeric_only=True).reset_index()
        df_uch_f = df_uch_f[df_uch_f["sessions"]>10].sort_values("sessions",ascending=False)
        uch_rows = []
        for _,r in df_uch_f.iterrows():
            ses=r["sessions"]; rev=r["purchase_revenue"]; txn=r["transactions"]
            br=r["bounce_rate"]*100 if "bounce_rate" in r.index else 0
            _cvr=txn/ses*100 if ses>0 else 0
            rps=rev/ses if ses>0 else 0
            uch_rows.append(f"""<tr>
              <td><b>{r["session_default_channel_group"]}</b></td>
              <td>{fmt_number(ses)}</td>
              <td>{fmt_currency(rev)}</td>
              <td>{fmt_number(txn)}</td>
              <td><b style='color:{"#1D9E75" if _cvr>=1 else "#EF9F27" if _cvr>=0.5 else "#D85A30"}'>{fmt_pct(_cvr,2)}</b></td>
              <td>{fmt_currency(rps,1)}</td>
              <td style='color:{"#D85A30" if br>55 else "#EF9F27" if br>45 else "#1D9E75"}'>{fmt_pct(br,1)}</td>
            </tr>""")
        st.markdown(f"""<table class='styled-table'>
          <thead><tr><th>Channel</th><th>Sessions</th><th>Revenue</th><th>Orders</th><th>CVR</th><th>Rev/Session</th><th>Bounce</th></tr></thead>
          <tbody>{''.join(uch_rows)}</tbody>
        </table>""", unsafe_allow_html=True)

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    # ── COHORT ANALYSIS ──────────────────────────────────────
    st.markdown(section_header("Cohort Analysis", "Returning Users بالشهر", "#D85A30"), unsafe_allow_html=True)
    st.caption("كل صف = شهر · بيوضح New vs Returning sessions ونسبة الـ Retention")

    with st.spinner("Loading cohort data (90 days)..."):
        df_cohort = load_cohort(_d_from, _d_to)

    if not df_cohort.empty and "date" in df_cohort.columns and "new_vs_returning" in df_cohort.columns:
        for col in ["sessions","purchase_revenue","transactions","active_users"]:
            if col in df_cohort.columns: df_cohort[col] = df_cohort[col].apply(safe_num)

        df_cohort["date"] = pd.to_datetime(df_cohort["date"], errors="coerce")
        df_cohort = df_cohort.dropna(subset=["date"])
        df_cohort["month"] = df_cohort["date"].dt.to_period("M").astype(str)

        # Monthly aggregation by new_vs_returning
        df_monthly = df_cohort.groupby(["month","new_vs_returning"]).agg(
            sessions=("sessions","sum"),
            revenue=("purchase_revenue","sum"),
            orders=("transactions","sum"),
        ).reset_index()

        months = sorted(df_monthly["month"].unique())

        cohort_rows = []
        for month in months:
            m_data = df_monthly[df_monthly["month"]==month]
            new_d  = m_data[m_data["new_vs_returning"]=="new"]
            ret_d  = m_data[m_data["new_vs_returning"]=="returning"]
            new_ses = safe_num(new_d["sessions"].sum())
            ret_ses = safe_num(ret_d["sessions"].sum())
            new_rev = safe_num(new_d["revenue"].sum())
            ret_rev_ = safe_num(ret_d["revenue"].sum())
            new_ord = safe_num(new_d["orders"].sum())
            ret_ord = safe_num(ret_d["orders"].sum())
            tot_ses = new_ses + ret_ses
            ret_rate = ret_ses/tot_ses*100 if tot_ses > 0 else 0
            tot_rev = new_rev + ret_rev_
            ret_rev_pct = ret_rev_/tot_rev*100 if tot_rev > 0 else 0
            new_cvr_ = new_ord/new_ses*100 if new_ses>0 else 0
            ret_cvr_ = ret_ord/ret_ses*100 if ret_ses>0 else 0

            # Color code retention rate
            ret_color = "#1D9E75" if ret_rate>50 else "#EF9F27" if ret_rate>30 else "#D85A30"
            bar_w = min(ret_rate, 100)

            cohort_rows.append(f"""<tr>
              <td><b>{month}</b></td>
              <td>{fmt_number(new_ses)}</td>
              <td>{fmt_number(ret_ses)}</td>
              <td>
                <div style='display:flex;align-items:center;gap:6px'>
                  <div style='flex:1;height:6px;background:#F0F2F5;border-radius:3px;overflow:hidden'>
                    <div style='width:{bar_w:.0f}%;height:100%;background:{ret_color};border-radius:3px'></div>
                  </div>
                  <span style='color:{ret_color};font-weight:600;min-width:38px;text-align:right'>{ret_rate:.1f}%</span>
                </div>
              </td>
              <td>{fmt_currency(new_rev)}</td>
              <td>{fmt_currency(ret_rev_)}</td>
              <td><b style='color:{ret_color}'>{ret_rev_pct:.1f}%</b></td>
              <td style='color:{"#EF9F27"}'>{fmt_pct(new_cvr_,2)}</td>
              <td style='color:#1D9E75;font-weight:600'>{fmt_pct(ret_cvr_,2)}</td>
            </tr>""")

        st.markdown(f"""<table class='styled-table'>
          <thead><tr>
            <th>Month</th>
            <th>New Sessions</th><th>Returning Sessions</th><th>Retention Rate</th>
            <th>New Revenue</th><th>Returning Revenue</th><th>Rev Retention</th>
            <th>New CVR</th><th>Returning CVR</th>
          </tr></thead>
          <tbody>{''.join(cohort_rows)}</tbody>
        </table>""", unsafe_allow_html=True)

        # Retention trend chart
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        months_list, ret_rates, new_revs, ret_revs = [], [], [], []
        for month in months:
            m_data = df_monthly[df_monthly["month"]==month]
            ns = safe_num(m_data[m_data["new_vs_returning"]=="new"]["sessions"].sum())
            rs = safe_num(m_data[m_data["new_vs_returning"]=="returning"]["sessions"].sum())
            nr = safe_num(m_data[m_data["new_vs_returning"]=="new"]["revenue"].sum())
            rr = safe_num(m_data[m_data["new_vs_returning"]=="returning"]["revenue"].sum())
            tot = ns+rs
            months_list.append(month)
            ret_rates.append(rs/tot*100 if tot>0 else 0)
            new_revs.append(nr/1000)
            ret_revs.append(rr/1000)

        fig_cohort = make_subplots(specs=[[{"secondary_y":True}]])
        fig_cohort.add_trace(go.Bar(name="New Revenue K ج", x=months_list, y=new_revs, marker_color="rgba(50,102,173,0.7)"), secondary_y=False)
        fig_cohort.add_trace(go.Bar(name="Returning Revenue K ج", x=months_list, y=ret_revs, marker_color="rgba(29,158,117,0.7)"), secondary_y=False)
        fig_cohort.add_trace(go.Scatter(name="Retention Rate %", x=months_list, y=ret_rates, line=dict(color="#D85A30",width=2.5), mode="lines+markers", marker_size=7), secondary_y=True)
        fig_cohort.update_layout(**PLOT_LAYOUT, height=300, barmode="group")
        fig_cohort.update_yaxes(title_text="Revenue K ج", secondary_y=False)
        fig_cohort.update_yaxes(title_text="Retention %", secondary_y=True, ticksuffix="%")
        st.plotly_chart(fig_cohort, use_container_width=True)
    else:
        st.info("مفيش بيانات cohort كافية — محتاج على الأقل شهرين من الداتا.")

# ═══════════════════════════════════════════════════════════
# INSIGHTS
# ═══════════════════════════════════════════════════════════
elif active_tab == "Insights":
    st.markdown(section_header("Strategic Insights & Action Plan", "Prioritized Recommendations", "#D85A30"), unsafe_allow_html=True)
    st.markdown("### 🔴 P1 — فوري (هذا الأسبوع)")
    st.markdown(insight("🔴", f"Cart Abandonment {cart_abandon:.1f}%", f"من {fmt_number(tot_carts)} add-to-cart، بس {fmt_number(tot_orders)} اشتروا. Abandoned Cart Email Series + Exit-intent popup = +15-20% revenue.", "insight-red"), unsafe_allow_html=True)
    if avg_bounce > 55:
        st.markdown(insight("🔴", f"Bounce Rate مرتفع {avg_bounce:.1f}%", "راجع الـ Landing Pages وسرعة التحميل فوراً.", "insight-red"), unsafe_allow_html=True)
    if not df_cp.empty and "session_google_ads_campaign_name" in df_cp.columns:
        for col in ["sessions","transactions"]:
            if col in df_cp.columns: df_cp[col] = df_cp[col].apply(safe_num)
        weak=df_cp[(df_cp["sessions"]>50000)&(df_cp["session_google_ads_campaign_name"]!="(not set)")&(df_cp["transactions"]/df_cp["sessions"].replace(0,1)<0.002)]
        for _,r in weak.head(2).iterrows():
            _cvr=r["transactions"]/r["sessions"]*100 if r["sessions"]>0 else 0
            st.markdown(insight("🔴", f"Campaign ضعيف: {r['session_google_ads_campaign_name']}", f"{fmt_number(r['sessions'])} session بـ CVR {_cvr:.2f}% فقط.", "insight-red"), unsafe_allow_html=True)
    st.markdown("### ⚠ P2 — مهم (هذا الشهر)")
    if not df_dv.empty and "devicecategory" in df_dv.columns:
        df_dv["bounce_rate"]=df_dv["bounce_rate"].apply(safe_num)
        d=df_dv[df_dv["devicecategory"]=="desktop"]; m=df_dv[df_dv["devicecategory"]=="mobile"]
        if not d.empty and not m.empty:
            db=d["bounce_rate"].mean()*100; mb=m["bounce_rate"].mean()*100
            if db>mb+5: st.markdown(insight("⚠", f"Desktop Bounce {db:.1f}% vs Mobile {mb:.1f}%", "تحسين Desktop UX ممكن يضيف ملايين.", "insight-amber"), unsafe_allow_html=True)
    if not df_ch.empty and "session_default_channel_group" in df_ch.columns:
        for col in ["sessions","purchase_revenue","transactions"]:
            if col in df_ch.columns: df_ch[col] = df_ch[col].apply(safe_num)
        ps=df_ch[df_ch["session_default_channel_group"]=="Paid Social"]; pq=df_ch[df_ch["session_default_channel_group"]=="Paid Search"]
        if not ps.empty and not pq.empty:
            ps_cvr=ps["transactions"].sum()/ps["sessions"].sum()*100 if ps["sessions"].sum()>0 else 0
            pq_cvr=pq["transactions"].sum()/pq["sessions"].sum()*100 if pq["sessions"].sum()>0 else 0
            if pq_cvr>ps_cvr*1.5: st.markdown(insight("⚠", f"Paid Search CVR ({pq_cvr:.2f}%) أعلى من Paid Social ({ps_cvr:.2f}%)", "إعادة توزيع الـ budget من Paid Social لـ Paid Search يحسن ROAS.", "insight-amber"), unsafe_allow_html=True)
    st.markdown("### ✅ P3 — فرص نمو")
    if not df_nr.empty and "new_vs_returning" in df_nr.columns:
        for col in ["sessions","purchase_revenue","transactions"]:
            if col in df_nr.columns: df_nr[col] = df_nr[col].apply(safe_num)
        ret=df_nr[df_nr["new_vs_returning"]=="returning"]
        if not ret.empty:
            rp=ret["purchase_revenue"].sum()/tot_revenue*100 if tot_revenue else 0
            st.markdown(insight("✅", f"Returning Users = {rp:.1f}% من الإيرادات", "Loyalty Program + Personalized offers = رفع LTV.", "insight-green"), unsafe_allow_html=True)
    st.markdown(insight("✅", f"AOV مرتفع {fmt_currency(aov, 0)}", "Installment plans + messaging واضح = رفع CVR.", "insight-green"), unsafe_allow_html=True)
    st.markdown(insight("▲", "Cart مرتفع — Checkout منخفض", f"Cart: {fmt_number(tot_carts)} → Purchase: {fmt_number(tot_orders)}. Streamline الـ checkout = quick win.", "insight-blue"), unsafe_allow_html=True)
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    st.markdown(section_header("Summary Metrics", "", "#2A3050"), unsafe_allow_html=True)
    st.dataframe(pd.DataFrame({
        "Metric":["Sessions","Revenue","Orders","AOV","CVR","Bounce Rate","Cart Abandonment","Avg Session"],
        "Value":[fmt_number(tot_sessions),fmt_currency(tot_revenue),fmt_number(tot_orders),fmt_currency(aov,0),fmt_pct(cvr,2),fmt_pct(avg_bounce),fmt_pct(cart_abandon),f"{avg_session_m}:{avg_session_s:02d} min"],
        "Status":["✅","✅","✅","✅","⚠" if cvr<1 else "✅","⚠" if avg_bounce>50 else "✅","🔴" if cart_abandon>85 else "⚠","✅"],
    }), use_container_width=True, hide_index=True)
