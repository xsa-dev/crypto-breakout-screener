# Code-agent guide for SCNR Pro Boy docs

Используй этот файл как entrypoint перед изменениями breakout-логики, research/backtesting, runbooks или OpenSpec contracts.

## Reading order

### Для breakout strategy / scoring / FSM / risk

1. `docs/ai/task/README.md`
2. `docs/ai/task/source-manifest.yaml`
3. `docs/ai/task/requirements-index.md`
4. `docs/ai/task/source-traceability.md`
5. relevant source material:
   - `docs/ai/task/deep-research-report.md`
   - `docs/ai/task/IMG_2656.transcript.md`
   - original `docs/ai/task/IMG_2656.JPEG` when visual confirmation is needed
6. relevant OpenSpec specs under `openspec/specs/`
7. relevant code/tests from the traceability table

### Для operations / degraded mode / fake execution / risk-stop

1. `docs/breakout-operations.md`
2. `openspec/specs/breakout-operations-security-docs/spec.md`
3. `src/app/breakout/health.py`
4. `src/app/breakout/risk_manager.py`
5. `src/app/breakout/execution.py`
6. `tests/test_breakout_ops_security_docs.py` and related breakout tests

### Для research planning / hypothesis review

1. `docs/ai/task/breakout-realistic-cost-timeout-2026-06-28.md`
2. `openspec/specs/breakout-research-hypothesis-governance/spec.md`
3. archived OpenSpec changes for prior negative evidence
4. current artifacts only if the user asks to inspect them

## Safety rules

- Do not infer live/full-auto breakout permission from source strategy documents.
- Do not treat fake fills as broker evidence.
- Do not treat baseline-only or friction-light `8/8` as realistic-cost success.
- Do not use `breakout-realistic-cost-timeout-2026-06-28.md` to rewrite the source strategy; it is research evidence, not the source method.
- Do not inspect or print secrets from `.env`, credentials, authorization headers, private endpoints, API keys, bot tokens, or local private account data.
- Do not edit Python/source code before an approved OpenSpec change exists.
- Keep docs/indexing changes separate from source-code changes and dependency updates.

## Source roles

| Role | Meaning | Examples |
|---|---|---|
| `authoritative_strategy_source` | Defines intended strategy semantics | `deep-research-report.md`, original infographic/PDF |
| `visual_source` | Needs transcript/extraction for normal text search | `IMG_2656.JPEG`, `Торговля пробоев.pdf` |
| `research_evidence` | Records empirical results, blockers, falsification, or pause decisions | `breakout-realistic-cost-timeout-2026-06-28.md` |
| `operator_runbook` | Explains local operation and safety procedures | `breakout-operations.md` |

## Before changing code

Check:

- Which `BRK-*` requirement IDs apply?
- Which OpenSpec capability governs the change?
- Which source block justifies the behavior?
- Which tests already cover or should cover it?
- Does the change touch deferred scope such as live broker adapters, full-auto production, concrete exchange execution, UI/operator dashboard, monitoring/ops, or production hardening?

If any answer is unclear, create or rebaseline an OpenSpec change before editing source.
