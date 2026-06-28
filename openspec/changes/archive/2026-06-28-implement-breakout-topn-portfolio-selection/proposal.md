# Proposal

## Why

The shared-bankroll portfolio should not accept every `bull_long` signal until exposure caps reject the rest. With a fixed `10000 USDT` balance and finite exposure, concurrent candidates must compete for capital. The strategy needs top-N selection that chooses the best entry-time candidates and records lower-ranked candidates as skipped evidence.

## What Changes

Add opt-in top-N portfolio selection for score-aware breakout candidates.

The selector SHALL sort concurrent candidates by:

1. algorithmic score descending;
2. relative strength rank descending;
3. lower relative friction;
4. deterministic symbol tie-breaker.

It SHALL accept only candidates that fit per-trade and total exposure caps, and record lower-ranked candidates as `portfolio_selection_rank_not_selected`.

## Success Criteria

- Concurrent candidates compete for shared bankroll before exposure allocation is finalized.
- Lower-ranked skipped candidates remain in the portfolio ledger with machine-readable blockers.
- The selection summary reports selected/rejected counts and score/rank distributions.
- Default non-top-N behavior remains unchanged.

## Non-goals

- No new score formula, no retest/confirmation behavior, no fast-failure exit, no threshold weakening, no universe reduction, no leverage.
