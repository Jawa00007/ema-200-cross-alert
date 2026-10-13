import pandas as pd
import requests

from . import config

BASE_URL = "https://api.tiingo.com/tiingo/fx"


def fetch_closes(ticker: str, resample_freq: str = None, limit: int = None) -> pd.Series:
    """Fetch recent historical closes for an FX ticker from Tiingo.

    Raises on HTTP errors or an empty response, which is how the Step 0
    gold-support probe (scripts/check_tiingo_gold.py) detects lack of support.
    """
    resample_freq = resample_freq or config.RESAMPLE_FREQ
    limit = limit or config.HISTORY_BARS

    resp = requests.get(
        f"{BASE_URL}/{ticker}/prices",
        params={"token": config.TIINGO_API_TOKEN, "resampleFreq": resample_freq},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    if not data:
        raise ValueError(f"Tiingo returned no data for ticker '{ticker}'")

    df = pd.DataFrame(data)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")
    return df["close"].tail(limit).reset_index(drop=True)
