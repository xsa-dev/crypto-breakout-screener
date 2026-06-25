# Tasks

## 1. OpenSpec readiness

- [x] 1.1 Confirm the change is scoped to existing `breakout-deferred-scope-gates` capability.
- [x] 1.2 Validate proposal/spec/tasks before source edits.

## 2. Implementation

- [x] 2.1 Add a local fail-closed `full_auto` contract-validation guard to `BreakoutStrategyConfig`.
- [x] 2.2 Preserve `OperationMode.FULL_AUTO` as an enum/contract value without enabling production behavior by default.
- [x] 2.3 Add focused tests for default `semi_auto`, unapproved `full_auto` rejection, and contract-validation-only instantiation.

## 3. Verification and archive

- [x] 3.1 Run OpenSpec validation for the change and all specs.
- [x] 3.2 Run relevant project tests, lint, and typecheck.
- [x] 3.3 Perform self-review against the deferred-scope acceptance criteria and security boundaries.
- [x] 3.4 Mark tasks complete, archive the change, validate archived specs, verify no spec/archive duplicate names, and commit locally.
