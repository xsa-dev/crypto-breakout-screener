# Proposal

## Why

`README.md` still reads like the generic Ayaz Sh template and only briefly mentions the original Bybit pump tradebot. The repository has since grown into a breakout screener/research codebase with:

- the original Bybit pump screener/tradebot runtime and FastAPI admin UI;
- a local breakout strategy foundation under `src/app/breakout`;
- deterministic public-crypto backtesting, batch, portfolio, and realistic-cost research CLIs;
- OpenSpec-governed research and operational safety docs;
- SQLite persistence/audit tables and generated local artifacts.

A new contributor/operator should be able to open the README and understand what this repository is now, what is safe to run locally, what requires credentials, where the main code/docs live, and which verification commands are authoritative.

## What Changes

Rewrite `README.md` as a repository-specific overview that is grounded in the current repo instead of the initial project template. The README should cover:

- current project purpose and status;
- safe setup and quality checks with `uv`;
- two runtime processes: tradebot and web admin;
- environment variables and secret-safety expectations without exposing any secrets;
- source layout for `src/core`, `src/database`, `src/app`, `src/web`, and `src/app/breakout`;
- breakout research/backtest entry points and artifact directories;
- important docs/OpenSpec pointers;
- clear limits around dry-run/fake breakout execution vs credentialed Bybit tradebot behavior;
- Russian-language documentation copy as the primary reader-facing language, because the repo, course template, existing README, comments, and target operators are Russian-first.

## Success Criteria

- README no longer presents the repo primarily as a generic template.
- README statements are traceable to inspected repository files and docs.
- README does not claim unsupported live/full-auto breakout execution.
- README keeps secrets out of examples and points users to `.env.example`.
- README is written in Russian for the main explanatory text; English terms and command/module names may remain where they are canonical.
- Documentation-only scope: no source, dependency, lockfile, database, or artifact behavior changes.

## Non-goals

- No Python source changes.
- No dependency or lockfile changes.
- No changes to OpenSpec capability specs except this README update proposal/spec delta.
- No new runtime features, migrations, scripts, generated reports, or research results.
- No commit, archive, or push unless separately requested.
