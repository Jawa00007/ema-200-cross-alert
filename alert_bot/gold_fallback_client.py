import requests

from . import config

# Used only when scripts/check_tiingo_gold.py confirms Tiingo does not return
# xauusd data. metals-api.com's free tier gives a latest spot price, not
# historical candles, which is why main.py builds gold's EMA incrementally
# instead of recomputing it from history each run.
LATEST_URL = "https://api.metals-api.com/v1/latest"


def fetch_latest_gold_price() -> float:
    resp = requests.get(
        LATEST_URL,
        params={"access_key": config.GOLD_FALLBACK_API_KEY, "base": "USD", "symbols": "XAU"},
        timeout=30,
    )
    resp.raise_for_status()
    payload = resp.json()
    if "rates" not in payload or "XAU" not in payload["rates"]:
        raise ValueError(f"Gold fallback API error: {payload}")
    # metals-api returns ounces-of-gold-per-USD; invert to get USD per ounce.
    return 1.0 / payload["rates"]["XAU"]
