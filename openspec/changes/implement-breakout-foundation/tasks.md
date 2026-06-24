## 1. Scope and baseline

- [ ] 1.1 Review current `src/app/breakout/*`, `src/core/*`, `tests/test_breakout_foundation.py`, and the relevant OpenSpec specs.
- [ ] 1.2 Confirm this slice remains foundation-only and does not enable live broker execution or production full-auto.

## 2. Runtime/data foundation

- [ ] 2.1 Define or harden typed config models for operation modes, symbols, timeframes, data sources, and baseline strategy parameters.
- [ ] 2.2 Define canonical OHLCV bar, tick, and optional order-book/density data contracts.
- [ ] 2.3 Implement provider abstractions for historical bars, recent/streaming ticks, and optional order-book snapshots.
- [ ] 2.4 Implement UTC normalization, deduplication, ordering validation, resampling/gap handling, and source metadata propagation.

## 3. Level/setup/scoring foundation

- [ ] 3.1 Implement pivot high/low, round-number, daily high/low, cascade, and trendline level detection where local inputs support it.
- [ ] 3.2 Implement level validity checks for min touches, H1/M15 visibility, reaction threshold, and recent-break invalidation.
- [ ] 3.3 Implement ATR, EMA50/EMA200, ADX, consolidation/protorgovka, slow approach, activity, and density/proxy features.
- [ ] 3.4 Implement score weights, 70/50 thresholds, scenario priority order, and explicit rejection reasons.

## 4. Verification

- [ ] 4.1 Add or update no-lookahead tests for closed-bar-only analysis and pivot right-window confirmation.
- [ ] 4.2 Run `uv run ruff check .`.
- [ ] 4.3 Run `uv run pyright` or document the local blocker if pyright is unavailable.
- [ ] 4.4 Run `uv run pytest`.
- [ ] 4.5 Run `npx --yes @fission-ai/openspec@1.4.1 validate implement-breakout-foundation --strict --no-interactive` and `npx --yes @fission-ai/openspec@1.4.1 validate --all --strict --no-interactive`.
