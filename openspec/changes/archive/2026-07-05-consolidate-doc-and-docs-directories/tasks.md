## 1. Baseline review
- [x] 1.1 Inspect current `doc/` and `docs/` directory inventories.
- [x] 1.2 Search repository references to the legacy source-material path, `docs/`, `deep-research-report`, `Торговля пробоев`, and `IMG_2656`.
- [x] 1.3 Confirm current git status and unrelated staged/dirty files before editing.

## 2. Directory consolidation
- [x] 2.1 Create `docs/ai/task/` and move useful source-material files into it.
- [x] 2.2 Remove stray `.DS_Store` files and empty obsolete `doc/` directories.
- [x] 2.3 Update README/OpenSpec/docs references to `docs/ai/task/...`.
- [x] 2.4 Preserve research document contents and binary source materials; do not rewrite strategy semantics.

## 3. Verification
- [x] 3.1 Run strict OpenSpec validation for this change and all specs.
- [x] 3.2 Run `git diff --check`.
- [x] 3.3 Run targeted path sanity checks for expected `docs/ai/task/*` files, no useful leftover `doc/` content, and updated path references.
- [x] 3.4 Report git status and separate unrelated staged/dirty files from this docs-layout change.
