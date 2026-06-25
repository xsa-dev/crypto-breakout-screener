# Design: add-on rollback reset

## Scope
Implement the existing `breakout-risk-position-execution` requirement "Price rolls back to add-on level" as a local, deterministic risk decision. The decision is broker-neutral and only describes what should happen; it does not place or cancel orders.

## Data contract
Add `AddonRollbackDecision` to `src/core/models.py`:

- `action`: `hold` or `reduce_added_quantity`
- `reason`: `addon_level_intact` or `addon_level_rollback`
- `affected_quantity`: non-negative quantity of the added portion to reduce
- `remaining_base_quantity`: non-negative base position quantity after the decision
- `metadata`: deterministic audit fields such as `addon_level`, `current_price`, `position_quantity`, and `addon_quantity`

## Behavior
Add `RiskManager.evaluate_addon_rollback(...)`:

- Inputs: `position`, `addon_quantity`, `addon_level`, `current_price`, and optional `tolerance`.
- If `addon_quantity <= 0`, reject via `ValueError` because no add-on portion can be evaluated.
- Compute side-symmetric rollback:
  - long rollback when `current_price <= addon_level + tolerance`;
  - short rollback when `current_price >= addon_level - tolerance`.
- On rollback, return `reduce_added_quantity`, affected quantity capped to the smaller of add-on quantity and current position quantity, and remaining base quantity after removing that portion.
- When no rollback occurred, return `hold`, zero affected quantity, and current base quantity.

## Safety
The helper has no external I/O and no live execution side effects. It only returns a Pydantic DTO that downstream execution/persistence can consume in later approved changes.
