# Design

## Scope

Documentation-only indexing layer for the consolidated `docs/` tree.

This change depends on the completed-but-not-yet-archived `consolidate-doc-and-docs-directories` layout, where source materials live under `docs/ai/task/`. If that layout is not landed first, implementation should either land it first or rebaseline paths before editing docs.

## Files to add or update

Add:

- `docs/README.md`
- `docs/CODEAGENT.md`
- `docs/ai/task/README.md`
- `docs/ai/task/source-manifest.yaml`
- `docs/ai/task/requirements-index.md`
- `docs/ai/task/source-traceability.md`
- `docs/ai/task/IMG_2656.transcript.md`

Update minimally:

- `docs/breakout-operations.md` with a short code-agent usage section and reason-code/module table.

Do not rewrite:

- `docs/ai/task/deep-research-report.md` except for optional metadata links if needed;
- `docs/ai/task/breakout-realistic-cost-timeout-2026-06-28.md` except for optional metadata links if needed;
- `docs/ai/task/Торговля пробоев.pdf`;
- `docs/ai/task/IMG_2656.JPEG`.

## Indexing model

### Source categories

Use explicit source roles:

- `authoritative_strategy_source`: source materials that define intended strategy semantics;
- `visual_source`: image/PDF materials that need transcript/extracted text for reliable retrieval;
- `research_evidence`: empirical results, falsification notes, timeout decisions, scorecards;
- `operator_runbook`: operational/safety documentation;
- `agent_guide`: navigation and usage rules for code agents.

### Requirement IDs

Use stable IDs grouped by topic:

- `BRK-SRC-*`: source/material governance;
- `BRK-LVL-*`: level detection and validity;
- `BRK-SETUP-*`: setup/score/context requirements;
- `BRK-ENTRY-*`: entry modes and confirmation;
- `BRK-FSM-*`: state machine requirements;
- `BRK-RISK-*`: risk/position/exit constraints;
- `BRK-BT-*`: backtest/reporting/evidence constraints;
- `BRK-OPS-*`: operations/degraded/security documentation;
- `BRK-SEC-*`: secrets, access, audit, legal/safety constraints.

The index is documentation traceability, not a new implementation contract. Normative SHALL/MUST behavior remains in OpenSpec specs.

### Visual/PDF handling

`IMG_2656.transcript.md` should describe only visible blocks and visible rules from the infographic, including:

- main strategy with retest;
- concept/search/setup/entry/confirmation/false-breakout/retest/addition/exit/density/market-direction/breakout-type blocks;
- state machine;
- scenario selection;
- breakout score;
- risk manager;
- market direction and context filter.

If reliable PDF extraction is unavailable, do not fabricate an extracted transcript. Mark the PDF in the manifest as `needs_extraction: true` and `text_companion: null` or equivalent.

## Verification

Run:

- `npx --yes @fission-ai/openspec@1.4.1 validate improve-docs-agent-indexing --strict --no-interactive`
- `npx --yes @fission-ai/openspec@1.4.1 validate --all --strict --no-interactive`
- `git diff --check`
- targeted docs-index sanity script that verifies:
  - required index files exist;
  - manifest paths exist;
  - no manifest path points to missing source files;
  - requirement IDs are unique;
  - traceability references use existing OpenSpec spec directories where applicable;
  - `IMG_2656.transcript.md` exists and names the visible high-level infographic blocks;
  - PDF extraction is either present as an existing companion file or explicitly marked as unavailable/needed.

Full Python lint/type/test gates are not required because this change does not modify code.
