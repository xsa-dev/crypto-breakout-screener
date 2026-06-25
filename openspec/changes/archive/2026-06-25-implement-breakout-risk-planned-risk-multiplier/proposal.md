## Why

The approved `breakout-risk-position-execution` capability defines position size and planned risk using `contract_multiplier`, but the current approval result can under-report `planned_risk` for new entries when an instrument multiplier is not `1.0`. That weakens downstream audit/reconciliation semantics even though quantity sizing already uses the multiplier.

## What Changes

- Keep the existing position-sizing formula and entry approval behavior.
- Ensure approved entry `planned_risk` is calculated as `approved_quantity * stop_distance * contract_multiplier`.
- Add a focused regression test for a non-unit `contract_multiplier` so quantity and planned risk remain aligned.

## Non-Goals

- No live broker, exchange, MT5, Bybit, or terminal adapter.
- No production `full_auto` enablement.
- No new capability spec; this change updates the existing `breakout-risk-position-execution` capability.
- No broad risk model redesign, persistence migration, UI, or order-placement changes.
