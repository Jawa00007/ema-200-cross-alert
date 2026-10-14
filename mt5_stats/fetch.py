import asyncio
import json
import os
import sys
from datetime import datetime, timedelta, timezone

import pandas as pd
from metaapi_cloud_sdk import MetaApi

from . import config

CONNECT_TIMEOUT_SECONDS = 60


async def fetch_account_stats(api: MetaApi, account_id: str) -> dict:
    account = await api.metatrader_account_api.get_account(account_id)
    await account.wait_connected(timeout_in_seconds=CONNECT_TIMEOUT_SECONDS)

    connection = account.get_rpc_connection()
    await connection.connect()
    await connection.wait_synchronized(timeout_in_seconds=CONNECT_TIMEOUT_SECONDS)

    try:
        info = await connection.get_account_information()
        positions = await connection.get_positions()

        # This integration is read-only by design: we only ever call get_*
        # methods below, never an order-placing one. The investor-password
        # connection the user provisions in MetaApi is what actually makes
        # trade placement impossible at the broker level - this check just
        # flags it loudly if an account was provisioned with a trading
        # password instead of the investor password.
        if not info.get("investorMode", True):
            print(
                f"WARNING: account {account_id} is NOT connected with an investor "
                "(read-only) password - reprovision it in MetaApi using the "
                "investor password instead.",
                file=sys.stderr,
            )

        return {
            "balance": info["balance"],
            "equity": info["equity"],
            "margin": info["margin"],
            "free_margin": info["freeMargin"],
            "open_positions": len(positions),
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }
    finally:
        await connection.close()


async def run() -> dict:
    api = MetaApi(config.METAAPI_TOKEN)
    results = {}
    try:
        for acct in config.ACCOUNTS:
            try:
                results[acct["label"]] = await fetch_account_stats(api, acct["account_id"])
            except Exception as exc:  # noqa: BLE001 - one bad account shouldn't kill the run
                print(f"{acct['label']}: {exc}", file=sys.stderr)
    finally:
        api.close()
    return results


def append_account_history(results: dict) -> None:
    """Appends one row per account for this run, then prunes anything older
    than HISTORY_RETENTION_DAYS so the file stays bounded over time.
    """
    os.makedirs(config.DATA_DIR, exist_ok=True)
    now = datetime.now(timezone.utc)
    rows = [
        {"timestamp": now, "account": label, "balance": stats["balance"], "equity": stats["equity"], "margin": stats["margin"]}
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
    if not config.METAAPI_TOKEN or not config.ACCOUNTS:
        # Not configured yet is an expected, normal state (this feature is
        # optional) - not an error, so don't fail the whole workflow run
        # over it.
        print("METAAPI_TOKEN or account IDs not configured - skipping MT5 stats fetch.", file=sys.stderr)
        return 0

    results = asyncio.run(run())

    os.makedirs(config.DATA_DIR, exist_ok=True)
    with open(config.OUTPUT_PATH, "w") as f:
        json.dump(results, f, indent=2)

    if results:
        append_account_history(results)

    return 0 if results else 1


if __name__ == "__main__":
    sys.exit(main())
