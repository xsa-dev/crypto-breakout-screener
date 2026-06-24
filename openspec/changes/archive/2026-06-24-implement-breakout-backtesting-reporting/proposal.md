## Why

The strategy cannot be accepted without deterministic replay and evidence that the no-lookahead, risk, retest, false-breakout, and exit rules behave over historical data. This slice adds local research tooling without connecting live trading.

## What Changes

- Implement deterministic backtest runs using the same online information boundary as live evaluation.
- Model spread, commission, slippage, and funding/swap where configuration supports it.
- Implement IS/OOS, walk-forward, Monte Carlo, and stability analysis primitives or documented local equivalents.
- Produce report artifacts: equity curve, drawdown, return distribution, trade list, scenario breakdown, score distribution, false breakout analysis, slippage report, parameter snapshot, and CSV/Parquet export where dependencies allow.

## Non-Goals

- No production scheduler, cloud reports, or live-trading enablement.
- No broker-specific historical data downloader unless already available locally or explicitly configured without secrets.
