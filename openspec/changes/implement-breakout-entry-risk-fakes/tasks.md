## 1. Entry lifecycle

- [ ] 1.1 Review implemented foundation contracts and relevant entry/risk specs.
- [ ] 1.2 Implement state enum and finite state machine transitions with explicit reason codes.
- [ ] 1.3 Implement entry intent generation for pre-entry, at-level, and post-breakout modes with default 30/30/40 caps.
- [ ] 1.4 Implement breakout confirmation, retest monitor, false-breakout handling, add-on monitor, partial exits, and complete states.

## 2. Risk and fake execution

- [ ] 2.1 Implement blocking risk manager checks for score/context, stop distance, position sizing, add-on risk budget, daily loss, max positions, degraded feed, and broker-state mismatch.
- [ ] 2.2 Implement fake execution adapter interfaces for order request, fill simulation, reconciliation, and idempotency tests.
- [ ] 2.3 Keep concrete live adapters and credentials blocked by deferred-scope gates.

## 3. Verification

- [ ] 3.1 Add tests for normal lifecycle, setup invalidation, false breakout, retest failure, add-on rejection, partial exits, and daily-loss/max-position blocking.
- [ ] 3.2 Run `uv run ruff check .`.
- [ ] 3.3 Run `uv run pyright` or document the local blocker if pyright is unavailable.
- [ ] 3.4 Run `uv run pytest`.
- [ ] 3.5 Run OpenSpec validation for this change and all specs.
