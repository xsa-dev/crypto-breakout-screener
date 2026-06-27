# Design

## Hypothesis
The selected mechanism is large favorable-target exit timing with longer bounded fallback holding. It tests whether the existing accepted entries have enough continuation to overcome realistic costs when exits require larger favorable moves and avoid additional adverse stop churn.

## Fixed candidate set
- `conservative-v1-m15-slope-positive-max-trades-8-target-3p0-hold-32`: intrabar `3.0 ATR` target, otherwise max-hold 32 M15 bars.
- `conservative-v1-m15-slope-positive-max-trades-8-target-4p0-hold-32`: intrabar `4.0 ATR` target, otherwise max-hold 32 M15 bars.
- `conservative-v1-m15-slope-positive-max-trades-8-close-target-2p0-hold-32`: close-confirmed `2.0 ATR` target, otherwise max-hold 32 M15 bars.

These candidates are fixed, named, and not an optimizer. If none reaches realistic-cost `8/8`, the hypothesis is falsified for this slice.

## Constraints
- Reuse the existing `BacktestExitProfileConfig` target-only fields; no new generic optimizer or CLI parameter surface.
- Keep entry selection, sizing, gates, feature filters, regime filters, confirmation filters, cost thresholds, and scorecard windows unchanged.
- Use only entry-time ATR and post-entry bars after the trade exists.
- Realistic-cost success requires `8/8` after `spread=1.0`, `slippage_per_unit=0.5`, `commission_rate=0.00055`, and `funding_rate_per_bar=0.00001`.
- No private/live API, account data, order placement, production approval, push, MR, merge, or Telegram success unless realistic-cost `8/8` is achieved after archive/commit.

## Verification strategy
1. Add profile-name resolution and serialization tests for the three fixed profiles.
2. Reuse existing target-only engine tests because the engine semantics already support target-only thresholds and fixed holding fallback; add only missing regression assertions if profile resolution exposes a gap.
3. Run realistic-cost cached-data batches for the required windows. Early falsify a candidate only after a required realistic-cost quarter fails; record remaining windows as blocked/not run.
4. Run targeted tests, full pytest, ruff, pyright, strict OpenSpec validation, duplicate spec/archive-name check, and `git diff --check` before archive/commit.
