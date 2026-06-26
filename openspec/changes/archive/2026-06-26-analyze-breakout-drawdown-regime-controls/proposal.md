# Proposal

## Why
The conservative lifecycle gates and the first deterministic feature-filter comparison materially improved the BTCUSDT breakout research pipeline, but the trading hypothesis still does not pass quarterly research thresholds.

Current best profile evidence:

- `conservative-v1` improved baseline overtrading but passed only 2/8 quarters.
- `conservative-v1-m15-slope-positive` is the best tested feature filter so far:
  - 5,110 trades;
  - 58,718.40 net profit;
  - worst max drawdown -1.5366;
  - 4/8 quarters passed;
  - 4/8 quarters still failed.

The remaining failures are drawdown/regime concentrated rather than generic overtrading failures. Failed windows for the best profile are 2023q2, 2024q1, 2024q2, and 2024q4, with 2024q1/2024q2 showing the largest risk problem. Simple H1 trend and candle-body filters did not improve the hypothesis. The next step is to analyze worst-day/regime concentration and test a small, evidence-driven set of research risk controls.

## What Changes
- Add a local research comparison for drawdown/regime controls on top of the current best profile, `conservative-v1-m15-slope-positive`.
- Produce auditable worst-window and worst-day summaries for failed quarters.
- Support a small fixed set of research-only risk-control profiles, such as stricter daily stop loss, lower max trades per day, longer cooldown after loss, and loss-streak/day-pause controls.
- Extend batch summaries so risk-control settings and risk-control skip/pause counts are visible per window.
- Run BTCUSDT quarterly 2023-2024 comparisons and report whether any profile improves passed-window count without hiding technical blockers.

## Out of Scope
- ML, boosting, neural networks, or model inference.
- Automatic parameter search, grid search, Bayesian optimization, or walk-forward optimizer.
- Production trading approval, live execution, broker adapters, private API/account/order/position state, deployment, or UI/dashboard.
- ETH/top-N/FX expansion.
- Changing default `baseline`, `conservative-v1`, or already committed feature-filter profile behavior unless an explicit new risk-control profile is selected.

## Expected Outcome
A deterministic research artifact that explains whether drawdown failures are reducible by simple risk/regime controls. A successful profile may become the next research candidate, but remains research-only and not production approval.
