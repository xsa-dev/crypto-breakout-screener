# Design

## Hypothesis
Path-risk diagnostics show failed windows have substantial favorable and adverse excursions. A fixed break-even/trailing exit may reduce failed-window drawdown and preserve enough favorable movement better than one-bar close or fixed stop/target exits. The hypothesis is supported only if a named candidate reaches `8/8` after realistic costs.

## Pre-implementation Scorecard
Reference artifact: `artifacts/path-risk-exit-diagnostics/crypto/BTCUSDT/2396740c76d50b91/summary.json`.
Command/source: archived diagnostic batch for `conservative-v1-m15-slope-positive-max-trades-8` with path-risk diagnostics enabled.

| Quarter | Status | Key metrics | Blockers | Artifact |
| --- | --- | --- | --- | --- |
| 2023q1 | pass | trades=543, net=5614.000000001684, pf=1.1364197470864763, max_dd=-0.3156576200417359 | none | `artifacts/path-risk-exit-diagnostics/crypto/BTCUSDT/af65706edd33b87d` |
| 2023q2 | pass | trades=487, net=7018.800000001695, pf=1.1949341776371043, max_dd=-0.3471478919200559 | none | `artifacts/path-risk-exit-diagnostics/crypto/BTCUSDT/71030ad63a81dd80` |
| 2023q3 | pass | trades=406, net=4324.800000001036, pf=1.1820232663849928, max_dd=-0.18664331864016465 | none | `artifacts/path-risk-exit-diagnostics/crypto/BTCUSDT/2c47b6576c069b0c` |
| 2023q4 | pass | trades=592, net=7203.200000001772, pf=1.1231526756710817, max_dd=-0.26353915143147233 | none | `artifacts/path-risk-exit-diagnostics/crypto/BTCUSDT/be2f12638128a685` |
| 2024q1 | fail | trades=575, net=-6187.600000007861, pf=0.9541519337752876, max_dd=-1.174919268030123 | net_profit_below_threshold; profit_factor_below_threshold; max_drawdown_below_threshold | `artifacts/path-risk-exit-diagnostics/crypto/BTCUSDT/9c03d4e6d4c898e0` |
| 2024q2 | fail | trades=462, net=-483.6000000135464, pf=0.9956820657510513, max_dd=-0.7580847629866918 | net_profit_below_threshold; profit_factor_below_threshold; max_drawdown_below_threshold | `artifacts/path-risk-exit-diagnostics/crypto/BTCUSDT/a6791fd0c7f20544` |
| 2024q3 | pass | trades=560, net=28129.999999996187, pf=1.2489045721283092, max_dd=-0.22247940260670482 | none | `artifacts/path-risk-exit-diagnostics/crypto/BTCUSDT/0bbf46775798a845` |
| 2024q4 | fail | trades=551, net=9230.399999974281, pf=1.0550859494542566, max_dd=-0.42254318548728437 | max_drawdown_below_threshold | `artifacts/path-risk-exit-diagnostics/crypto/BTCUSDT/b941441c45434170` |

Primary failure mechanism: failed windows lose on drawdown/adverse excursion, while 2024q1/2024q2 also lack net edge. The first target is shared path-risk control across `2024q1`, `2024q2`, and `2024q4`.

## Exit Semantics
Add optional fields to `BacktestExitProfileConfig`:

- `breakeven_after_atr`: after price reaches entry + N ATR, a later bar touching entry exits at entry.
- `trailing_after_atr`: after price reaches entry + N ATR, enable trailing protection from subsequent maximum high.
- `trailing_giveback_atr`: trailing stop distance below the post-activation maximum high.

For long trades, evaluate bars causally from the first post-entry bar through the configured fixed holding horizon. Ordering is conservative:

1. existing fixed ATR stop, if configured;
2. break-even touch after activation;
3. trailing stop after activation;
4. existing fixed ATR target, if configured;
5. fallback fixed-holding close.

Activation and stop/touch decisions use only the current and prior simulated bars. If entry-time ATR is unavailable, the profile records a missing-ATR reason and falls back to fixed-holding close.

## Candidate Set
The candidate grid is intentionally small and fixed:

- breakeven at +1.0 ATR, max hold 8 bars;
- trail after +1.0 ATR with 0.5 ATR giveback, max hold 8 bars;
- trail after +1.0 ATR with 1.0 ATR giveback, max hold 16 bars.

These are derived from existing path-risk diagnostic columns (`breakeven_reachable_ratio`, `trail_after_fav_1p0_giveback_0p5_touched_ratio`, `trail_after_fav_1p0_giveback_1p0_touched_ratio`) and avoid repeating fixed hold or fixed target-only profiles already archived.

## Artifact and Verdict Plan
1. Run targeted unit tests for exit profile defaults and ordering.
2. Run quarterly batch candidates under baseline settings using cached public market data.
3. Run the realistic-cost robustness summary against candidate trade ledgers.
4. If any candidate reaches realistic-cost `8/8`, stop and send success notification after validation/archive/commit.
5. If none reaches `8/8`, record best scorecard, blockers, artifact paths, mark the hypothesis falsified, validate, archive, and commit without success notification.

## Safety
This change remains local research only. It does not touch `.env`, credentials, live broker APIs, private account endpoints, production approval, push, MR, or merge.
