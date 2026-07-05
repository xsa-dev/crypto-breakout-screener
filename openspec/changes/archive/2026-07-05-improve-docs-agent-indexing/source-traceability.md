# Source Traceability Review Aid

This planning aid maps the inspected documents to the proposed indexing deliverables. Normative requirements live in `specs/breakout-operations-security-docs/spec.md`.

| Source | Observed content | Indexing gap | Proposed deliverable |
|---|---|---|---|
| `docs/ai/task/deep-research-report.md` | Russian source report / ТЗ for breakout strategy, with strategy rules, FSM, architecture, config/storage, testing, acceptance, security | Large document with no stable requirement IDs or section-level traceability | `requirements-index.md`, `source-traceability.md`, `docs/ai/task/README.md`, manifest metadata |
| `docs/ai/task/IMG_2656.JPEG` | Visual infographic: main breakout-with-retest strategy and implementation blocks | Not searchable by grep/RAG without a text companion | `IMG_2656.transcript.md`, manifest `visual_source` metadata |
| `docs/ai/task/Торговля пробоев.pdf` | Original PDF source material; local text read produced binary/unusable output | Not reliably text-indexable in current tooling | Manifest marks `needs_extraction: true`; optional future extracted companion |
| `docs/ai/task/breakout-realistic-cost-timeout-2026-06-28.md` | Decision record: current realistic-cost/shared-bankroll branch is paused as negative evidence | Could be confused with source strategy requirements | `docs/ai/task/README.md`, manifest `research_evidence` role, `docs/CODEAGENT.md` warning |
| `docs/breakout-operations.md` | Local runbook: setup, dry-run, health/degraded mode, runbooks, security, QA | Useful for agents but lacks explicit code-agent usage and reason-code/module mapping | Update with `Code-agent usage` and reason-code table |
| `openspec/specs/*` | Normative capability contracts | Current path/spec linkage not summarized for agents | `source-traceability.md` maps source blocks to spec directories |

## First implementation slice

The first implementation of this change should add indexes and metadata only. It should not modify source/runtime code or attempt to solve the underlying research strategy.

## Deferred work

- Full OCR/extraction of `Торговля пробоев.pdf` if reliable tooling is not available in the implementation session.
- Automatic docs-index lint in CI.
- Any code changes to implement uncovered requirements.
