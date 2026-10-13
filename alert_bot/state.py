import json
import os
from datetime import datetime, timezone

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


def update_instrument_state(state: dict, instrument: str, close: float, ema: float, side: str, warm_up_count=None) -> dict:
    entry = {
        "side": side,
        "last_close": close,
        "last_ema200": ema,
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }
    if warm_up_count is not None:
        entry["warm_up_count"] = warm_up_count
    state[instrument] = entry
    return state


def append_log(instrument: str, direction: str, close: float, ema: float) -> None:
    os.makedirs(config.DATA_DIR, exist_ok=True)
    is_new = not os.path.exists(config.LOG_PATH)
    with open(config.LOG_PATH, "a") as f:
        if is_new:
            f.write("timestamp,instrument,direction,close,ema200\n")
        f.write(f"{datetime.now(timezone.utc).isoformat()},{instrument},{direction},{close},{ema}\n")
