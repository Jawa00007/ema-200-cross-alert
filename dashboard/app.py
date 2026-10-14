import json
import os
import sys

import pandas as pd
import streamlit as st

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from alert_bot import config  # noqa: E402
from mt5_stats import config as mt5_config  # noqa: E402

st.set_page_config(page_title="200 EMA Cross Monitor", layout="wide")
st.title("200 EMA Cross Monitor")


def load_state() -> dict:
    if not os.path.exists(config.STATE_PATH):
        return {}
    with open(config.STATE_PATH, "r") as f:
        return json.load(f)


def load_log() -> pd.DataFrame:
    if not os.path.exists(config.LOG_PATH):
        return pd.DataFrame(columns=["timestamp", "instrument", "direction", "close", "ema200"])
    return pd.read_csv(config.LOG_PATH)


def load_mt5_accounts() -> dict:
    if not os.path.exists(mt5_config.OUTPUT_PATH):
        return {}
    with open(mt5_config.OUTPUT_PATH, "r") as f:
        return json.load(f)


state = load_state()

if not state:
    st.info("No data yet - the GitHub Action hasn't run yet, or hasn't pushed data/ yet.")
else:
    rows = []
    for instrument, entry in state.items():
        close = entry["last_close"]
        ema = entry["last_ema200"]
        distance_pct = (close - ema) / ema * 100
        rows.append(
            {
                "Pair": instrument.upper(),
                "Price": round(close, 5),
                "EMA200": round(ema, 5),
                "Distance %": round(distance_pct, 3),
                "Side": entry["side"].upper(),
                "Updated (UTC)": entry["last_updated"],
            }
        )
    st.dataframe(pd.DataFrame(rows), width='stretch', hide_index=True)

st.subheader("Crossover log")
log_df = load_log()
if log_df.empty:
    st.caption("No crossovers recorded yet.")
else:
    st.dataframe(log_df.sort_values("timestamp", ascending=False), width='stretch', hide_index=True)

st.subheader("MT5 Accounts")
mt5_accounts = load_mt5_accounts()
if not mt5_accounts:
    st.caption("No MT5 account data yet - configure METAAPI_TOKEN and account IDs to enable this.")
else:
    mt5_rows = [
        {
            "Account": label,
            "Balance": round(stats["balance"], 2),
            "Equity": round(stats["equity"], 2),
            "Margin": round(stats["margin"], 2),
            "Free Margin": round(stats["free_margin"], 2),
            "Open Positions": stats["open_positions"],
            "Updated (UTC)": stats["last_updated"],
        }
        for label, stats in mt5_accounts.items()
    ]
    st.dataframe(pd.DataFrame(mt5_rows), width='stretch', hide_index=True)
