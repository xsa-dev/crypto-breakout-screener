## Design

The change implements the existing flag as a deterministic local entry-intent gate without side effects.

1. Reuse `BreakoutStrategyConfig.entries.lower_protorgovka_entry_enabled` as the explicit opt-in flag.
2. Extend `EntryEngine.generate_intents(...)` with a keyword-only readiness signal for the rare lower-protorgovka boundary condition. Default it to `False` so existing callers and tests remain unchanged.
3. When all required conditions hold, create an early long `TradeIntent` capped by the configured `pre_entry_share`:
   - the explicit flag is enabled;
   - `lower_protorgovka_ready=True`;
   - `side is Side.LONG`;
   - score/base-quantity gates already pass.
4. Add metadata to the intent with a stable reason code such as `lower_protorgovka_ready` and an entry subtype such as `lower_protorgovka_boundary`.
5. Keep cumulative exposure capping through the existing `_cap_total_quantity(...)` path.
6. Do not add broker behavior, persistence schema changes, UI controls, or dependency changes.

## Risks and Mitigations

- Risk: Hidden early-entry behavior before breakout confirmation. Mitigation: keep it disabled by default and require both a config flag and explicit caller readiness.
- Risk: Duplicating normal pre-entry unintentionally. Mitigation: use the same pre-entry share cap and existing cumulative exposure cap; focused tests cover no intent when disabled and no short-side asymmetric behavior.
