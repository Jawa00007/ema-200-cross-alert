"""Parses an MT5 Strategy Tester .htm report into a structured backtest log.

Usage: python ea/analyze_backtest.py <path-to-report.htm> <run_label>

Appends one row per entry trade (grouping partial-close exits together) to
ea/backtest_log.csv, plus prints the headline summary stats, so each
backtest run is comparable against earlier ones over time.
"""
import re
import sys
from datetime import datetime, timezone

import pandas as pd


def parse_report(path: str) -> tuple[dict, pd.DataFrame]:
    tables = pd.read_html(path, encoding="utf-16")
    t0, t1 = tables[0], tables[1]

    def cell(row_label: str, col_offset: int = 3) -> str:
        row = t0.index[t0[0] == row_label]
        if len(row) == 0:
            return ""
        return str(t0.iloc[row[0], col_offset])

    summary = {
        "symbol": cell("Symbol:"),
        "period": cell("Period:"),
        "total_net_profit": cell("Total Net Profit:"),
        "profit_factor": cell("Profit Factor:"),
        "expected_payoff": cell("Expected Payoff:", 7),
        "sharpe_ratio": cell("Recovery Factor:", 7),
        "max_equity_drawdown_pct": cell("Equity Drawdown Maximal:", 7),
        "total_trades": cell("Total Trades:"),
        "short_trades_won_pct": cell("Short Trades (won %):", 7),
        "long_trades_won_pct": cell("Long Trades (won %):", 11),
    }

    deals_start = t1.index[t1[0] == "Deals"][0]
    header_row = deals_start + 1
    data = t1.iloc[header_row + 1:].copy()
    data.columns = [
        "time", "deal", "symbol", "type", "dir", "volume", "price",
        "order", "commission", "swap", "profit", "balance", "comment",
    ]
    data = data.dropna(subset=["time"])
    data["profit_num"] = (
        data["profit"].astype(str).str.replace(" ", "").str.replace("\xa0", "").astype(float)
    )
    data["time"] = pd.to_datetime(data["time"], format="%Y.%m.%d %H:%M:%S")
    return summary, data


def deals_to_trades(deals: pd.DataFrame) -> pd.DataFrame:
    """Groups each entry deal with its (possibly multiple, due to partial
    closes) exit deals into one row per trade.
    """
    trades = []
    current = None
    for _, row in deals.iterrows():
        if row["dir"] == "in":
            if current:
                trades.append(current)
            setup_type = ""
            if isinstance(row["comment"], str):
                m = re.search(r"\b(REV|BRK)\b", row["comment"])
                if m:
                    setup_type = m.group(1)
            current = {
                "entry_time": row["time"],
                "direction": row["type"],
                "setup_type": setup_type,
                "entry_price": row["price"],
                "volume": row["volume"],
                "exit_time": None,
                "exit_price": None,
                "total_profit": 0.0,
                "exit_reason": "",
            }
        elif row["dir"] == "out" and current is not None:
            current["exit_time"] = row["time"]
            current["exit_price"] = row["price"]
            current["total_profit"] += row["profit_num"]
            if isinstance(row["comment"], str) and row["comment"].strip():
                current["exit_reason"] = row["comment"]
    if current:
        trades.append(current)
    return pd.DataFrame(trades)


def main():
    report_path = sys.argv[1]
    run_label = sys.argv[2] if len(sys.argv) > 2 else "unlabeled"

    summary, deals = parse_report(report_path)
    trades = deals_to_trades(deals)

    log_path = "ea/backtest_log.csv"
    now = datetime.now(timezone.utc).isoformat()
    trades.insert(0, "run_label", run_label)
    trades.insert(1, "run_timestamp", now)

    try:
        existing = pd.read_csv(log_path)
        combined = pd.concat([existing, trades], ignore_index=True)
    except FileNotFoundError:
        combined = trades
    combined.to_csv(log_path, index=False)

    print("=== Summary ===")
    for k, v in summary.items():
        print(f"{k}: {v}")
    print(f"\nWrote {len(trades)} trades to {log_path} (run_label={run_label})")


if __name__ == "__main__":
    main()
