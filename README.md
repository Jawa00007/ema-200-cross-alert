# 200 EMA Cross Alert System

Watches XAUUSD, EURUSD, GBPUSD, USDJPY, and BTCUSD on 5-minute candles for a
price cross of the 200-period EMA, and sends a Telegram alert the moment it
happens. Runs for free on a GitHub Actions schedule (no computer or paid
server needed).

## 1. Create the Telegram bot

1. In Telegram, message **@BotFather**, send `/newbot`, and follow the prompts. Save the **HTTP API token** it gives you.
2. Message **@userinfobot**, press Start, and save the numeric chat ID it shows you.
3. Open your new bot's chat and press **Start** so it's allowed to message you.

## 2. Get a Tiingo API token

1. Sign up free at [tiingo.com](https://www.tiingo.com) and grab your API token from the account page.
2. Copy `.env.example` to `.env` and fill in `TIINGO_API_TOKEN`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`.
3. Install dependencies: `pip install -r requirements.txt`

## 3. Local smoke test

```
python -m alert_bot.main
```

This fetches each instrument, computes/updates its EMA200, and writes `data/crossover_state.json`. No crossover has happened yet on the very first run, so no Telegram message is expected.

To force a test alert: open `data/crossover_state.json`, flip one instrument's `"side"` value (e.g. `"above"` to `"below"`), then rerun `python -m alert_bot.main`. You should get a Telegram message.

## 4. Deploy to GitHub Actions

1. Push this repo to GitHub.
2. In the repo's **Settings → Secrets and variables → Actions**, add: `TIINGO_API_TOKEN`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`.
3. Go to the **Actions** tab, select "EMA 200 Cross Alert", and run it once manually (`Run workflow`) to confirm it succeeds and commits an update to `data/`.
4. After that it runs automatically every 5 minutes via the cron schedule in `.github/workflows/ema_alert.yml`.

Note: GitHub's free scheduled runs can occasionally lag a few extra minutes under high load — expected behavior for a free cron, not a bug in this code.

## 5. iPhone notification settings

- iPhone Settings → Telegram → Notifications: enable Banners, Sounds, Badges.
- If you use Focus modes / Do Not Disturb: iPhone Settings → Focus → (your mode) → Apps, allow Telegram through, or mark its notifications as Time Sensitive.

## 6. MT5 account stats (optional)

Shows balance/equity/gain/drawdown for your MT5 account(s) on the dashboard, via [Myfxbook](https://www.myfxbook.com) (free, no local terminal needed to stay running):

1. Sign up at myfxbook.com, go to **Portfolio → Add Account → MetaTrader 5**, and choose the **"Auto Update"** connection method (free, server-side) — not "Live (Verified)" ($5/mo) or "Expert Advisor" (requires your terminal to stay open).
2. Use your account's **investor (read-only) password**, never the full trading password.
3. Add `MYFXBOOK_EMAIL` and `MYFXBOOK_PASSWORD` to `.env` (local) and as GitHub repo secrets (deployed) — this is your real Myfxbook login, not a scoped API token, so treat it with the same care as any other password.
4. Test locally: `python -m mt5_stats.fetch` — writes `data/mt5_accounts.json`.

This runs on its own hourly schedule (`.github/workflows/mt5_stats.yml`), separate from the 5-minute EMA check, to stay well within Myfxbook's free API rate limit. Balance/equity don't need 5-minute granularity the way price crossovers do.

**Important if you have a prop-firm funded account**: check your prop firm's rules before ever connecting a real funded account to Myfxbook (or any third-party tracker) — some firms prohibit external connections even when read-only, and violating that can void the account. This project only ever reads account data (never places trades), but that's a separate question from what your specific prop firm's terms allow.

## 7. Dashboard

```
streamlit run dashboard/app.py
```

Shows current price/EMA200/distance per pair, the crossover log, and MT5 account stats if configured. Deploy the same repo on [Streamlit Community Cloud](https://streamlit.io/cloud) pointing at `dashboard/app.py` for a hosted, mobile-friendly view — it reads straight from the `data/` files the GitHub Actions keep updated.

## Troubleshooting: scheduled runs never firing

If `gh run list` shows only `workflow_dispatch` runs and never a `schedule`-triggered one, even hours after the workflow was first pushed, the cron registration can get stuck despite valid YAML and an `"active"` workflow state. Fix: `gh workflow disable <file>` followed by `gh workflow enable <file>` for the affected workflow(s) forces GitHub to re-register the schedule. Verify afterward with `gh run list --workflow <file> --json event` once enough time has passed for the next scheduled tick.
