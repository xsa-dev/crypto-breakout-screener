## Design

The change adds one configuration flag and one deterministic planning method rather than wiring execution side effects.

1. Extend the existing risk/entry configuration surface with `fast_exit_for_low_breakouts: bool = False`.
2. Add a small Pydantic DTO for an exit plan, or reuse a typed dictionary only if neighbouring code already has one. The plan must expose:
   - whether fast exit is active;
   - first/second/runner quantities;
   - a stable reason code.
3. Add a `LifecycleEngine.plan_exit_framework(...)` method that keeps `partial_exit_quantities(...)` intact for backward compatibility and returns the fast-exit plan only when all conditions hold:
   - config flag is enabled;
   - side is `SHORT`;
   - the caller identifies the setup as a low-breakout scenario;
   - total quantity is positive.
4. For fast exit, allocate no long-running runner and distribute the full quantity through accelerated first/second fixations. Use 50% first fixation and 50% second fixation as the local deterministic v1 contract; later execution changes can translate those quantities into real orders.
5. Do not add live adapter behavior, persistence schema changes, or UI controls.

## Risks and Mitigations

- Risk: Hidden asymmetry for shorts. Mitigation: require explicit `low_breakout=True` and record `fast_exit_low_breakout` reason.
- Risk: Breaking existing tests that call `partial_exit_quantities`. Mitigation: keep the existing method unchanged and add a new planner method.
