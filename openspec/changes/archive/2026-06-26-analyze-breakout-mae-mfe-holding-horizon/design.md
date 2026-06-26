# Design

## Baseline
Use the fixed current best profile as the diagnostic target:

`conservative-v1-m15-slope-positive-max-trades-8`

Known status before this change:

- passed: 5/8
- failed: 3/8
- hypothesis_supported: false

The change is diagnostic-only. It must not add filters, retune thresholds, change exits, or alter batch verdict semantics.

## Diagnostic horizons
Use fixed M15 forward horizons:

- 1 bar
- 2 bars
- 4 bars
- 8 bars
- 16 bars

For a trade entering at bar index `i`, each horizon `h` may use bars up to `i + h` only for offline diagnostics after the trade has already been created. These values are not allowed to influence entry decisions in this change.

## Per-trade diagnostics
For each exported trade, produce forward-path diagnostics including:

- trade id;
- symbol;
- side;
- entry time;
- entry index;
- entry price;
- current realized exit time/price/PnL;
- selected breakout level when available;
- horizon bars;
- forward close return at the horizon;
- MFE over the horizon;
- MAE over the horizon;
- MFE/MAE ratio when defined;
- time to MFE in bars;
- time to MAE in bars;
- whether close is above entry at the horizon;
- whether price returned to the breakout level within the horizon;
- whether price crossed below entry within the horizon.

Long-only semantics apply for the current research path. If short-side is added later, it must be separately specified.

## Holding-horizon synthetic summaries
For each fixed horizon, export an aggregate summary that computes a deterministic synthetic close-at-horizon PnL using the existing quantity and cost assumptions where available.

This is diagnostic only:

- it does not change the actual trade list;
- it does not change current reported net profit;
- it does not claim a new strategy result unless a later OpenSpec implements an exit/holding profile.

## Passed-vs-failed comparison
The batch diagnostics SHALL compare passed and failed windows for the current best profile using the existing batch verdict labels. The comparison should summarize:

- average/median forward returns by horizon;
- average/median MFE and MAE by horizon;
- share of trades with positive close return at each horizon;
- share of trades returning to breakout level;
- share of trades crossing below entry;
- worst-day forward-path behavior where available.

## Artifacts
Required artifacts:

- per-run `*-forward-path-diagnostics.csv`;
- per-run `*-holding-horizon-pnl.csv`;
- batch-level `forward-path-window-summary.csv`;
- batch-level `passed-vs-failed-forward-path-summary.csv`.

Optional if small and useful:

- `worst-day-forward-path.csv`.

## No-lookahead boundary
Forward-path values necessarily use future bars relative to entry, but only as offline diagnostic labels. They SHALL NOT be available to entry filters, risk gates, confirmation filters, or sizing logic in this change.

The implementation should keep these diagnostics in report/export code paths after trades are already produced.

## Verification
Run:

```bash
uv run pytest
uv run ruff check .
uv run pyright
npx --yes @fission-ai/openspec@1.4.1 validate analyze-breakout-mae-mfe-holding-horizon --strict --no-interactive
npx --yes @fission-ai/openspec@1.4.1 validate --all --strict --no-interactive
git diff --check
```

Then run the quarterly 2023-2024 batch for:

`conservative-v1-m15-slope-positive-max-trades-8`

with forward-path diagnostics enabled, using existing public BTCUSDT market data when available.
