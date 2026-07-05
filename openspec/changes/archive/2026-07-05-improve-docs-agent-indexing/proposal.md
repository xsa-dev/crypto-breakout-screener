# Proposal

## Why

The repository now keeps source and operator documentation under `docs/`, but the documents are still optimized mostly for human reading rather than code-agent retrieval and traceability.

Current issues observed in `docs/`:

- there is no root `docs/README.md` explaining which documents to read for which kind of work;
- `docs/ai/task/` mixes authoritative source materials, visual/PDF source files, and a negative research decision record without a local index;
- the JPEG infographic and PDF are not reliably text-indexable by normal grep/RAG/code-agent flows unless companion text files exist;
- the large `deep-research-report.md` has good content but no stable requirement IDs, manifest metadata, or source-to-spec/code traceability index;
- `docs/breakout-operations.md` is useful as a runbook but does not explicitly tell a code agent when to use it or which reason codes/modules it governs.

This makes it too easy for an agent to miss authoritative source blocks, confuse strategy requirements with research evidence, or infer unsupported live-trading scope.

## What Changes

Add a documentation indexing layer for code-agent use without rewriting strategy semantics or changing runtime behavior:

- add a root documentation index;
- add a source-material index under `docs/ai/task/`;
- add machine-readable source metadata;
- add requirement IDs and source-to-spec/code traceability tables;
- add a code-agent guide for safe document usage;
- add a text companion for the JPEG infographic;
- classify the PDF as requiring extraction/OCR unless reliable text extraction is produced within scope;
- add targeted sanity verification for the new index files.

## Success Criteria

- A reader or code agent can start at `docs/README.md` and find the correct source, runbook, evidence, and OpenSpec documents.
- `docs/ai/task/README.md` clearly separates authoritative strategy sources from research evidence and visual/PDF files.
- `docs/ai/task/source-manifest.yaml` lists every source material with type, status, language, topics, and indexing caveats.
- `docs/ai/task/requirements-index.md` assigns stable IDs to the key breakout strategy/risk/testing/security requirements.
- `docs/ai/task/source-traceability.md` maps source blocks to OpenSpec capabilities, likely code areas, and tests.
- `docs/ai/task/IMG_2656.transcript.md` captures the visible infographic blocks in text form without inventing unseen content.
- `docs/CODEAGENT.md` tells agents what to read and what not to infer, especially around live/full-auto trading and negative evidence.
- OpenSpec validation, `git diff --check`, and a targeted docs-index sanity script pass.

## Non-goals

- No Python/source-code changes.
- No dependency or lockfile changes.
- No trading strategy rewrite or new research result.
- No generated artifact migration.
- No live-trading, broker-adapter, production, or full-auto scope expansion.
- No credential inspection or secret handling changes beyond documentation guidance.
- No archive/commit/push unless separately requested.
