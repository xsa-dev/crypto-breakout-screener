# Proposal

## Why

The previous shared-bankroll portfolio evidence shows a strong blocker in `2024q1`, while earlier BTCUSDT work reached partial success (`5/8`). Before adding more entry/exit logic, the research loop needs a deterministic diagnostic that explains what separates passing quarters from failing quarters. Without this, later changes risk tuning blindly against one blocked window.

## What Changes

Add quarter diagnostics for portfolio scorecards that compare passing, failed, blocked, and unknown windows using only public historical data and existing artifacts.

Diagnostics SHALL include:

- candidate count and accepted count;
- net profit, profit factor, max drawdown, skipped signal counts, and blocker mix;
- regime contribution by `bull_long`, `bear_short_or_avoid`, and `neutral_blocked`;
- BTCUSDT and ETHUSDT trend/regime context;
- fixed-universe market breadth;
- relative strength distribution versus BTCUSDT and ETHUSDT;
- cost-feasibility skip ratio when available;
- confirmation/retest availability ratios when available;
- fast-failure exit ratio when available.

## Success Criteria

- The portfolio runner writes a quarter diagnostics artifact for every smoke/promoted run.
- The diagnostics explicitly compare passing versus failed/blocked quarters when at least two window statuses are present.
- Diagnostics do not use future data or realized PnL as an entry-time selector.
- The report identifies the strongest observed differences and the missing data fields that prevent a stronger conclusion.

## Non-goals

- No new trading rule, no changed entry/exit behavior, no threshold weakening, no universe reduction, no private/live API, no ML, no production approval.
