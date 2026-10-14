import json
import os
from datetime import datetime, timedelta, timezone

import pandas as pd

from . import config


def load_state() -> dict:
    if not os.path.exists(config.STATE_PATH):
        return {}
    with open(config.STATE_PATH, "r") as f:
        return json.load(f)


def save_state(state: dict) -> None:
    os.makedirs(config.DATA_DIR, exist_ok=True)
    with open(config.STATE_PATH, "w") as f:
        json.dump(state, f, indent=2)


def update_instrument_state(state: dict, instrument: str, close: float, ema: float, side: str) -> dict:
    state[instrument] = {
        "side": side,
        "last_close": close,
        "last_ema200": ema,
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }
    return state


def append_log(instrument: str, direction: str, close: float, ema: float) -> None:
    os.makedirs(config.DATA_DIR, exist_ok=True)
    is_new = not os.path.exists(config.LOG_PATH)
    with open(config.LOG_PATH, "a") as f:
        if is_new:
            f.write("timestamp,instrument,direction,close,ema200\n")
        f.write(f"{datetime.now(timezone.utc).isoformat()},{instrument},{direction},{close},{ema}\n")


def append_price_history(rows: list[dict]) -> None:
    """Appends one row per instrument for this run, then prunes anything
    older than HISTORY_RETENTION_DAYS so the file (and the repo) stay bounded
    as the bot keeps running every 5 minutes, forever.
    """
    os.makedirs(config.DATA_DIR, exist_ok=True)
    now = datetime.now(timezone.utc)
    new_df = pd.DataFrame(rows)
    new_df["timestamp"] = pd.to_datetime(new_df["timestamp"], utc=True)

    if os.path.exists(config.PRICE_HISTORY_PATH):
        existing = pd.read_csv(config.PRICE_HISTORY_PATH)
        existing["timestamp"] = pd.to_datetime(existing["timestamp"], utc=True)
        cutoff = now - timedelta(days=config.HISTORY_RETENTION_DAYS)
        existing = existing[existing["timestamp"] >= cutoff]
        combined = pd.concat([existing, new_df], ignore_index=True)
    else:
        combined = new_df

    combined.to_csv(config.PRICE_HISTORY_PATH, index=False)
