# Breakout Realistic-Cost Timeout - 2026-06-28

## Decision

Pause the current autonomous `8/8` breakout portfolio search branch.

The branch is recorded as negative robustness evidence for the current implementation path:

- M15 breakout entries remain too noisy after realistic trading costs.
- Shared-bankroll portfolio selection did not rescue the profile.
- Retest/confirmation and top-N selection improved implementation coverage, but did not produce convincing economics.
- The main observed failure modes are drawdown, cost drag from frequent entries, and weak altcoin selection quality.

This does not erase earlier friction-light `8/8` concept evidence. It narrows the claim:

- there is evidence of signal under favorable or missing execution-cost assumptions;
- the current realistic-cost/shared-bankroll implementation branch is not sufficiently robust for promotion.

## Latest Evidence Snapshot

Best robust quarterly result found in archived scorecards:

- artifact: `artifacts/extended-hold-exit-profile-comparison-summary/realistic-cost/scorecard.csv`
- best realistic-cost score: `1/8`
- best profile: `conservative-v1-m15-slope-positive-max-trades-8-hold-32`
- passed quarter: `2024q1`
- `2024q1` realistic metrics: net profit `601627.5099455944`, profit factor `2.7455148591505085`, max drawdown `-0.2013496223285395`
- remaining quarters blocked mainly by max drawdown and, for some windows, negative net profit/profit factor.

Recent retest/confirmation smoke:

- artifact: `artifacts/retest-confirmation-profile-smoke/crypto/BTCUSDT/7e3501419068c37e/summary.json`
- score: `0/1` on `2024q1`
- net profit: `-7858.726772000104`
- profit factor: `0.11915366913084179`
- max drawdown: `-0.7858726772000104`
- blockers: `net_profit_below_threshold`, `profit_factor_below_threshold`, `max_drawdown_below_threshold`

Recent top-N portfolio smoke:

- artifact: `artifacts/altcoin-universe-portfolio-comparison-top3-smoke/conservative-v1-m15-slope-positive-max-trades-8-target-4p0-hold-32/5aa1e5de7202c627/summary.json`
- universe: fixed-50 altcoins, selected symbols `ETHUSDT`, `SOLUSDT`, `BNBUSDT`
- score: `0/1` on `2024q1`
- net profit: `-6586.672688484541`
- profit factor: `0.22678513065806627`
- max drawdown: `-0.6586672688484546`
- ETH contribution was slightly positive; SOL and BNB dominated the loss.

## Current Scope Boundary

Do not continue automatic parameter chasing for this branch during the timeout.

Do not treat the remaining `implement-breakout-fast-failure-exit` idea as mandatory continuation until the owner explicitly resumes this branch or creates a new narrowed hypothesis. Fast failure may still be useful later, but the current decision is to stop the chain of incremental filters and reassess the strategy design.

## Reassessment Questions

Before resuming, answer these explicitly:

- Should this remain an auto-trading system, or become a watchlist/screener for discretionary review?
- Is M15 the correct execution timeframe after costs, or should the hypothesis move to fewer, higher-conviction signals?
- Should the system require stronger market-regime gating before any long-only breakout entries?
- Should altcoin selection be based on independent regime/liquidity/relative-strength criteria before running breakout logic?
- What exact promoted universe, cost model, exposure caps, and drawdown limits should define the next hypothesis?

## Operational State

Autonomous Dev was paused by `.hermes/autonomous.disabled` after this decision. No Telegram success notification is allowed for this branch because no promoted realistic-cost shared-bankroll `8/8` result was reached.
