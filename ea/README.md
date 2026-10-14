# HawkSR_M15_M1_EA

Mechanical interpretation of a gold scalping strategy from a Hindi/Hinglish
trading class (support/resistance drawn on M15, refined on M5, executed on
M1). This EA places real trades automatically - **demo-test before ever
considering live use.**

## Strategy rules (as implemented)

- **Levels**: M15 confirmed fractals (swing highs/lows) mark support and
  resistance. "Next swing" above/below the entry price becomes TP1; the
  swing after that becomes TP2.
- **Reversal entry**: price's rejection candle (`p`) touches a level with a
  long wick in the rejection direction; the next candle (`c`) confirms by
  closing beyond `p`'s body. SL sits just beyond `p`'s wick (the rejection
  candle, not the confirmation candle) - an ATR-scaled buffer.
- **Breakout entry**: a strong/large-body candle closes beyond a level -
  entry happens immediately on that candle's close. No waiting for a
  post-break pullback/retest; the transcript describes entering directly on
  the breakout candle, not a classic break-then-retest pattern.
- **Position management**: 0.5% equity risk per trade (position sizing from
  entry/SL distance), 50% partial close at TP1 with move-to-breakeven,
  remainder runs to TP2.
- **Daily limits**: max 3 trades/day, stop for the day after 2 consecutive
  losses, max daily loss %, spread filter, one position at a time per
  symbol+magic number.

## Deliberate fixes vs. the originally generated code

1. **Reversal SL/touch-zone anchor.** The original code tested the zone-touch
   and wick-rejection conditions against the *confirmation* candle, and
   placed the SL relative to it too. The transcript is explicit that it's
   the *rejection* candle's wick that matters for both. Fixed to anchor all
   three (touch, reject, SL reference) to the rejection candle.
2. **Breakout mechanic.** The original code waited for a post-break pullback
   to the broken level (a pending-state machine with an expiry window)
   before entering. The transcript describes immediate entry on the strong
   breakout candle itself. Rewritten accordingly; the pending-state
   machinery was removed since it's no longer needed.

## Explicitly out of scope (present in the transcript, not implemented)

- **Anti-FOMO filter**: the transcript repeatedly warns against entering
  mid-move on a run of same-colored candles without a retest first. Not
  encoded as a rule here - add only if entries in practice look like FOMO
  chases.
- **Trend-line strategy**: a separate setup style (one-sided trend line,
  SL at the line) covered later in the class - a different strategy, not
  part of this EA.
- **Fake-breakout counter-trade**: trading a failed breakout in the opposite
  direction - a separate pattern, not implemented.

## Testing

This repo/session cannot compile or backtest MQL5. To verify:

1. Copy `HawkSR_M15_M1_EA.mq5` into your MT5 data folder's `MQL5/Experts`
   directory (MetaEditor: File > Open Data Folder) and compile with F7.
   Fix any compiler errors and report them back if they're not obvious.
2. Run it in the Strategy Tester (visual mode recommended) against recent
   XAUUSD M1 data, or attach to a **demo** chart only.
3. Confirm entries actually trigger on the corrected reversal/breakout
   conditions and that SL/TP1/TP2 land where expected.
