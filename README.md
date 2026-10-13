# 200 EMA Cross Alert System

Watches XAUUSD, EURUSD, and GBPUSD on 5-minute candles for a price cross of
the 200-period EMA, and sends a Telegram alert the moment it happens. Runs
for free on a GitHub Actions schedule (no computer or paid server needed).

## 1. Create the Telegram bot

1. In Telegram, message **@BotFather**, send `/newbot`, and follow the prompts. Save the **HTTP API token** it gives you.
2. Message **@userinfobot**, press Start, and save the numeric chat ID it shows you.
3. Open your new bot's chat and press **Start** so it's allowed to message you.

## 2. Get a Tiingo API token

1. Sign up free at [tiingo.com](https://www.tiingo.com) and grab your API token from the account page.
2. Copy `.env.example` to `.env` and fill in `TIINGO_API_TOKEN`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`.
3. Install dependencies: `pip install -r requirements.txt`

## 3. Run the Step 0 gold check (do this before anything else)

```
python scripts/check_tiingo_gold.py
```

- If it prints real price data for xauusd: set `TIINGO_SUPPORTS_GOLD=true` in `.env` (and later as a GitHub secret).
- If it fails: leave `TIINGO_SUPPORTS_GOLD=false`, sign up for a free key at a metals spot-price API (e.g. metals-api.com) and put it in `GOLD_FALLBACK_API_KEY`. Gold's EMA will then build up incrementally over roughly a day of 5-minute runs instead of being computed from history immediately — this is expected, not a bug.

## 4. Local smoke test

```
python -m alert_bot.main
```

This fetches each instrument, computes/updates its EMA200, and writes `data/crossover_state.json`. No crossover has happened yet on the very first run, so no Telegram message is expected.

To force a test alert: open `data/crossover_state.json`, flip one instrument's `"side"` value (e.g. `"above"` to `"below"`), then rerun `python -m alert_bot.main`. You should get a Telegram message.

## 5. Deploy to GitHub Actions

1. Push this repo to GitHub.
2. In the repo's **Settings → Secrets and variables → Actions**, add: `TIINGO_API_TOKEN`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `GOLD_FALLBACK_API_KEY` (if used), `TIINGO_SUPPORTS_GOLD` (`true` or `false`).
3. Go to the **Actions** tab, select "EMA 200 Cross Alert", and run it once manually (`Run workflow`) to confirm it succeeds and commits an update to `data/`.
4. After that it runs automatically every 5 minutes via the cron schedule in `.github/workflows/ema_alert.yml`.

Note: GitHub's free scheduled runs can occasionally lag a few extra minutes under high load — expected behavior for a free cron, not a bug in this code.

## 6. iPhone notification settings

- iPhone Settings → Telegram → Notifications: enable Banners, Sounds, Badges.
- If you use Focus modes / Do Not Disturb: iPhone Settings → Focus → (your mode) → Apps, allow Telegram through, or mark its notifications as Time Sensitive.

## 7. Dashboard

```
streamlit run dashboard/app.py
```

Shows current price/EMA200/distance per pair and the crossover log. Deploy the same repo on [Streamlit Community Cloud](https://streamlit.io/cloud) pointing at `dashboard/app.py` for a hosted, mobile-friendly view — it reads straight from the `data/` files the GitHub Action keeps updated.
