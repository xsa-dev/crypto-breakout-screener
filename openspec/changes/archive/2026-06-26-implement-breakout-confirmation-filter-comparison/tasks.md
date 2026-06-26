## 1. OpenSpec readiness
- [x] 1.1 Confirm previous volatility-regime comparison change is archived and committed.
- [x] 1.2 Confirm no source-code edits are made before this OpenSpec review/approval.
- [x] 1.3 Confirm unrelated dirty files, especially `.dev/autonomous_dev.sh`, are not included in this change.
- [x] 1.4 Validate this OpenSpec change strictly before implementation.

## 2. Implementation
- [x] 2.1 Add disabled-by-default confirmation filter configuration with named fixed profiles.
- [x] 2.2 Implement causal pending-breakout confirmation state in the backtest path; delayed entries must not use future bars to enter at the original breakout timestamp.
- [x] 2.3 Implement `confirm-close-1`.
- [x] 2.4 Implement `confirm-close-2`.
- [x] 2.5 Implement `confirm-close-1-closepos70`.
- [x] 2.6 Implement `confirm-close-1-no-return-inside-range`.
- [x] 2.7 Add machine-readable confirmation skip/cancel counts to artifacts and batch summaries.
- [x] 2.8 Keep gate, feature, risk, and confirmation profile/settings/count fields separate.
- [x] 2.9 Preserve default/reference behavior when confirmation filters are disabled.

## 3. Tests
- [x] 3.1 Add unit tests proving disabled confirmation preserves existing trade selection.
- [x] 3.2 Add tests proving one-close confirmation delays entry until confirmation is available.
- [x] 3.3 Add tests proving two-close confirmation requires consecutive closes.
- [x] 3.4 Add tests for close-position threshold, including `high == low` safe failure.
- [x] 3.5 Add tests for return-inside-range cancellation.
- [x] 3.6 Add tests for deterministic skip/cancel reason counts.
- [x] 3.7 Add batch tests for profile resolution and CSV/JSON serialization fields.
- [x] 3.8 Add no-lookahead tests that fail if confirmation enters at the original breakout bar using future data.

## 4. Experiments
- [x] 4.1 Run full verification before quarterly experiments: pytest, ruff, pyright, OpenSpec strict validation, all-spec validation, and `git diff --check`.
- [x] 4.2 Run quarterly 2023-2024 public BTCUSDT batches for all required confirmation profiles.
- [x] 4.3 Parse and report pass/fail windows, blockers, trade count, net profit, worst drawdown, and confirmation skip counts.
- [x] 4.4 Compare each profile against `conservative-v1-m15-slope-positive-max-trades-8`.
- [x] 4.5 State explicitly whether the confirmation hypothesis is supported, improved-but-not-supported, or not supported.

## 5. Archive and final review
- [x] 5.1 Update this task list with experiment evidence.
- [x] 5.2 Run final full verification.
- [x] 5.3 Archive the OpenSpec change before the final commit boundary.
- [x] 5.4 Trim archive EOF whitespace if the OpenSpec CLI introduces it, then rerun all-spec validation and `git diff --check`.
- [x] 5.5 Run scoped final diff/security review and confirm no active `crypto_batch` processes remain.
- [x] 5.6 Commit only intended files; do not include unrelated `.dev/autonomous_dev.sh`.

## Evidence summary

Quarterly 2023-2024 comparison completed for all required confirmation profiles:

- `conservative-v1-m15-slope-positive-max-trades-8-confirm-close-1`: batch `1a3d58cd7cac587e`, passed 3/8, failed 5/8, trades 3922, net 78704.80, worst DD -1.320725, hypothesis_supported=false.
- `conservative-v1-m15-slope-positive-max-trades-8-confirm-close-2`: batch `a03dbd0bbf5783d2`, passed 2/8, failed 6/8, trades 3624, net 12074.00, worst DD -1.013299, hypothesis_supported=false.
- `conservative-v1-m15-slope-positive-max-trades-8-confirm-close-1-closepos70`: batch `3f2c5376626824a6`, passed 1/8, failed 7/8, trades 2469, net -194.00, worst DD -1.745294, hypothesis_supported=false.
- `conservative-v1-m15-slope-positive-max-trades-8-confirm-close-1-no-return-inside-range`: batch `f49ae333fba83e82`, passed 3/8, failed 5/8, trades 3853, net 85314.40, worst DD -1.288608, hypothesis_supported=false.

Conclusion: the tested confirmation filters do not support the breakout hypothesis and do not improve the reference `conservative-v1-m15-slope-positive-max-trades-8` profile, which remains 5/8 passed. The no-return-inside-range profile improves total net profit but still worsens pass count and leaves drawdown blockers.
