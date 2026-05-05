import requests
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta

WINDSOR_BASE = "https://connectors.windsor.ai/all"


def get_windsor_data(
    api_key: str,
    fields: list[str],
    date_preset: str = "last_30d",
    date_from: str = None,
    date_to: str = None,
    connector: str = "googleanalytics4",
) -> pd.DataFrame:
    """Fetch data from Windsor.ai API and return as DataFrame."""

    params = {
        "api_key": api_key,
        "connector": connector,
        "fields": ",".join(fields),
        "date_preset": date_preset,
    }

    if date_from:
        params["date_from"] = date_from
        params.pop("date_preset", None)
    if date_to:
        params["date_to"] = date_to

    try:
        resp = requests.get(WINDSOR_BASE, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        if isinstance(data, dict) and "data" in data:
            rows = data["data"]
        elif isinstance(data, list):
            rows = data
        else:
            rows = []

        if not rows:
            return pd.DataFrame()

        df = pd.DataFrame(rows)
        return df

    except requests.exceptions.RequestException as e:
        st.error(f"Windsor API Error: {e}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Data Error: {e}")
        return pd.DataFrame()


def safe_num(val, default=0):
    """Safely convert to number."""
    try:
        return float(val) if val is not None else default
    except (TypeError, ValueError):
        return default


def fmt_currency(val, decimals=1):
    """Format as Egyptian Pounds."""
    v = safe_num(val)
    if v >= 1_000_000:
        return f"{v/1_000_000:.{decimals}f}M ج"
    elif v >= 1_000:
        return f"{v/1_000:.{decimals}f}K ج"
    return f"{v:,.0f} ج"


def fmt_number(val, decimals=0):
    """Format large numbers."""
    v = safe_num(val)
    if v >= 1_000_000:
        return f"{v/1_000_000:.1f}M"
    elif v >= 1_000:
        return f"{v/1_000:.1f}K"
    return f"{v:,.{decimals}f}"


def fmt_pct(val, decimals=1):
    """Format as percentage."""
    v = safe_num(val)
    return f"{v:.{decimals}f}%"


def pct_change_color(val):
    """Return color based on positive/negative change."""
    v = safe_num(val)
    if v > 0:
        return "#1D9E75"
    elif v < 0:
        return "#D85A30"
    return "#888780"
