import sys

from . import config, ema as ema_mod, state as state_mod, telegram_notify, tiingo_client


def process_instrument(instrument: str, cur_state: dict):
    """Updates cur_state in place for this instrument. Returns an alert dict if a crossover fired."""
    prior = cur_state.get(instrument)

    closes = tiingo_client.fetch_closes(instrument)
    close, ema = ema_mod.latest_close_and_ema(closes, config.EMA_PERIOD)
    side = ema_mod.side_of(close, ema)

    alert = None
    if prior is not None and prior["side"] != side:
        direction = "crossed ABOVE" if side == "above" else "crossed BELOW"
        alert = {"instrument": instrument, "direction": direction, "close": close, "ema": ema}

    state_mod.update_instrument_state(cur_state, instrument, close, ema, side)
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
        try:
            text = (
                f"\U0001F6A8 {alert['instrument'].upper()} {alert['direction']} the 200 EMA\n"
                f"Close: {alert['close']:.5f}\nEMA200: {alert['ema']:.5f}"
            )
            telegram_notify.send_message(text)
            state_mod.append_log(alert["instrument"], alert["direction"], alert["close"], alert["ema"])
        except Exception as exc:  # noqa: BLE001 - a failed send shouldn't block state from being saved
            errors.append(f"{alert['instrument']} alert: {exc}")

    if errors:
        print("Errors during run:\n" + "\n".join(errors), file=sys.stderr)

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
