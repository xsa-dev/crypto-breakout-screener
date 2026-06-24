## 1. Scope and specs

- [x] 1.1 Review existing `breakout-setup-scoring` spec and current setup scoring implementation.
- [x] 1.2 Add a narrow OpenSpec delta for deterministic local context filters under the existing capability.

## 2. Implementation

- [x] 2.1 Add typed context driver/config models without external integrations.
- [x] 2.2 Update setup scoring to apply side-aware context penalties and hard blocks with explicit rejection reasons.
- [x] 2.3 Add focused unit tests for unchanged/no-context behavior, score lowering, hard blocking, and side symmetry.

## 3. Verification and landing

- [x] 3.1 Run OpenSpec validation for the change and all specs.
- [x] 3.2 Run `uv run ruff check .`.
- [x] 3.3 Run `uv run pyright`.
- [x] 3.4 Run `uv run pytest`.
- [x] 3.5 Self-review the diff against acceptance criteria and deferred-scope gates.
- [x] 3.6 Mark tasks complete, archive the change, re-run OpenSpec validation, and create one local commit.
