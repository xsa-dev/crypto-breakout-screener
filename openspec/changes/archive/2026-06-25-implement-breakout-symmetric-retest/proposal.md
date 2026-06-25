## Why

The approved `breakout-entry-state-machine` capability requires long and short breakout/retest rules to be symmetric unless a configuration explicitly says otherwise. Current local retest evaluation is deterministic, but it only treats a retest as holding when `close >= level`, which is correct for long setups and wrong for short setups that must hold below resistance.

## What Changes

- Add a narrow side-aware local retest contract for `LifecycleEngine.evaluate_retest(...)`.
- Keep existing long behavior unchanged: the retest zone must be touched, close must hold at/above the level, and micro-impulse must resume.
- Add symmetric short behavior: the retest zone must be touched, close must hold at/below the level, and micro-impulse must resume.
- Add focused tests for short retest hold/failure and a long-regression check.

## Non-Goals

- No live broker, exchange, MT5, Bybit, or terminal adapter.
- No production `full_auto` enablement.
- No add-on execution, persistence migration, operator UI, or real order placement.
- No new capability spec; this change updates the existing `breakout-entry-state-machine` capability.
