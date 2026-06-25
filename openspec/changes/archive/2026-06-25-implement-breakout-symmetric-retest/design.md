## Design

The change makes the existing retest helper side-aware while preserving its local, side-effect-free nature.

1. Extend `LifecycleEngine.evaluate_retest(...)` with a keyword-only `side: Side = Side.LONG` argument so current callers keep long behavior by default.
2. Keep zone-touch and micro-impulse requirements common to both sides.
3. Evaluate structure hold side-symmetrically:
   - long retest holds when `market.close >= level_price`;
   - short retest holds when `market.close <= level_price`.
4. Add focused tests that first fail against the current long-only hold logic:
   - a short retest touching the zone and closing below the level returns `True`;
   - a short retest touching the zone but closing above the level returns `False`;
   - existing long behavior still holds/rejects as before.
5. Do not add state transitions, order placement, add-on execution, persistence, UI, or dependency changes.

## Risks and Mitigations

- Risk: Existing callers omit side and expect long semantics. Mitigation: default the new argument to `Side.LONG` and add a long regression test.
- Risk: Short retest may be confused with reversal logic. Mitigation: this helper only returns a local boolean for retest validity; false-breakout/reversal remains unchanged and separately gated by existing config/specs.
