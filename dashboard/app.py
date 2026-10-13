import json
import os
import sys

import pandas as pd
import streamlit as st

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from alert_bot import config  # noqa: E402

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


state = load_state()

if not state:
    st.info("No data yet - the GitHub Action hasn't run yet, or hasn't pushed data/ yet.")
else:
    rows = []
    for instrument, entry in state.items():
        close = entry["last_close"]
        ema = entry["last_ema200"]
        distance_pct = (close - ema) / ema * 100
        warming_up = entry.get("warm_up_count") is not None and entry["warm_up_count"] < 200
        rows.append(
            {
                "Pair": instrument.upper(),
                "Price": round(close, 5),
                "EMA200": round(ema, 5),
                "Distance %": round(distance_pct, 3),
                "Side": entry["side"].upper(),
                "Updated (UTC)": entry["last_updated"],
                "Warming up": "Yes" if warming_up else "",
            }
        )
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

st.subheader("Crossover log")
log_df = load_log()
if log_df.empty:
    st.caption("No crossovers recorded yet.")
else:
    st.dataframe(log_df.sort_values("timestamp", ascending=False), use_container_width=True, hide_index=True)
