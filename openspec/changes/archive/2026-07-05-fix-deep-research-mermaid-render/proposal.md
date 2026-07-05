# Proposal

## Why

GitHub still reports a Mermaid rendering error in `docs/ai/task/deep-research-report.md` after the readability cleanup:

```text
Lexical error on line 25. Unrecognized text.
...lerts] <-- H P <-- G P <-- B
```

The remaining issue is the architecture `flowchart` block using reverse links (`<--`) that are fragile in GitHub Mermaid rendering. The source report should render cleanly in GitHub preview.

## What Changes

- Update only `docs/ai/task/deep-research-report.md`.
- Replace fragile reverse Mermaid links with forward `-->` links or another GitHub-safe diagram form.
- Preserve the architecture meaning and all existing prose/table content.

## Success Criteria

- No Mermaid block contains ` <-- ` reverse links.
- The document still has balanced fenced code blocks and H1 `# SCNR Pro Boy`.
- OpenSpec validation and `git diff --check` pass.

## Non-goals

- No source-code changes.
- No dependency, lockfile, generated artifact, or trading logic changes.
- No archive/commit/push unless separately requested.
