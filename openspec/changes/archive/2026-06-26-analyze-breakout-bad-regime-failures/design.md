# Design

## Baseline
Use the fixed best current profile:

`conservative-v1-m15-slope-positive-max-trades-8`

Reference evidence from the previous archived slice:

- trades: 4176
- net: 54850.00
- worst drawdown: -1.1749
- passed quarters: 5/8
- failed quarters: 2024q1, 2024q2, 2024q4

## Diagnostic Focus
The diagnostics should answer:

1. Are the remaining failures concentrated in a small number of UTC days or drawdown runs?
2. Do losing entries cluster by feature buckets such as ATR percentile, breakout distance, candle body ratio, volume ratio, or higher-timeframe trend labels?
3. Are losses more severe after volatility expansion, failed continuation, or exhaustion-like candles?
4. Does the best current profile fail mostly from negative expectancy regimes, or from profitable regimes with drawdown spikes?

## Artifact Shape
Add or extend local research exports with deterministic CSV/JSON artifacts under the experiment output directory. Suggested artifacts:

- `*-failed-window-diagnostics.csv`
- `*-worst-drawdown-runs.csv`
- `*-bad-regime-bucket-summary.csv`

Each artifact should include enough identifiers to trace back to the run/window:

- window label
- profile name
- run id
- entry/exit timestamps where applicable
- feature bucket or diagnostic dimension
- trade count
- net PnL
- gross PnL if available
- max drawdown contribution or adverse run metric where available
- profit factor where meaningful
- blocker or failure reason where applicable

## Data Boundary
Stay within:

- BTCUSDT only
- public unauthenticated market data
- M15 execution data
- H1/H4/D1 context data already used by the research runner
- local artifacts only

Out of scope for this slice:

- historical order book / стакан snapshots
- L2 depth or DOM data
- spread, top-of-book, or liquidity-wall data sourced from order books
- taker-flow or trade tape datasets not already present in the current public OHLCV pipeline

If diagnostics suggest candle/context features are insufficient, microstructure context should be handled in a later dedicated OpenSpec change.

## No-Lookahead Boundary
Diagnostics may use completed trade outcomes after a run, because this is post-run analysis. However, if a diagnostic proposes an entry-time bucket or later no-trade regime candidate, the bucket definition must be computable from information available at or before the entry decision.

The implementation must distinguish:

- post-run attribution metrics, which may use realized outcomes;
- candidate regime features, which must be entry-time/no-lookahead computable.

## Implementation Notes
Prefer extending existing batch/reporting code rather than creating a separate one-off script, but keep default behavior unchanged unless the diagnostic export is explicitly requested by the research profile or batch mode.

The change should not add another filter profile as the primary deliverable. If a simple diagnostic-only classifier is useful, it must be reported as evidence and remain disabled by default.

## Verification
Required:

- unit tests for artifact schema and deterministic aggregation;
- no-lookahead test or assertion for candidate regime feature definitions;
- real quarterly run for `conservative-v1-m15-slope-positive-max-trades-8` over 2023-2024 producing diagnostics;
- strict OpenSpec validation;
- full pytest/ruff/pyright;
- `git diff --check`.
