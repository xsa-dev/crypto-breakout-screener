# Design

## Score contract

Implement a deterministic `algorithmic-breakout-score-v1` function that returns:

- `total_score`;
- component score map;
- `eligibility_bucket`: `blocked`, `reduced_priority`, or `normal_priority`;
- rejection reasons.

## Inputs

Allowed inputs:

- configured cost model and entry price;
- BTCUSDT/ETHUSDT public OHLCV context up to candidate time;
- fixed-universe public OHLCV breadth up to candidate time;
- symbol relative strength up to candidate time;
- volatility compression, volume/activity, ATR distance, and trend alignment from entry feature snapshots or public OHLCV-derived features.

Forbidden inputs:

- realized PnL;
- exit price;
- future bars;
- archived per-symbol contribution rankings;
- manual labels from after the run.

## Reporting

Artifacts SHALL include score distribution by window, regime, symbol, and eligibility bucket. Score blockers must be counted separately from cost, regime, and exposure blockers.
