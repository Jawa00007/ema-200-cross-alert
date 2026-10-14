import pandas as pd
import requests

from . import config

FX_BASE_URL = "https://api.tiingo.com/tiingo/fx"
CRYPTO_BASE_URL = "https://api.tiingo.com/tiingo/crypto/prices"


def fetch_closes(ticker: str, resample_freq: str = None, limit: int = None) -> pd.Series:
    """Fetch recent historical closes for an FX ticker from Tiingo."""
    resample_freq = resample_freq or config.RESAMPLE_FREQ
    limit = limit or config.HISTORY_BARS

    resp = requests.get(
        f"{FX_BASE_URL}/{ticker}/prices",
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


def fetch_crypto_closes(ticker: str, resample_freq: str = None, limit: int = None) -> pd.Series:
    """Fetch recent historical closes for a crypto ticker from Tiingo.

    Tiingo's crypto endpoint has a different response shape than its FX
    endpoint: a list with one object per requested ticker, each holding a
    nested "priceData" list of candles.
    """
    resample_freq = resample_freq or config.RESAMPLE_FREQ
    limit = limit or config.HISTORY_BARS

    resp = requests.get(
        CRYPTO_BASE_URL,
        params={"tickers": ticker, "resampleFreq": resample_freq, "token": config.TIINGO_API_TOKEN},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    if not data or not data[0].get("priceData"):
        raise ValueError(f"Tiingo returned no crypto data for ticker '{ticker}'")

    df = pd.DataFrame(data[0]["priceData"])
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")
    return df["close"].tail(limit).reset_index(drop=True)
