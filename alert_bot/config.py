import os

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

TIINGO_API_TOKEN = os.environ.get("TIINGO_API_TOKEN", "")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
GOLD_FALLBACK_API_KEY = os.environ.get("GOLD_FALLBACK_API_KEY", "")

# Flip to true (env var "true") once scripts/check_tiingo_gold.py confirms
# Tiingo actually returns xauusd data on your account. Until then, gold uses
# gold_fallback_client.py plus an incrementally-built EMA instead.
TIINGO_SUPPORTS_GOLD = os.environ.get("TIINGO_SUPPORTS_GOLD", "false").lower() == "true"

EMA_PERIOD = 200
RESAMPLE_FREQ = "5min"
HISTORY_BARS = 500

INSTRUMENTS = ["eurusd", "gbpusd", "xauusd"]

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
STATE_PATH = os.path.join(DATA_DIR, "crossover_state.json")
LOG_PATH = os.path.join(DATA_DIR, "crossover_log.csv")
