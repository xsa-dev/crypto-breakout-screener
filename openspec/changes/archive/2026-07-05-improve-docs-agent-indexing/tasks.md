## 1. Baseline and planning
- [x] 1.1 Inspect current `docs/` inventory and headings.
- [x] 1.2 Inspect the source report, timeout decision record, operations guide, JPEG infographic, and PDF extraction behavior.
- [x] 1.3 Confirm current git status and note unrelated/active changes before editing.

## 2. Documentation index layer
- [x] 2.1 Add `docs/README.md` as the root documentation navigation entrypoint.
- [x] 2.2 Add `docs/CODEAGENT.md` with code-agent reading order, safety rules, and non-inference warnings.
- [x] 2.3 Add `docs/ai/task/README.md` that classifies source materials, visual/PDF assets, and research evidence.
- [x] 2.4 Add `docs/ai/task/source-manifest.yaml` listing every source file, type, role, language, topics, and indexing caveats.
- [x] 2.5 Add `docs/ai/task/requirements-index.md` with stable requirement IDs for key strategy/risk/testing/security requirements.
- [x] 2.6 Add `docs/ai/task/source-traceability.md` mapping source blocks to OpenSpec capabilities, likely code areas, and tests.
- [x] 2.7 Add `docs/ai/task/IMG_2656.transcript.md` describing visible infographic blocks and rules without inventing unseen text.
- [x] 2.8 Update `docs/breakout-operations.md` with a concise code-agent usage section and reason-code/module mapping.

## 3. Safety boundaries
- [x] 3.1 Preserve strategy semantics; do not rewrite source research content or empirical evidence.
- [x] 3.2 Keep PDF/JPEG originals unchanged.
- [x] 3.3 Do not modify Python source, dependencies, lockfiles, runtime behavior, generated research artifacts, or secrets.

## 4. Verification
- [x] 4.1 Run strict OpenSpec validation for this change and all specs: `validate improve-docs-agent-indexing` passed; `validate --all` reported 13 passed, 0 failed.
- [x] 4.2 Run `git diff --check`: passed.
- [x] 4.3 Run targeted docs-index sanity checks for required files, manifest path existence, unique requirement IDs, traceability references, and visual/PDF companion status: missing required files `[]`, missing manifest paths `[]`, duplicate requirement IDs `[]`, missing specs `[]`, missing transcript blocks `[]`, PDF marked `needs_extraction: true`, old `doc/ai/task` refs `[]`.
- [x] 4.4 Report git status and keep unrelated staged/dirty files separate from this docs-indexing change.
