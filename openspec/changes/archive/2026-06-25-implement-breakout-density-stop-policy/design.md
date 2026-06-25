## Design

The change adds deterministic planning helpers only; it does not execute broker orders or persist runtime state.

1. Extend the local DTO surface with a `DensitySupportPlan` that records:
   - density reference price;
   - side;
   - stop price placed behind the density;
   - stop placement rule code;
   - exit-on-density-eating rule code;
   - affected quantity and remaining base quantity.
2. Add a small density-risk configuration to `RiskLimits` so tests and later callers can tune the buffer behind density without introducing global runtime settings.
3. Add `RiskManager.plan_density_support(...)` to produce a plan only from explicit caller-supplied density support data. The method must be side-symmetric: long stops below density, short stops above density.
4. Add `RiskManager.evaluate_density_invalidation(...)` to return a machine-readable decision when density is eaten/invalidated. If density is still valid, it returns a no-op decision; if eaten, it records `density_eaten` and the remaining base position state after reducing the affected quantity.
5. Keep existing entry sizing, add-on approval, fake execution, and partial-exit logic unchanged.

## Risks and Mitigations

- Risk: Treating density scoring as real order-book execution evidence. Mitigation: the helper accepts already-normalized density references and returns local plans only.
- Risk: Hidden side asymmetry. Mitigation: cover long and short stop placement in tests.
- Risk: Accidentally enabling live exit behavior. Mitigation: no execution adapter calls, no persistence writes, and no live configuration changes.
