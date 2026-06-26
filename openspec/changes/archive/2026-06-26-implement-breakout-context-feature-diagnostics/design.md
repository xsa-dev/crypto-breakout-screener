# Design

## Goal
Add a deterministic research diagnostics layer that answers: "which entry-time technical/context conditions explain the remaining drawdown after lifecycle gates?"

The implementation should expose feature evidence first. It should not introduce model training or new trading filters in this change.

## Current evidence
The latest committed lifecycle/gate run shows:

- baseline remained hypothesis-negative with extreme churn;
- conservative-v1 reduced trades by about 89.7%;
- conservative-v1 improved worst drawdown by about 2.2x;
- conservative-v1 still failed 6/8 windows, mostly on max drawdown;
- therefore remaining failure likely depends on market context and setup quality, not only trade frequency.

## Feature extraction boundary
Feature snapshots must be calculated from information available at or before the simulated entry bar.

Allowed inputs:

- current M15 closed-bar history up to entry index;
- the already-computed `SetupEvaluator.calculate_features(...)` output;
- simulated lifecycle state already known before the candidate trade;
- optional H1/H4/D1 context CSVs, aligned by closed context bar timestamp less than or equal to the M15 entry timestamp;
- public OHLCV data only.

Forbidden inputs:

- future M15 bars after the entry bar;
- trade outcome, exit price, future PnL, future drawdown, or next-bar label during feature calculation;
- private exchange/account data;
- live broker state;
- model predictions from unapproved ML scopes.

## Feature groups

### Existing setup/scoring features
Record the feature vector and score components already produced by the setup scorer where available:

- total setup score;
- eligibility bucket/rejection reasons;
- consolidation/range metrics;
- slow-approach / approach velocity;
- trend score inputs such as EMA fast/slow and ADX where available;
- activity and density/proxy indicators.

### M15 technical features
Compute low-cost deterministic indicators from closed M15 history:

- ATR value and ATR percentile/rank over a configurable trailing window;
- candle body/range ratio;
- close position inside candle range;
- breakout distance from level in ATR units;
- distance from EMA fast/slow in ATR units;
- EMA slope proxy over a trailing window;
- recent range compression proxy;
- recent high/low breakout distance;
- volume ratio against trailing average when volume is present.

### H1/H4/D1 context features
When context CSV paths are supplied and valid, align closed context bars at or before the M15 entry time and record:

- context close timestamp used per timeframe;
- close above/below EMA fast/slow;
- EMA slope proxy;
- ATR/range regime proxy;
- context availability reason if missing.

If context CSVs are not supplied, feature exports should still exist and mark context fields as unavailable rather than failing the baseline backtest.

### Lifecycle state features
Record pre-entry lifecycle state already known before the candidate trade:

- trades today before entry;
- realized PnL today before entry;
- bars since previous trade exit when available;
- previous trade was loss flag when available;
- current research gate profile/settings hash or gate parameters.

## Artifacts
Backtest report export should include deterministic feature diagnostics:

- `<run_id>-entry-feature-snapshots.csv`
  - one row per exported trade
  - includes trade id, symbol, side, entry time, entry index, score, selected setup/context/lifecycle features, outcome columns (`net_pnl`, `max_drawdown_contribution` if available or explicitly unavailable) for offline grouping
- `<run_id>-feature-bucket-pnl.csv`
  - one row per feature bucket and bucket value
  - includes trade count, net PnL, average trade, win rate, profit factor when computable, max drawdown proxy if available
- `<run_id>-regime-bucket-summary.csv`
  - coarser summary for high-signal regimes such as ATR percentile bucket, trend alignment, candle quality, and context alignment
- `<run_id>-worst-day-attribution.csv`
  - identifies days with largest realized net loss, trade count, dominant bucket values, and available context flags

Existing artifacts must remain stable unless deliberately extended and tested.

## Batch comparison
Run the BTCUSDT quarterly public-data batch after implementation with at least:

- baseline profile;
- conservative-v1 gates;
- conservative-v1 with feature diagnostics enabled using M15 plus available H1/H4/D1 context datasets.

The comparison must report whether diagnostics reveal clear candidate filters, but must not claim those filters are production-approved. If the feature diagnostics indicate a promising rule or ML direction, capture it as a recommendation for a separate OpenSpec change.

## Data and safety constraints

- Public unauthenticated data only.
- BTCUSDT only for this change.
- M15 remains the execution/backtest input.
- H1/H4/D1 remain context datasets and must be recorded in manifests/summaries when downloaded.
- No `.env`, private keys, authorization headers, order endpoints, account balances, positions, or broker state.
- No new runtime dependencies unless the implementation proves they are already in the project; prefer pure Python feature computation.

## Verification strategy

- Unit tests for no-lookahead feature alignment.
- Unit tests for deterministic feature snapshots and bucket outputs.
- Unit tests for missing context CSV behavior.
- Batch tests that verify feature artifact paths and metadata are recorded.
- Full `uv run pytest`, `uv run ruff check .`, `uv run pyright`.
- OpenSpec strict validation and `git diff --check`.
- Real public-data BTCUSDT quarterly smoke if network/provider access is available; otherwise report the exact blocker and run fixture-based smoke.
