## Why

The approved `breakout-risk-position-execution` capability requires a `fast_exit_for_low_breakouts` option because low-breakout short scenarios can accelerate on long liquidations and stops. The current lifecycle code implements the baseline 30/50/20 partial-exit framework but has no deterministic local contract for this configured asymmetry.

## What Changes

- Add a narrow local fast-exit plan for low-breakout shorts when `fast_exit_for_low_breakouts` is enabled.
- Keep the default partial-exit behavior unchanged when the option is disabled or the setup is not a short/low-breakout scenario.
- Record machine-readable reasons in the returned plan so later persistence/execution work can audit why the fast-exit path was or was not selected.
- Add focused tests covering enabled short behavior, disabled fallback, and long-side fallback.

## Non-Goals

- No live broker, exchange, MT5, Bybit, or terminal adapter.
- No production `full_auto` enablement.
- No persistence migration, operator UI, or real order placement.
- No new capability spec; this change updates the existing `breakout-risk-position-execution` capability.
