# Design

## Baseline
Use the fixed current best profile as the diagnostic target:

`conservative-v1-m15-slope-positive-max-trades-8`

Known status before this change:

- passed: 5/8
- failed: 3/8
- hypothesis_supported: false

The forward-path diagnostic baseline from the prior archived change showed weak continuation and frequent adverse excursion. This change stays diagnostic-only and must not add or activate exits.

## Diagnostic horizons
Use the same fixed M15 forward horizons unless implementation discovers a concrete reason to reduce scope:

- 1 bar
- 2 bars
- 4 bars
- 8 bars
- 16 bars

Diagnostics may use future bars relative to entry only after trades have already been produced and only as offline labels.

## Fixed threshold grid
Use a small fixed diagnostic grid, not an optimizer:

Favorable thresholds, measured from entry:

- +0.5 ATR
- +1.0 ATR
- +1.5 ATR
- +2.0 ATR

Adverse thresholds, measured from entry:

- -0.5 ATR
- -1.0 ATR
- -1.5 ATR
- -2.0 ATR

If entry-time ATR is unavailable for a trade, the row must be marked unavailable with a reason rather than inferred from future bars.

Break-even and trailing diagnostics use fixed labels only; they do not simulate a new strategy:

- break-even is considered reachable when price first reaches at least `+1.0 ATR` from entry within the horizon;
- break-even touch-after-reach is true when, after `+1.0 ATR` is first reached, a later bar low returns to or below the entry price within the same horizon;
- trailing diagnostics are evaluated only after a favorable threshold is reached;
- trailing giveback thresholds are fixed at `0.5 ATR` and `1.0 ATR` below the maximum high observed after the favorable threshold was reached;
- trailing-touch labels report whether those giveback levels were touched later within the same horizon.

## Per-trade path-risk diagnostics
For each already-produced trade and each horizon, export labels including:

- trade id;
- symbol;
- side;
- entry time;
- entry index;
- entry price;
- realized exit time/price/PnL;
- entry-time ATR value used for threshold labels;
- horizon bars;
- MFE and MAE over the horizon;
- maximum favorable ATR multiple;
- maximum adverse ATR multiple;
- first favorable threshold hit and bar offset;
- first adverse threshold hit and bar offset;
- whether favorable threshold was hit before adverse threshold for each fixed pair;
- whether adverse threshold was hit before favorable threshold for each fixed pair;
- whether break-even would become reachable after each favorable threshold;
- whether break-even was touched after becoming reachable;
- whether fixed trailing giveback levels after favorable excursion would have been touched within the horizon.

Long-only semantics apply for the current research path. Short-side behavior must be specified separately if added later.

## Aggregate path-risk summaries
Batch artifacts should summarize by horizon, passed/failed window group, and window label:

- hit rate for each favorable threshold;
- hit rate for each adverse threshold;
- favorable-before-adverse ratio for each fixed pair;
- adverse-before-favorable ratio for each fixed pair;
- median/average maximum favorable ATR multiple;
- median/average maximum adverse ATR multiple;
- break-even reachability rate;
- trailing-touch rate after favorable excursion;
- unavailable counts and reasons.

## Artifacts
Required artifacts:

- per-run `*-path-risk-diagnostics.csv`;
- per-run `*-path-risk-threshold-summary.csv`;
- batch-level `path-risk-window-summary.csv`;
- batch-level `passed-vs-failed-path-risk-summary.csv`.

Optional if small and useful:

- `path-risk-worst-day-summary.csv`.

## No-lookahead boundary
Path-risk labels necessarily use future bars relative to entry, but only as offline diagnostics after the trade exists. They SHALL NOT be available to entry filters, risk gates, confirmation filters, sizing logic, actual exit logic, actual PnL calculations, or batch verdicts in this change.

## Verification
Run:

```bash
uv run pytest
uv run ruff check .
uv run pyright
npx --yes @fission-ai/openspec@1.4.1 validate analyze-breakout-path-risk-exit-diagnostics --strict --no-interactive
npx --yes @fission-ai/openspec@1.4.1 validate --all --strict --no-interactive
git diff --check
```

Then run the quarterly 2023-2024 batch for:

`conservative-v1-m15-slope-positive-max-trades-8`

with path-risk diagnostics enabled, using existing public BTCUSDT market data when available.
