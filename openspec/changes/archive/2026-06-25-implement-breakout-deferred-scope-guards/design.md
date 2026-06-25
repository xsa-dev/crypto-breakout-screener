# Design

## Context

`BreakoutStrategyConfig.mode` currently defaults to `semi_auto`, and `OperationMode.FULL_AUTO` exists as a stable enum value. The capability spec requires production full-auto enablement to remain blocked until a later dedicated approval change defines production readiness and live execution scope.

## Approach

1. Add a small, explicit contract-validation flag to `BreakoutStrategyConfig` such as `full_auto_contract_validation_only: bool = False`.
2. Add a Pydantic model-level validator that rejects `mode=OperationMode.FULL_AUTO` unless that local contract-validation flag is true.
3. Use a deterministic error message that names the deferred-scope guard and says a dedicated full-auto OpenSpec change is required.
4. Keep the enum untouched so fake-adapter and future contract tests can still refer to `OperationMode.FULL_AUTO` without enabling it by default.
5. Add unit tests in the existing breakout foundation test surface; no runtime networking, DB migration, or adapter wiring is needed.

## Data / API Impact

- No database schema changes.
- No external API changes.
- `BreakoutStrategyConfig` JSON gains an internal boolean contract-validation guard field with safe default `false`.
- Existing default config remains backward compatible because `semi_auto` is unchanged.

## Safety

The guard is fail-closed: config attempts to use production-like `full_auto` fail locally during model validation before startup or activation can proceed.
