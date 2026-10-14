import os

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

METAAPI_TOKEN = os.environ.get("METAAPI_TOKEN", "")

_raw_accounts = [
    (os.environ.get("MT5_ACCOUNT_1_LABEL", "Account 1"), os.environ.get("METAAPI_ACCOUNT_ID_1", "")),
    (os.environ.get("MT5_ACCOUNT_2_LABEL", "Account 2"), os.environ.get("METAAPI_ACCOUNT_ID_2", "")),
]
ACCOUNTS = [{"label": label, "account_id": account_id} for label, account_id in _raw_accounts if account_id]

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
OUTPUT_PATH = os.path.join(DATA_DIR, "mt5_accounts.json")
