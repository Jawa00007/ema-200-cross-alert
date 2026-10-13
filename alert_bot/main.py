import sys

from . import config, ema as ema_mod, gold_fallback_client, state as state_mod, telegram_notify, tiingo_client

WARM_UP_MIN_SAMPLES = 30


def process_instrument(instrument: str, cur_state: dict):
    """Updates cur_state in place for this instrument. Returns an alert dict if a crossover fired."""
    use_tiingo = instrument != "xauusd" or config.TIINGO_SUPPORTS_GOLD
    prior = cur_state.get(instrument)

    if use_tiingo:
        closes = tiingo_client.fetch_closes(instrument)
        close, ema = ema_mod.latest_close_and_ema(closes, config.EMA_PERIOD)
        warm_up_count = None
    else:
        close = gold_fallback_client.fetch_latest_gold_price()
        warm_up_count = prior.get("warm_up_count", 0) if prior else 0
        prev_ema = prior["last_ema200"] if prior else None
        if prev_ema is None or warm_up_count < WARM_UP_MIN_SAMPLES:
            # Not enough history yet for a real EMA200 - seed with a running average.
            prev_avg = prev_ema if prev_ema is not None else close
            ema = (prev_avg * warm_up_count + close) / (warm_up_count + 1)
            warm_up_count += 1
        else:
            ema = ema_mod.incremental_ema(prev_ema, close, config.EMA_PERIOD)
            warm_up_count += 1

    side = ema_mod.side_of(close, ema)

    alert = None
    if prior is not None and prior["side"] != side:
        direction = "crossed ABOVE" if side == "above" else "crossed BELOW"
        alert = {"instrument": instrument, "direction": direction, "close": close, "ema": ema}

    state_mod.update_instrument_state(cur_state, instrument, close, ema, side, warm_up_count)
    return alert


def main() -> int:
    cur_state = state_mod.load_state()
    alerts = []
    errors = []

    for instrument in config.INSTRUMENTS:
        try:
            alert = process_instrument(instrument, cur_state)
            if alert:
                alerts.append(alert)
        except Exception as exc:  # noqa: BLE001 - one bad instrument shouldn't kill the run
            errors.append(f"{instrument}: {exc}")

    state_mod.save_state(cur_state)

    for alert in alerts:
        text = (
            f"\U0001F6A8 {alert['instrument'].upper()} {alert['direction']} the 200 EMA\n"
            f"Close: {alert['close']:.5f}\nEMA200: {alert['ema']:.5f}"
        )
        telegram_notify.send_message(text)
        state_mod.append_log(alert["instrument"], alert["direction"], alert["close"], alert["ema"])

    if errors:
        print("Errors during run:\n" + "\n".join(errors), file=sys.stderr)

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
