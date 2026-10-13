import pandas as pd


def compute_ema_series(closes: pd.Series, period: int = 200) -> pd.Series:
    return closes.ewm(span=period, adjust=False).mean()


def latest_close_and_ema(closes: pd.Series, period: int = 200):
    ema_series = compute_ema_series(closes, period)
    return float(closes.iloc[-1]), float(ema_series.iloc[-1])


def incremental_ema(prev_ema: float, price: float, period: int = 200) -> float:
    k = 2 / (period + 1)
    return price * k + prev_ema * (1 - k)


def side_of(close: float, ema: float) -> str:
    return "above" if close >= ema else "below"
