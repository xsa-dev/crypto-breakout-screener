## ADDED Requirements

### Requirement: BTCUSDT research success uses net-of-costs robustness verdicts
The BTCUSDT breakout research loop SHALL treat `8/8` after realistic costs as the success condition for robustness-search changes. Baseline-only `8/8` SHALL be insufficient and SHALL NOT stop the loop as a successful profile.

#### Scenario: Baseline-only 8/8 appears
- **WHEN** a candidate reaches `8/8` only under baseline or legacy costs
- **AND** fails one or more required quarters under realistic costs
- **THEN** the research loop records the baseline result as insufficient
- **AND** archives the candidate as falsified robustness evidence when the change closes
- **AND** continues to the next bounded hypothesis unless an external blocker prevents safe local work.

#### Scenario: Net-of-costs 8/8 appears
- **WHEN** a candidate reaches `8/8` under realistic costs using the required quarterly windows and thresholds
- **THEN** the research loop may stop with success for the research slice
- **AND** the final report states `successful profile = 8/8 after realistic costs`.

### Requirement: Telegram success notifications are gated by realistic-cost success
The BTCUSDT breakout research loop SHALL send a Telegram success notification only for a candidate that reaches `8/8` after realistic costs, not for baseline-only `8/8`.

#### Scenario: Baseline-only profile passes
- **WHEN** a candidate reaches baseline-only `8/8`
- **THEN** no Telegram success notification is sent
- **AND** the final report records that notification was intentionally withheld because baseline-only `8/8` is insufficient.

#### Scenario: Realistic-cost profile passes
- **WHEN** a candidate reaches `8/8` after realistic costs
- **THEN** a Telegram success notification is sent or the send failure is recorded
- **AND** the notification includes the change id, profile name, realistic cost settings, passed quarters, thresholds, summary artifact paths, and no secrets or private account data.
