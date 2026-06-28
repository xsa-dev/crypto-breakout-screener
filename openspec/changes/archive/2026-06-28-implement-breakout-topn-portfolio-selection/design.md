# Design

## Concurrency bucket

Group candidates that compete for capital by entry timestamp or a deterministic allocation bucket. Within each bucket, sort candidates by configured ranking keys.

## Ranking keys

Required keys:

1. algorithmic score descending;
2. relative strength rank descending;
3. relative friction ascending;
4. symbol ascending.

If an optional upstream key is unavailable, the candidate must either receive the documented fallback value or be skipped with an explicit missing-feature blocker.

## Allocation

After ranking, accept candidates until `max_trade_notional` and `max_total_open_notional` constraints are reached. Candidates not selected because better-ranked candidates consumed the bucket allocation are skipped with `portfolio_selection_rank_not_selected`, not silently dropped.

## Reporting

Portfolio artifacts SHALL include selected count, rank-not-selected count, rank distribution, and the ranking values used for every selected or skipped candidate.
