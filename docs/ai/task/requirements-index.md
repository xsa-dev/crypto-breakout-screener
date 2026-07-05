# Breakout source requirements index

Этот индекс даёт стабильные documentation IDs для ключевых требований из source materials. Он помогает кодагенту ссылаться на требования в OpenSpec changes, reviews, tests и commit messages.

Нормативные SHALL/MUST-контракты остаются в `openspec/specs/`; этот файл — навигационный слой.

## Source governance

| ID | Requirement summary | Primary source | Related OpenSpec |
|---|---|---|---|
| BRK-SRC-001 | Treat `docs/ai/task/` as the primary algorithmic source for the breakout screener/trading-system strategy. | `deep-research-report.md`; `IMG_2656.JPEG`; `Торговля пробоев.pdf` | `breakout-research-hypothesis-governance` |
| BRK-SRC-002 | Do not replace the documented breakout method with unrelated strategy invention. Deviations must be recorded as implementation constraints. | `deep-research-report.md` | `breakout-research-hypothesis-governance` |
| BRK-SRC-003 | Separate source strategy requirements from empirical research evidence and timeout decisions. | `breakout-realistic-cost-timeout-2026-06-28.md` | `breakout-research-hypothesis-governance` |

## Level detection and setup

| ID | Requirement summary | Primary source | Related OpenSpec |
|---|---|---|---|
| BRK-LVL-001 | Detect levels from pivot high, pivot low, round numbers, daily high/low, and cascade levels. | `deep-research-report.md`; `IMG_2656.transcript.md` | `breakout-level-engine` |
| BRK-LVL-002 | A level should have at least 2-3 touches, visibility on H1/M15, no recent breakout, and meaningful reaction. | `deep-research-report.md`; `IMG_2656.transcript.md` | `breakout-level-engine` |
| BRK-LVL-003 | Pivot high/low logic must avoid look-ahead; right-window pivots are valid only after required bars close. | `deep-research-report.md` | `breakout-runtime-and-data`; `breakout-level-engine` |
| BRK-SETUP-001 | Evaluate consolidation/compression, slow approach, trend context, volume/activity, and density/support before breakout. | `deep-research-report.md`; `IMG_2656.transcript.md` | `breakout-setup-scoring` |
| BRK-SETUP-002 | Baseline breakout score has five 20-point factors with max score 100. | `deep-research-report.md`; `IMG_2656.transcript.md` | `breakout-setup-scoring` |
| BRK-SETUP-003 | Score thresholds classify decisions: `>=70` accept, `50-69` lower risk/possible, `<50` skip/wait. | `deep-research-report.md`; `IMG_2656.transcript.md` | `breakout-setup-scoring`; `breakout-risk-position-execution` |

## Entry, confirmation, retest, and exits

| ID | Requirement summary | Primary source | Related OpenSpec |
|---|---|---|---|
| BRK-ENTRY-001 | Support three entry modes: before breakout, at the level, and after breakout. | `deep-research-report.md`; `IMG_2656.transcript.md` | `breakout-entry-state-machine` |
| BRK-ENTRY-002 | Default entry split is 30% before breakout, 30% at level, and 40% after breakout/close above level. | `deep-research-report.md`; `IMG_2656.transcript.md` | `breakout-risk-position-execution`; `breakout-entry-state-machine` |
| BRK-ENTRY-003 | Breakout confirmation requires price beyond level plus buffer, sufficient score, and optional trend filter. | `deep-research-report.md`; `IMG_2656.transcript.md` | `breakout-entry-state-machine`; `breakout-setup-scoring` |
| BRK-ENTRY-004 | Retest is valid only when price returns to the level zone, holds structure, and forms a new impulse. | `deep-research-report.md`; `IMG_2656.transcript.md` | `breakout-entry-state-machine` |
| BRK-ENTRY-005 | False breakout is a first-class failure scenario requiring close/invalidation; reversal needs explicit opt-in config. | `deep-research-report.md`; `IMG_2656.transcript.md` | `breakout-entry-state-machine`; `breakout-risk-position-execution` |
| BRK-RISK-001 | Base risk per trade is about 0.5%-1% of deposit unless a narrower profile overrides it. | `IMG_2656.transcript.md`; `deep-research-report.md` | `breakout-risk-position-execution` |
| BRK-RISK-002 | Additions are limited, typically 10%-20% of position per add, with at most two additions unless config changes. | `deep-research-report.md`; `IMG_2656.transcript.md` | `breakout-risk-position-execution` |
| BRK-RISK-003 | Exit framework uses staged take profit: 30%, 50%, and 20% runner/trailer; stop moves to breakeven after first fixation. | `deep-research-report.md`; `IMG_2656.transcript.md` | `breakout-risk-position-execution` |
| BRK-RISK-004 | Daily loss, max position, max additions, volatility filters, and session rules are risk-manager inputs. | `IMG_2656.transcript.md`; `deep-research-report.md` | `breakout-risk-position-execution` |

## State machine and scenarios

| ID | Requirement summary | Primary source | Related OpenSpec |
|---|---|---|---|
| BRK-FSM-001 | Preserve logical states from level search through setup, scenario selection, entry, confirmation, retest/addition, false breakout, fixation, and exit. | `deep-research-report.md`; `IMG_2656.transcript.md` | `breakout-entry-state-machine` |
| BRK-FSM-002 | Scenario selection should consider consolidation, cascade levels, local maximum near level, trendline, and density/support; otherwise no trade. | `IMG_2656.transcript.md`; `deep-research-report.md` | `breakout-entry-state-machine`; `breakout-setup-scoring` |
| BRK-FSM-003 | Main flow and alternative failure flow must remain explicit; false breakout and отказ от сделки are not silent exits. | `IMG_2656.transcript.md`; `deep-research-report.md` | `breakout-entry-state-machine` |

## Backtesting, evidence, and operations

| ID | Requirement summary | Primary source | Related OpenSpec |
|---|---|---|---|
| BRK-BT-001 | Testing must separate in-sample/out-of-sample, walk-forward, Monte Carlo or robustness checks where applicable. | `deep-research-report.md` | `breakout-backtesting-reporting` |
| BRK-BT-002 | Historical evidence must classify cost assumptions and not promote baseline-only results as realistic-cost success. | `breakout-realistic-cost-timeout-2026-06-28.md` | `breakout-research-hypothesis-governance` |
| BRK-BT-003 | The current realistic-cost/shared-bankroll branch is paused as negative robustness evidence until explicitly resumed or rebaselined. | `breakout-realistic-cost-timeout-2026-06-28.md` | `breakout-research-hypothesis-governance` |
| BRK-OPS-001 | Degraded feed/config/fake-broker/risk-stop states block new entries with machine-readable reasons. | `docs/breakout-operations.md` | `breakout-operations-security-docs`; `breakout-risk-position-execution` |
| BRK-OPS-002 | Breakout execution remains local/fake unless a later OpenSpec change approves a live adapter. | `docs/breakout-operations.md`; `README.md` | `breakout-deferred-scope-gates`; `breakout-operations-security-docs` |
| BRK-SEC-001 | Secrets, tokens, authorization headers, private endpoints, and private account data must not be committed or printed in docs/logs/tests. | `deep-research-report.md`; `docs/breakout-operations.md` | `breakout-operations-security-docs` |
| BRK-SEC-002 | Production hardening, TLS, backups, role separation, incident response, and live credentials require separate approved scope. | `docs/breakout-operations.md`; `deep-research-report.md` | `breakout-deferred-scope-gates`; `breakout-operations-security-docs` |
