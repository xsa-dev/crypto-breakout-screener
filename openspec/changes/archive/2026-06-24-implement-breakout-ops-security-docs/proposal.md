## Why

Before the strategy can move toward semi-auto or live adapter work, operators need clear health checks, degraded-mode behavior, secret-handling rules, and documentation for safe local operation and QA.

## What Changes

- Implement health/degraded-mode checks for stale market data, config errors, fake broker/order mismatch, and risk stop states.
- Add alerts/logging hooks that remain local and do not expose secrets.
- Document setup, configuration, operator workflow, API/web surfaces, test methodology, runbook, deployment assumptions, secret handling, QA checklist, and changelog/config changelog expectations.

## Non-Goals

- No production monitoring stack, external alerting integration, cloud deployment, or live broker adapter.
- No full operator dashboard beyond existing local admin surfaces unless required to expose health state safely.
