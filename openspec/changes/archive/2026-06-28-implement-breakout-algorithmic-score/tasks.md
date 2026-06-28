## 1. Implementation
- [x] 1.1 Add score model/settings for `algorithmic-breakout-score-v1`.
- [x] 1.2 Compute component scores from entry-time public features.
- [x] 1.3 Add eligibility buckets and score-based blockers.
- [x] 1.4 Export score components and distributions in candidate/portfolio artifacts.

## 2. Tests
- [x] 2.1 Test score components sum to deterministic total.
- [x] 2.2 Test score below 70 blocks with the required reason.
- [x] 2.3 Test 70..84 and 85+ produce correct priority buckets.
- [x] 2.4 Test future/realized outcome fields are not accepted as score inputs.

## 3. Verification
- [x] 3.1 Run targeted score tests.
- [x] 3.2 Run strict OpenSpec validation.
- [x] 3.3 Run `git diff --check`.
