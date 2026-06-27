# Design

## Hypothesis
The selected mechanism is fixed lower per-trade exposure combined with already-supported large-target holding exits. Prior large-target profiles improved gross edge and realistic-cost net/PF in `2024q1`, but failed max drawdown. Prior tight stops/trailing/protected residual exits reduced exposure by adding more exit churn and became cost/negative-expectancy failures. This slice keeps the profitable favorable-exit behavior and scales only deterministic `base_quantity` from `10.0` to `0.5` for named research candidates.

## Fixed candidate set
- `conservative-v1-m15-slope-positive-max-trades-8-target-3p0-hold-32-qty-0p5`: intrabar `3.0 ATR` favorable target, max-hold 32 M15 bars, `base_quantity=0.5`.
- `conservative-v1-m15-slope-positive-max-trades-8-target-4p0-hold-32-qty-0p5`: intrabar `4.0 ATR` favorable target, max-hold 32 M15 bars, `base_quantity=0.5`.
- `conservative-v1-m15-slope-positive-max-trades-8-close-target-2p0-hold-32-qty-0p5`: close-confirmed `2.0 ATR` favorable target, max-hold 32 M15 bars, `base_quantity=0.5`.

These candidates are fixed, named, and not an optimizer. If none reaches realistic-cost `8/8`, the hypothesis is falsified for this slice.

## Implementation details
- Add profile names to the BTCUSDT batch runner's disabled-by-default profile set.
- Reuse existing `BacktestExitProfileConfig` fields for the target/holding portion.
- Add a small helper that resolves candidate exposure settings from the profile name:
  - default profiles keep `base_quantity=10.0` and current behavior;
  - `*-qty-0p5` profiles pass `base_quantity=0.5` into `run_crypto_experiment`.
- Include exposure settings in batch id inputs and summary artifacts so reruns are deterministic and auditable.
- Existing trade PnL/costs remain quantity-based; no thresholds are changed.

## Constraints
- Keep entry scoring, M15 slope filter, max-trades setting, confirmation/regime filters, scorecard windows, cost settings, and thresholds unchanged.
- Use only public cached OHLCV and already-produced trade metadata; no private/live API or account data.
- Do not add broad parameter search, ML, order-book/microstructure data, or production approval.

## Verification strategy
1. Validate this OpenSpec change strictly before source implementation.
2. Add/update tests for named profile resolution, exposure forwarding, summary serialization, and default behavior preservation.
3. Run targeted tests and full project gates.
4. Run cached public-data realistic-cost batches for candidates. Early-falsify a candidate only after a required realistic-cost quarter fails; record remaining windows as blocked/not run.
5. Archive as successful only on realistic-cost `8/8`; otherwise archive as falsified research evidence with scorecard artifacts and no success notification.
