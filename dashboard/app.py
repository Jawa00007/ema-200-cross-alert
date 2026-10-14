import json
import os
import sys
from datetime import datetime, timedelta, timezone

import pandas as pd
import streamlit as st

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from alert_bot import config  # noqa: E402
from mt5_stats import config as mt5_config  # noqa: E402

import charts  # noqa: E402

st.set_page_config(page_title="200 EMA Cross Monitor", layout="wide")
st.title("200 EMA Cross Monitor")

RANGE_OPTIONS = {
    "Last 24 hours": timedelta(hours=24),
    "Last 3 days": timedelta(days=3),
    "Last 7 days": timedelta(days=7),
    "Last 14 days": timedelta(days=14),
}


def format_price(value: float) -> str:
    if value >= 1000:
        return f"{value:,.2f}"
    if value >= 10:
        return f"{value:,.3f}"
    return f"{value:,.5f}"


def load_state() -> dict:
    if not os.path.exists(config.STATE_PATH):
        return {}
    with open(config.STATE_PATH, "r") as f:
        return json.load(f)


def load_log() -> pd.DataFrame:
    if not os.path.exists(config.LOG_PATH):
        return pd.DataFrame(columns=["timestamp", "instrument", "direction", "close", "ema200"])
    return pd.read_csv(config.LOG_PATH)


def load_price_history() -> pd.DataFrame:
    if not os.path.exists(config.PRICE_HISTORY_PATH):
        return pd.DataFrame(columns=["timestamp", "instrument", "close", "ema200"])
    df = pd.read_csv(config.PRICE_HISTORY_PATH)
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    return df


def load_mt5_accounts() -> dict:
    if not os.path.exists(mt5_config.OUTPUT_PATH):
        return {}
    with open(mt5_config.OUTPUT_PATH, "r") as f:
        return json.load(f)


def load_mt5_history() -> pd.DataFrame:
    if not os.path.exists(mt5_config.HISTORY_PATH):
        return pd.DataFrame(columns=["timestamp", "account", "balance", "equity", "margin"])
    df = pd.read_csv(mt5_config.HISTORY_PATH)
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    return df


state = load_state()
price_history = load_price_history()
log_df = load_log()
mt5_accounts = load_mt5_accounts()
mt5_history = load_mt5_history()

if not state:
    st.info("No data yet - the GitHub Action hasn't run yet, or hasn't pushed data/ yet.")
    st.stop()

range_label = st.selectbox("Date range", list(RANGE_OPTIONS.keys()), index=1)
cutoff = datetime.now(timezone.utc) - RANGE_OPTIONS[range_label]

st.subheader("Market Overview")
instruments = list(state.keys())
cols = st.columns(len(instruments))
for col, instrument in zip(cols, instruments):
    entry = state[instrument]
    close = entry["last_close"]
    ema = entry["last_ema200"]
    distance_pct = (close - ema) / ema * 100
    with col:
        st.metric(
            label=instrument.upper(),
            value=format_price(close),
            delta=f"{distance_pct:+.3f}% vs EMA200",
        )

st.caption(f"Prices and EMA200 as of the most recent check. Charts below show {range_label.lower()}.")

tabs = st.tabs([i.upper() for i in instruments])
for tab, instrument in zip(tabs, instruments):
    with tab:
        hist = price_history[(price_history["instrument"] == instrument) & (price_history["timestamp"] >= cutoff)]
        if len(hist) < 2:
            st.caption("Not enough history yet to chart - check back after a few more runs.")
        else:
            hist = hist.sort_values("timestamp")
            st.altair_chart(charts.price_ema_chart(hist), use_container_width=True)
            st.caption("🔵 Price  ·  ⚪┄ EMA200 (dashed)")

            dist = hist.copy()
            dist["distance_pct"] = (dist["close"] - dist["ema200"]) / dist["ema200"] * 100
            st.altair_chart(charts.distance_bar_chart(dist[["timestamp", "distance_pct"]]), use_container_width=True)

st.subheader("Recent Crossover Alerts")
if log_df.empty:
    st.caption("No crossovers recorded yet.")
else:
    display_log = log_df.sort_values("timestamp", ascending=False).copy()
    display_log["direction"] = display_log["direction"].apply(
        lambda d: f"🟢 {d}" if "ABOVE" in d else f"🔴 {d}"
    )
    st.dataframe(display_log, width="stretch", hide_index=True)

st.subheader("MT5 Accounts")
if not mt5_accounts:
    st.caption("No MT5 account data yet - configure METAAPI_TOKEN and account IDs to enable this.")
else:
    mt5_cols = st.columns(len(mt5_accounts))
    for col, (label, stats) in zip(mt5_cols, mt5_accounts.items()):
        floating_pnl = stats["equity"] - stats["balance"]
        with col:
            st.metric(label=f"{label} - Balance", value=f"{stats['balance']:,.2f}")
            st.metric(label=f"{label} - Equity", value=f"{stats['equity']:,.2f}", delta=f"{floating_pnl:+,.2f}")
            st.caption(
                f"Margin {stats['margin']:,.2f} · Free margin {stats['free_margin']:,.2f} · "
                f"{stats['open_positions']} open position(s) · Updated {stats['last_updated']}"
            )

    if not mt5_history.empty:
        for label in mt5_accounts.keys():
            acct_hist = mt5_history[(mt5_history["account"] == label) & (mt5_history["timestamp"] >= cutoff)]
            if len(acct_hist) >= 2:
                st.markdown(f"**{label}**")
                st.altair_chart(charts.equity_chart(acct_hist.sort_values("timestamp")), use_container_width=True)
                st.caption("🔵 Balance  ·  🟠 Equity")
