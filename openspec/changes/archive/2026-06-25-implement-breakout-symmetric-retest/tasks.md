## 1. OpenSpec readiness

- [x] 1.1 Confirm this is a narrow implementation of existing `breakout-entry-state-machine` symmetry/retest requirements.
- [x] 1.2 Validate the change and all specs before source implementation.

## 2. TDD implementation

- [x] 2.1 Add failing tests for side-symmetric short retest hold and failure.
- [x] 2.2 Add/keep long-side regression coverage.
- [x] 2.3 Implement the minimal lifecycle retest logic to pass the tests without live execution or persistence changes.

## 3. Verification and review

- [x] 3.1 Run `uv run pytest`.
- [x] 3.2 Run `uv run ruff check .`.
- [x] 3.3 Run `uv run pyright`.
- [x] 3.4 Run `npx --yes @fission-ai/openspec@1.4.1 validate implement-breakout-symmetric-retest --strict --no-interactive`.
- [x] 3.5 Run `npx --yes @fission-ai/openspec@1.4.1 validate --all --strict --no-interactive`.
- [x] 3.6 Run self-review against the approved spec and confirm no live execution or unrelated changes were introduced.
