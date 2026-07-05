# Source-to-spec/code traceability

Этот файл связывает source blocks из `docs/ai/task/` с OpenSpec capabilities, likely code areas и тестами. Он нужен для code-agent retrieval и review; нормативные требования остаются в `openspec/specs/`.

## Traceability matrix

| Source block | Requirement IDs | OpenSpec capability | Likely code area | Tests / verification |
|---|---|---|---|---|
| Source material governance | BRK-SRC-001, BRK-SRC-002, BRK-SRC-003 | `breakout-research-hypothesis-governance` | OpenSpec changes; docs indexes | `npx --yes @fission-ai/openspec@1.4.1 validate --all --strict --no-interactive` |
| Market data and no-lookahead constraints | BRK-LVL-003 | `breakout-runtime-and-data`, `breakout-level-engine` | `src/app/breakout/normalizer.py`, `src/app/breakout/providers.py`, `src/app/breakout/level_engine.py` | `tests/test_breakout_foundation.py`, `tests/test_crypto_historical_experiment.py` |
| Level search: pivots, round numbers, daily high/low, cascade levels | BRK-LVL-001, BRK-LVL-002 | `breakout-level-engine` | `src/app/breakout/level_engine.py` | `tests/test_breakout_foundation.py` |
| Setup quality and breakout score | BRK-SETUP-001, BRK-SETUP-002, BRK-SETUP-003 | `breakout-setup-scoring` | `src/app/breakout/setup_scoring.py`, `src/app/breakout/algorithmic_score.py` | `tests/test_breakout_foundation.py`, `tests/test_breakout_backtesting_reporting.py` |
| Entry modes: before, at level, after breakout | BRK-ENTRY-001, BRK-ENTRY-002 | `breakout-entry-state-machine`, `breakout-risk-position-execution` | `src/app/breakout/entry_engine.py`, `src/app/breakout/risk_manager.py` | `tests/test_breakout_entry_risk_fakes.py` |
| Confirmation, retest, false breakout, lifecycle transitions | BRK-ENTRY-003, BRK-ENTRY-004, BRK-ENTRY-005, BRK-FSM-001, BRK-FSM-003 | `breakout-entry-state-machine` | `src/app/breakout/entry_engine.py`, lifecycle-related models in `src/core/models.py` | `tests/test_breakout_entry_risk_fakes.py`, `tests/test_breakout_foundation.py` |
| Scenario selection: consolidation, cascade, local maximum, trendline, density/support | BRK-FSM-002, BRK-SETUP-001 | `breakout-entry-state-machine`, `breakout-setup-scoring` | `src/app/breakout/setup_scoring.py`, `src/app/breakout/level_engine.py`, `src/app/breakout/entry_engine.py` | `tests/test_breakout_foundation.py` |
| Risk sizing, max position, additions, stop-loss, take-profit split | BRK-RISK-001, BRK-RISK-002, BRK-RISK-003, BRK-RISK-004 | `breakout-risk-position-execution` | `src/app/breakout/risk_manager.py`, `src/app/breakout/execution.py` | `tests/test_breakout_entry_risk_fakes.py`, `tests/test_breakout_persistence_audit.py` |
| Backtesting, reports, evidence tiers, realistic-cost robustness | BRK-BT-001, BRK-BT-002, BRK-BT-003 | `breakout-backtesting-reporting`, `breakout-research-hypothesis-governance` | `src/app/breakout/backtesting.py`, `src/app/breakout/experiments/*.py` | `tests/test_breakout_backtesting_reporting.py`, `tests/test_crypto_batch_experiment.py`, `tests/test_realistic_cost_profile_search.py` |
| Operations, degraded mode, fake execution reconciliation, risk-stop | BRK-OPS-001, BRK-OPS-002 | `breakout-operations-security-docs`, `breakout-risk-position-execution` | `src/app/breakout/health.py`, `src/app/breakout/risk_manager.py`, `src/app/breakout/execution.py` | `tests/test_breakout_ops_security_docs.py`, `tests/test_breakout_entry_risk_fakes.py` |
| Security, secrets, production hardening boundaries | BRK-SEC-001, BRK-SEC-002 | `breakout-operations-security-docs`, `breakout-deferred-scope-gates` | `src/core/env.py`, `src/core/config.py`, docs/OpenSpec | `tests/test_breakout_ops_security_docs.py`, manual secret-safety diff review |

## Source document map

| Source | Main covered blocks | Companion / index |
|---|---|---|
| `docs/ai/task/deep-research-report.md` | Strategy, levels, setup score, FSM, architecture, config/storage, testing, docs/security | `requirements-index.md`, this file |
| `docs/ai/task/IMG_2656.JPEG` | Visual rules for entry percentages, score table, risk manager, state machine, scenario selection | `IMG_2656.transcript.md` |
| `docs/ai/task/Торговля пробоев.pdf` | Original PDF source material | Needs extraction/OCR; tracked in `source-manifest.yaml` |
| `docs/ai/task/breakout-realistic-cost-timeout-2026-06-28.md` | Negative realistic-cost evidence and reassessment questions | `requirements-index.md` BRK-BT-* |
| `docs/breakout-operations.md` | Local runbook, degraded mode, fake execution, QA, security | `docs/CODEAGENT.md`, BRK-OPS-* / BRK-SEC-* |

## Maintenance rules

- When a source document moves, update `source-manifest.yaml` and this matrix.
- When adding a new `BRK-*` requirement ID, keep it unique and map it to at least one source and one OpenSpec capability.
- When code modules move, update likely code areas here; do not use stale module names in new OpenSpec changes.
- If PDF extraction is added later, update `source-manifest.yaml` and add the extracted companion to this map.
