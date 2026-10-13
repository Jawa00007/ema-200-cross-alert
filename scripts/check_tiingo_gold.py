"""Step 0 from the plan: run this once to find out whether Tiingo's FX
endpoint actually returns data for xauusd on your account.

Usage:
    python scripts/check_tiingo_gold.py

Reads TIINGO_API_TOKEN from .env or the environment.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from alert_bot import tiingo_client  # noqa: E402


def main() -> int:
    try:
        closes = tiingo_client.fetch_closes("xauusd", limit=5)
        print("Tiingo DOES return data for xauusd:")
        print(closes)
        print("\nSet TIINGO_SUPPORTS_GOLD=true in your .env and in the GitHub repo secret.")
        return 0
    except Exception as exc:  # noqa: BLE001
        print(f"Tiingo does NOT support xauusd on this account (or a network/token issue): {exc}")
        print("\nKeep TIINGO_SUPPORTS_GOLD=false and set GOLD_FALLBACK_API_KEY instead.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
