import os

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

MYFXBOOK_EMAIL = os.environ.get("MYFXBOOK_EMAIL", "")
MYFXBOOK_PASSWORD = os.environ.get("MYFXBOOK_PASSWORD", "")

HISTORY_RETENTION_DAYS = 14

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
OUTPUT_PATH = os.path.join(DATA_DIR, "mt5_accounts.json")
HISTORY_PATH = os.path.join(DATA_DIR, "mt5_history.csv")
