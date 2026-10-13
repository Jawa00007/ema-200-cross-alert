import requests

from . import config

_session = requests.Session()


def send_message(text: str) -> None:
    if not config.TELEGRAM_BOT_TOKEN or not config.TELEGRAM_CHAT_ID:
        raise RuntimeError("Telegram credentials are not configured")
    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
    resp = _session.post(url, data={"chat_id": config.TELEGRAM_CHAT_ID, "text": text}, timeout=15)
    resp.raise_for_status()
