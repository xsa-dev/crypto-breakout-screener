# Proposal

## Why

Partial success implies the breakout idea may depend on context quality. The current portfolio runner does not compute a unified score that combines market regime, breadth, relative strength, compression, volume, ATR distance, trend, and cost feasibility. Without a score, the portfolio cannot prefer strong setups over weak concurrent signals.

## What Changes

Add opt-in `algorithmic-breakout-score-v1`, a deterministic 0..100 entry-time score for breakout candidates.

Score components:

- cost feasibility: 15 points;
- BTC/ETH market regime agreement: 15 points;
- fixed-universe market breadth: 15 points;
- symbol relative strength versus BTC/ETH: 15 points;
- volatility compression before breakout: 15 points;
- volume/activity expansion: 10 points;
- ATR-normalized breakout distance quality: 10 points;
- multi-timeframe trend alignment: 5 points.

## Success Criteria

- Candidate artifacts include total score, component scores, eligibility bucket, and rejection reasons.
- Score `< 70` is blocked for score-aware profiles with `portfolio_selection_algorithmic_score_below_threshold`.
- Score `70..84` is eligible with reduced priority; score `>=85` is eligible with normal priority.
- Score calculation uses only public data available at candidate time.

## Non-goals

- No top-N allocation, no retest/confirmation behavior, no fast-failure exit, no ML, no realized-PnL training, no threshold weakening.
