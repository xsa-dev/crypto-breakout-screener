## Design

This is a narrow correctness fix inside the existing blocking risk manager.

1. Add a regression test that uses a non-unit `RiskLimits.contract_multiplier` and an entry intent whose requested quantity is above the risk-derived maximum.
2. Assert that:
   - approved quantity remains `equity * risk_pct / (stop_distance * contract_multiplier)`;
   - `planned_risk` equals `approved_quantity * stop_distance * contract_multiplier`;
   - rejection behavior and add-on behavior are unchanged.
3. Update `RiskManager.evaluate(...)` for non-add-on intents to reuse the multiplier-aware planned-risk calculation.
4. Keep public DTO shapes, enum values, adapter behavior, persistence schema, and full-auto guards unchanged.

## Risks and Mitigations

- Risk: Existing tests may implicitly expect `planned_risk` without multiplier. Mitigation: the approved spec formula includes multiplier, so tests should be updated only where they conflict with the normative requirement.
- Risk: Add-on risk semantics change accidentally. Mitigation: do not touch add-on branch logic; add-on `planned_risk` already includes `contract_multiplier` through the existing local variable.
