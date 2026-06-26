# Proposal

## Why
The completed BTCUSDT feature-diagnostics change produced evidence that conservative lifecycle gates reduce overtrading and improve drawdown, but the trading hypothesis still fails most quarterly windows on max drawdown. The diagnostics identified candidate entry/context conditions that appear to separate profitable and loss-making regimes, especially M15 EMA slope and H1 trend alignment.

The next research slice should test those candidate filters as explicit deterministic backtest profiles. This should remain research-only: it must not optimize thresholds automatically, train ML models, or claim production approval.

## What Changes
- Add disabled-by-default research feature filters for entry candidates using already available entry-time diagnostics.
- Add named comparison profiles on top of `conservative-v1`, including:
  - `conservative-v1-m15-slope-positive`;
  - `conservative-v1-h1-long`;
  - `conservative-v1-m15-slope-positive-h1-long`;
  - `conservative-v1-m15-slope-positive-body-cap`.
- Keep existing `baseline` and `conservative-v1` behavior unchanged.
- Run BTCUSDT quarterly public-data comparisons and report whether any filter profile improves the hypothesis verdict.
- Treat successful filter profiles as research evidence only, not live/full-auto/production approval.

## Out of Scope
- ML training, boosting, neural networks, model inference, or new ML dependencies.
- Automatic threshold search, parameter optimization, walk-forward optimizer, Monte Carlo optimizer, or auto-selected rules.
- Live trading, private exchange APIs, account/order/position state, broker adapters, or `.env`/credential access.
- ETH/top-N expansion, FX support, UI/dashboard, scheduler, DB storage, deployment, or production OOS approval.
- Changing default baseline or conservative-v1 behavior unless a named feature-filter profile is explicitly requested.

## Expected Outcome
The change should produce a reproducible quarterly comparison table showing whether feature-filter profiles improve trade count, net profit, max drawdown, profit factor, win rate, and hypothesis verdict versus `conservative-v1`.

A likely first candidate is `conservative-v1-m15-slope-positive`, based on diagnostic evidence:

- M15 EMA slope negative: 3,237 trades, net PnL -24,607.60.
- M15 EMA slope positive: 3,956 trades, net PnL 77,993.20.

The implementation must verify this through actual backtest profiles because post-filtered CSV diagnostics do not recalculate lifecycle state, cooldowns, max-trades/day, or daily stop-loss behavior.
