# Design

## Scope

This is a docs-only README refresh. The implementation edits only `README.md` after review approval.

## Evidence inspected for README content

- `pyproject.toml`: Python `>=3.13`, `uv`, dependencies, Ruff/Pyright configuration.
- `.env.example` and `src/core/env.py`: environment variable names and credential-free defaults.
- `src/app/__main__.py`: tradebot process, producer/consumer/signal-manager tasks, Bybit exchange-info loading.
- `src/web/__main__.py` and `src/web/routes.py`: FastAPI admin process, session auth, settings/signals/trades pages.
- `src/database/models.py`: settings/signals/trades plus breakout audit/replay/persistence tables.
- `src/core/models.py` and `src/app/breakout/*`: breakout DTOs, strategy config, entry/risk/execution/backtest foundation.
- `src/app/breakout/experiments/*.py`: public crypto backtest, batch, portfolio, and realistic-cost CLIs.
- `docs/breakout-operations.md`: local-first safety, dry-run/fake breakout execution, QA checklist, secret handling.
- `openspec/specs/*`: active capability contracts for breakout runtime, reporting, research governance, and operations/security docs.

## README shape

Recommended top-level sections:

1. Project overview/status.
2. Quick start and verification commands.
3. Environment and secret safety.
4. Running the tradebot and web admin.
5. Breakout research/backtesting commands.
6. Repository layout.
7. Data/artifacts and OpenSpec/docs pointers.
8. Safety/limitations.

## Language

The README should use Russian as the primary prose language. Keep command examples,
module names, CLI flags, file paths, dependency names, and canonical technical terms
in their original spelling where that is clearer. English-only prose should be
avoided except for short established labels or artifact names.

## Safety notes

- Keep `.env` values out of README examples.
- Describe Bybit/Telegram variables by name only and refer to `.env.example`.
- State breakout execution is local/fake unless a later OpenSpec change approves live adapters, matching `docs/breakout-operations.md`.
- Preserve `uv` commands and Python 3.13+ expectations.

## Verification

After README implementation:

- `npx --yes @fission-ai/openspec@1.4.1 validate update-readme-repository-overview --strict --no-interactive`
- `npx --yes @fission-ai/openspec@1.4.1 validate --all --strict --no-interactive`
- `uv run ruff check .`
- `uv run pyright`
- `uv run pytest`
- `git diff --check`

If full Python verification is blocked by pre-existing failures unrelated to README, report the exact failures and also run a README-specific sanity check (`python` script or grep) for forbidden secret-like values and broken local file references.
