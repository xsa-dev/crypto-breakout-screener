# Design

## Hypothesis

The selected mechanism is delayed close-stop activation. Existing immediate intrabar stops and immediate close stops either increased churn/cost sensitivity or failed to reduce drawdown enough. Large-target variants showed that allowing favorable continuation can improve gross edge in `2024q1`, but unrestricted adverse paths keep drawdown above the threshold. A delayed close-stop tests whether a short fixed grace period preserves early noisy continuation while closing sustained adverse moves before they dominate quarterly drawdown.

## Fixed candidate set

- `conservative-v1-m15-slope-positive-max-trades-8-delayed-close-stop-1p0-after-4-hold-16`: fixed hold 16 bars, close-stop at `-1.0 ATR` from entry, stop checks start at holding bar 5.
- `conservative-v1-m15-slope-positive-max-trades-8-target-3p0-delayed-close-stop-1p0-after-4-hold-32`: intrabar `+3.0 ATR` target, fixed hold 32 bars, delayed close-stop at `-1.0 ATR` after 4 bars.
- `conservative-v1-m15-slope-positive-max-trades-8-close-target-2p0-delayed-close-stop-1p0-after-4-hold-32`: close-confirmed `+2.0 ATR` target, fixed hold 32 bars, delayed close-stop at `-1.0 ATR` after 4 bars.

These candidates are fixed, named, and not an optimizer. If none reaches realistic-cost `8/8`, the hypothesis is falsified for this slice.

## Implementation details

- Extend `BacktestExitProfileConfig` with a disabled-by-default `close_stop_after_bars` integer field.
- Require `close_stop_after_bars` to be configured only with `close_stop_atr`; default/legacy profiles keep immediate behavior.
- In `_resolve_exit`, evaluate `close_stop_atr` only when the current holding offset is greater than `close_stop_after_bars`.
- Include the new setting in exit-profile serialization, run-id/config hashes, batch ids, summary CSV/JSON, and trade metadata.
- Add the three fixed profile names to the BTCUSDT batch runner and CLI choices.

## Constraints

- Keep reference behavior unchanged when `close_stop_after_bars=0` or no close-stop profile is selected.
- Keep entry scoring, M15 slope filter, max-trades risk control, costs, scorecard windows, and thresholds unchanged.
- Use only public cached OHLCV and already-produced deterministic backtest logic; no private/live API.

## Verification strategy

1. Validate this OpenSpec change strictly before source implementation.
2. Add/update tests for model validation, delayed close-stop behavior, profile resolution, summary serialization, and default close-stop preservation.
3. Run targeted tests, full tests, lint, typecheck, OpenSpec validation, and `git diff --check`.
4. Run realistic-cost cached BTCUSDT quarterly evidence for fixed candidates, early-falsifying only after a required realistic-cost quarter fails.
5. Archive as successful only on realistic-cost `8/8`; otherwise archive as falsified research evidence with scorecard artifacts and no success notification.
