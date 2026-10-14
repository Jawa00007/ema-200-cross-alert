import json
import os
import sys
from datetime import datetime, timedelta, timezone

import pandas as pd

from . import config, myfxbook_client


def _to_float(value) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def fetch_all_accounts() -> dict:
    session = myfxbook_client.login(config.MYFXBOOK_EMAIL, config.MYFXBOOK_PASSWORD)
    try:
        accounts = myfxbook_client.get_my_accounts(session)
    finally:
        myfxbook_client.logout(session)

    now = datetime.now(timezone.utc).isoformat()
    results = {}
    for acct in accounts:
        label = acct.get("name") or str(acct.get("id", "account"))
        results[label] = {
            "balance": _to_float(acct.get("balance")),
            "equity": _to_float(acct.get("equity")),
            "gain_pct": _to_float(acct.get("gain")),
            "drawdown_pct": _to_float(acct.get("drawdown")),
            "demo": bool(acct.get("demo")),
            "last_updated": now,
        }
    return results


def append_account_history(results: dict) -> None:
    """Appends one row per account for this run, then prunes anything older
    than HISTORY_RETENTION_DAYS so the file stays bounded over time.
    """
    os.makedirs(config.DATA_DIR, exist_ok=True)
    now = datetime.now(timezone.utc)
    rows = [
        {
            "timestamp": now,
            "account": label,
            "balance": stats["balance"],
            "equity": stats["equity"],
            "gain_pct": stats["gain_pct"],
            "drawdown_pct": stats["drawdown_pct"],
        }
        for label, stats in results.items()
    ]
    new_df = pd.DataFrame(rows)
    new_df["timestamp"] = pd.to_datetime(new_df["timestamp"], utc=True)

    if os.path.exists(config.HISTORY_PATH):
        existing = pd.read_csv(config.HISTORY_PATH)
        existing["timestamp"] = pd.to_datetime(existing["timestamp"], utc=True)
        cutoff = now - timedelta(days=config.HISTORY_RETENTION_DAYS)
        existing = existing[existing["timestamp"] >= cutoff]
        combined = pd.concat([existing, new_df], ignore_index=True)
    else:
        combined = new_df

    combined.to_csv(config.HISTORY_PATH, index=False)


def main() -> int:
    if not config.MYFXBOOK_EMAIL or not config.MYFXBOOK_PASSWORD:
        # Not configured yet is an expected, normal state (this feature is
        # optional) - not an error, so don't fail the whole workflow run
        # over it.
        print("MYFXBOOK_EMAIL or MYFXBOOK_PASSWORD not configured - skipping MT5 stats fetch.", file=sys.stderr)
        return 0

    try:
        results = fetch_all_accounts()
    except Exception as exc:  # noqa: BLE001
        print(f"Myfxbook fetch failed: {exc}", file=sys.stderr)
        return 1

    os.makedirs(config.DATA_DIR, exist_ok=True)
    with open(config.OUTPUT_PATH, "w") as f:
        json.dump(results, f, indent=2)

    if results:
        append_account_history(results)

    return 0 if results else 1


if __name__ == "__main__":
    sys.exit(main())
