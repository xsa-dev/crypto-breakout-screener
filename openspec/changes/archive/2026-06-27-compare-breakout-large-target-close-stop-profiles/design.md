# Design

## Hypothesis
The selected mechanism is a close-confirmed catastrophic stop layered on the large-target exit profiles that previously made `2024q1` net/PF positive but still failed drawdown. Intrabar stops were already falsified as cost-sensitive/churn-prone; this slice uses a close-only stop at `-1.0 ATR` from entry to avoid same-bar noise while clipping sustained adverse paths before they accumulate the large `2024q1` drawdown.

## Fixed candidate set
- `conservative-v1-m15-slope-positive-max-trades-8-target-3p0-close-stop-1p0-hold-32`: intrabar `3.0 ATR` favorable target, close-confirmed `1.0 ATR` adverse stop, max-hold 32 M15 bars.
- `conservative-v1-m15-slope-positive-max-trades-8-target-4p0-close-stop-1p0-hold-32`: intrabar `4.0 ATR` favorable target, close-confirmed `1.0 ATR` adverse stop, max-hold 32 M15 bars.
- `conservative-v1-m15-slope-positive-max-trades-8-close-target-2p0-close-stop-1p0-hold-32`: close-confirmed `2.0 ATR` favorable target, close-confirmed `1.0 ATR` adverse stop, max-hold 32 M15 bars.

These candidates are fixed, named, and not an optimizer. If none reaches realistic-cost `8/8`, the hypothesis is falsified for this slice.

## Implementation details
- Add profile names to the BTCUSDT batch runner's disabled-by-default `EXIT_PROFILE_NAMES` set.
- Resolve the three names through existing `BacktestExitProfileConfig` fields:
  - `fixed_holding_bars=32`
  - `close_stop_atr=1.0`
  - either `target_atr=3.0`, `target_atr=4.0`, or `close_target_atr=2.0`
- The existing `_resolve_exit` order already checks `close_stop_atr` before favorable target checks, satisfying the conservative close-stop-first semantics without new decision-path abstractions.
- Existing exit-profile metadata and batch summary JSON/CSV should serialize the stop, target, holding bars, and exit reason.

## Constraints
- Keep entry scoring, sizing, M15 slope feature filter, max-trades setting, confirmation/regime filters, scorecard windows, cost settings, and thresholds unchanged.
- Use only public cached OHLCV and already-produced trade metadata; no private/live API or account data.
- Do not add broad parameter search, ML, order-book/microstructure data, or production approval.

## Verification strategy
1. Validate this OpenSpec change strictly before source implementation.
2. Add/update tests for named profile resolution and serialization; reuse existing `_resolve_exit` tests for close-stop-first semantics where possible.
3. Run targeted tests and full project gates.
4. Run cached public-data realistic-cost batches for candidates. Early-falsify a candidate only after a required realistic-cost quarter fails; record remaining windows as blocked/not run.
5. Archive as successful only on realistic-cost `8/8`; otherwise archive as falsified research evidence with scorecard artifacts and no success notification.
