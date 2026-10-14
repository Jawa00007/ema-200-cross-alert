import pandas as pd


def compute_ema_series(closes: pd.Series, period: int = 200) -> pd.Series:
    return closes.ewm(span=period, adjust=False).mean()


def latest_close_and_ema(closes: pd.Series, period: int = 200):
    ema_series = compute_ema_series(closes, period)
    return float(closes.iloc[-1]), float(ema_series.iloc[-1])


def side_of(close: float, ema: float) -> str:
    return "above" if close >= ema else "below"
