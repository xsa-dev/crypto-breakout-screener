# Design

## Research Verdict
The verdict is strict:

`successful profile = 8/8 after realistic costs`.

`baseline-only 8/8 = insufficient` and must enter the robustness workflow. If the same candidate fails realistic costs, archive it as falsified robustness evidence and continue with the next bounded hypothesis instead of stopping the research loop.

## Required Windows and Thresholds
All candidate evaluations SHALL use exactly these quarters:

- `2023q1`
- `2023q2`
- `2023q3`
- `2023q4`
- `2024q1`
- `2024q2`
- `2024q3`
- `2024q4`

Thresholds SHALL remain:

- `min_trade_count=1`
- `min_net_profit=0.0`
- `min_profit_factor=1.0`
- `min_max_drawdown=-0.35`
- `require_no_feed_gaps=true`

## Required Realistic Cost Check
Before a candidate can be called successful, run or summarize it under conservative realistic costs with all of:

- notional `commission_rate=0.00055` per side;
- stressed spread/slippage greater than the legacy/default assumptions used for baseline compatibility;
- `funding_rate_per_bar > 0` for conservative long-position stress.

The baseline/legacy-cost pass may be used to decide whether a candidate is worth the expensive realistic run, but it cannot satisfy success criteria and cannot trigger a success notification.

## Search Direction
The implementation should add or reuse bounded named profiles that move away from the falsified tight ATR pattern:

- avoid microscopic tight stops such as `0.01 ATR` and one-bar/high-turnover mechanics unless they are only used as a documented negative reference;
- reduce trade count and churn with cooldowns, max trades per day/window, or no-trade/regime controls;
- increase average trade and gross edge per trade through larger exits, longer holding horizons, or less cost-sensitive stop/target geometry;
- preserve causality: all gates/filters must use only information available at or before the simulated decision time;
- keep profile dimensions auditable and separate: lifecycle gates, feature filters, risk controls, regime filters, confirmation filters, and exit profile settings should remain distinct in artifacts.

## Candidate Artifacts
Every candidate, including falsified candidates, must write deterministic artifacts sufficient for review:

- `summary.json` with profile name, baseline verdict, realistic-cost verdict, thresholds, required window list, aggregate metrics, blockers, and artifact paths;
- `scorecard.csv` with one row per quarter and fields for status, blocker, trade count, net profit, profit factor, max drawdown, feed gap status, and artifact directory;
- serialized `cost_model_settings` for both baseline and realistic/stress runs;
- per-quarter pass/fail status and machine-readable blockers;
- final candidate classification: `net_costs_supported`, `baseline_only_insufficient`, `falsified_realistic_costs`, `technical_blocked`, or `not_supported`.

## Telegram Notification Gate
Notification behavior follows the robustness verdict:

- do not send Telegram success for baseline-only `8/8`;
- send Telegram success, or record send failure, only when realistic-cost scorecard is `8/8`;
- notification content must include the change id, profile name, realistic cost settings, passed quarters, thresholds, summary artifact paths, and must not include secrets or private account data.

## Safety Boundaries
This change remains local research only. It does not approve production OOS, full-auto trading, broker connection, live order placement, push, MR, merge, or private account/API access.
