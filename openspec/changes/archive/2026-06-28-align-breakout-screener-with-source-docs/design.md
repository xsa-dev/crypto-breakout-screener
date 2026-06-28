# Design

## Source of truth

The source documentation in `doc/ai/task` is the authoritative description of the intended strategy. Implementation changes should map to these blocks:

- level engine: pivot high/low, round numbers, daily high/low, cascade levels, trendline/naklonnaya;
- setup scoring: consolidation, slow approach, trend, volume/activity, density/support or proxy;
- entry modes: pre-entry, entry-at-level, post-breakout;
- confirmation: level plus buffer, score threshold, trend filter;
- retest: return to zone, hold, continuation impulse;
- additions: 10-20%, max additions, risk budget;
- exits: 30/50/20, breakeven/protected stop, runner/trailer;
- false breakout: return under/over level, structure break, close or optional reversal;
- risk manager: blocking approval, position sizing, daily/risk limits;
- reporting: full decision log, scorecards, trades, artifacts.

## Evidence classification

Backtest and portfolio results SHALL be classified by evidence tier:

- `concept_evidence`: verifies a documented algorithm block behaves as specified;
- `friction_light_evidence`: uses favorable or missing execution costs and can demonstrate signal existence but not realistic deployability;
- `realistic_cost_evidence`: includes commission, spread, slippage, funding/swap where applicable;
- `falsified_or_blocked_evidence`: shows failure, feed gaps, unavailable data, or unsupported assumptions.

Historical `8/8` under friction-light conditions should be preserved as positive concept evidence. It should not be overwritten by later realistic-cost failure. Later failure narrows the claim: the current implementation may not yet be robust under those costs, or needs the remaining documented algorithmic blocks.

## Universe policy

Runs over one coin, ten coins, fifty coins, one hundred coins, or fixed approved universes are valid evidence if they clearly report:

- symbols/universe;
- windows;
- costs;
- thresholds;
- starting balance and exposure rules when portfolio-based;
- scorecard status;
- artifact paths.

Promoted robustness claims still require the configured promoted universe and full quarterly scorecard.

## Relationship to active changes

The currently split changes are implementation slices of the documented screener:

- `compare-breakout-cost-feasible-portfolio-selection`: execution-cost viability foundation;
- `compare-breakout-quarter-diagnostics`: evidence/logging layer;
- `implement-breakout-lifecycle-state-audit`: documented finite-state algorithm;
- `implement-breakout-algorithmic-score`: documented setup score;
- `implement-breakout-topn-portfolio-selection`: portfolio capital allocation for screener signals;
- `implement-breakout-retest-confirmation-profile`: documented confirmation/retest behavior;
- `implement-breakout-fast-failure-exit`: documented fast rejection/exit behavior for failed breakouts.

No slice should be treated as a new strategy unless it is explicitly outside the source-document algorithm.
