## Why

The approved `breakout-risk-position-execution` capability requires density/support to be usable as both a trade-support premise and a stop/exit policy. Current local code scores density as a setup factor, but it does not expose a deterministic risk/exit contract that records the density reference, stop placement rule, exit-on-density-eating rule, or the reset/reduction reason when that density is invalidated.

## What Changes

- Add a narrow local density-support plan under the existing `breakout-risk-position-execution` capability.
- Record machine-readable density reference, stop placement rule, and exit-on-density-eating policy in a Pydantic DTO.
- Add deterministic invalidation logic that decides whether an eaten density should reduce/exit the affected position and records the reason plus remaining base position state.
- Add focused tests for long/short density stop placement and density invalidation/reset behavior.

## Non-Goals

- No live broker, exchange, MT5, Bybit, or terminal adapter.
- No production `full_auto` enablement.
- No persistence migration, operator UI, or real order placement.
- No new capability spec; this change updates the existing `breakout-risk-position-execution` capability.
