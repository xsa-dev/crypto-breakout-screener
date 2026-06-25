## Why

The approved `breakout-entry-state-machine` capability requires the rare lower-protorgovka early long-entry subtype to be available only behind an explicit configuration flag. The current configuration exposes `lower_protorgovka_entry_enabled`, but entry generation has no deterministic contract proving the flag gates this early intent.

## What Changes

- Add a narrow local entry-generation path for lower-protorgovka early long entries when `lower_protorgovka_entry_enabled` is enabled and the caller marks the condition ready.
- Keep default behavior unchanged: no lower-protorgovka intent is created when the flag is disabled, when the setup is not long, when readiness is false, or when score/base quantity blocks entries.
- Record a stable machine-readable reason/metadata on the generated intent so later persistence and execution slices can audit the configured asymmetry.
- Add focused tests for enabled behavior and disabled/non-long fallbacks.

## Non-Goals

- No live broker, exchange, MT5, Bybit, or terminal adapter.
- No production `full_auto` enablement.
- No persistence migration, operator UI, or real order placement.
- No new capability spec; this change updates the existing `breakout-entry-state-machine` capability.
