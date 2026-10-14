import os

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

TIINGO_API_TOKEN = os.environ.get("TIINGO_API_TOKEN", "")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

EMA_PERIOD = 200
RESAMPLE_FREQ = "5min"
HISTORY_BARS = 500

FX_INSTRUMENTS = ["eurusd", "gbpusd", "xauusd", "usdjpy"]
CRYPTO_INSTRUMENTS = ["btcusd"]
INSTRUMENTS = FX_INSTRUMENTS + CRYPTO_INSTRUMENTS

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
STATE_PATH = os.path.join(DATA_DIR, "crossover_state.json")
LOG_PATH = os.path.join(DATA_DIR, "crossover_log.csv")
