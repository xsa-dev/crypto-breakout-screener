## 1. Repository review
- [x] 1.1 Inspect current README, project manifest, env/config, runtime entrypoints, web/admin routes, database models, breakout modules, experiment CLIs, operations docs, and OpenSpec specs.
- [x] 1.2 Identify unsupported claims to avoid: generic-template positioning and live/full-auto breakout execution.

## 2. README implementation
- [x] 2.1 Rewrite `README.md` as the current repository overview.
- [x] 2.2 Document setup, verification, runtime, admin, breakout research CLIs, repo layout, docs pointers, data/artifacts, and safety limitations.
- [x] 2.3 Keep examples secret-free and reference `.env.example` instead of inline credential values.
- [x] 2.4 Write the main README prose in Russian while keeping commands, paths, module names, and canonical technical terms readable.

## 3. Verification
- [x] 3.1 Run strict OpenSpec validation for this change and all specs.
- [x] 3.2 Run `uv run ruff check .`.
- [x] 3.3 Run `uv run pyright` (script shim failed to spawn; verified with `uv run python -m pyright`).
- [x] 3.4 Run `uv run pytest` (script shim used wrong interpreter before dependency resolution; verified with `uv run python -m pytest`).
- [x] 3.5 Run `git diff --check`.
- [x] 3.6 Report git status and any pre-existing unrelated dirty/staged files separately from the README docs change.
