## 1. Operations and safety

- [ ] 1.1 Review existing app/web startup paths, logging, settings, and breakout runtime contracts.
- [ ] 1.2 Implement local health/degraded-mode checks for feed gaps, config errors, fake broker/order mismatch, and risk stop states.
- [ ] 1.3 Ensure degraded mode blocks new entries and records explicit reasons.
- [ ] 1.4 Ensure logs/errors redact secrets and do not print credentials.

## 2. Documentation

- [ ] 2.1 Update README or docs with setup, dry-run behavior, configuration, and safe local execution.
- [ ] 2.2 Add operator guide/runbook for feed gaps, restart/reconnect checks, daily loss stop, false breakout handling, and QA release checks.
- [ ] 2.3 Add security notes for env secrets, least privilege, rotation, role separation, TLS assumptions, backups, rollback, and incident checklist.
- [ ] 2.4 Add test methodology and test report template or current test report.

## 3. Verification

- [ ] 3.1 Add tests for degraded mode blocking, config-health failure, secret redaction, and restart/reconnect fake state reconciliation where implemented.
- [ ] 3.2 Run `uv run ruff check .`.
- [ ] 3.3 Run `uv run pyright` or document the local blocker if pyright is unavailable.
- [ ] 3.4 Run `uv run pytest`.
- [ ] 3.5 Run OpenSpec validation for this change and all specs.
