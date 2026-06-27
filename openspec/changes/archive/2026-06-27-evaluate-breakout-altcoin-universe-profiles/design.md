# Design

## Context

The BTCUSDT-only line has repeatedly found gross/net profitability on selected quarters, especially with large-target exits, but the realistic-cost scorecard remains blocked by drawdown. Recent evidence:

- `target-4p0-hold-32` on BTCUSDT `2024q1`: net profit `340063.67`, profit factor `2.0268`, max drawdown `-0.6480`.
- Exposure scaling to `qty-0p5` reduced drawdown but failed `2024q2` on net profit, profit factor, and drawdown.
- Delayed close stops preserved profit on `2024q1` but worsened drawdown.

The next discriminating question is whether this breakout/large-target structure is BTC-specific negative evidence or whether a diversified liquid-crypto portfolio can produce a cleaner quarterly equity path with the same realistic costs and drawdown discipline.

## Universe

Use a fixed deterministic research allowlist instead of a live top-market-cap lookup. BTCUSDT remains the default baseline symbol, but the altcoin universe contains 50 non-BTC USDT symbols:

| Bucket | Symbols |
| --- | --- |
| Large majors | `ETHUSDT`, `SOLUSDT`, `BNBUSDT`, `XRPUSDT`, `DOGEUSDT`, `ADAUSDT`, `AVAXUSDT`, `LINKUSDT`, `TRXUSDT`, `TONUSDT` |
| Liquid L1/L2 and DeFi | `DOTUSDT`, `NEARUSDT`, `LTCUSDT`, `BCHUSDT`, `UNIUSDT`, `AAVEUSDT`, `APTUSDT`, `ARBUSDT`, `OPUSDT`, `INJUSDT` |
| Mid-cap majors | `SUIUSDT`, `SEIUSDT`, `ATOMUSDT`, `ETCUSDT`, `FILUSDT`, `ICPUSDT`, `IMXUSDT`, `RUNEUSDT`, `HBARUSDT`, `ALGOUSDT` |
| Theme/liquidity basket | `VETUSDT`, `THETAUSDT`, `FETUSDT`, `GRTUSDT`, `MKRUSDT`, `LDOUSDT`, `STXUSDT`, `JUPUSDT`, `WIFUSDT`, `PEPEUSDT` |
| Additional liquid names | `SHIBUSDT`, `FLOKIUSDT`, `BONKUSDT`, `ENAUSDT`, `PENDLEUSDT`, `TIAUSDT`, `TAOUSDT`, `WLDUSDT`, `ONDOUSDT`, `JASMYUSDT` |

Start with ETHUSDT as a data/implementation proof, then evaluate the 50-symbol universe as one shared-bankroll portfolio. Missing Bybit public history or unsupported symbols are recorded as blocked/negative evidence and are not silently replaced.

## Portfolio accounting

The portfolio research mode uses money-based accounting:

- starting equity: `10000 USDT` per quarterly window;
- one shared cash/equity curve across all selected symbols;
- no independent per-symbol deposits;
- fixed per-trade notional cap and fixed total open-exposure cap;
- no implicit leverage from simultaneous signals across many symbols;
- realistic costs applied to every symbol trade before portfolio aggregation;
- per-symbol PnL/contribution remains auditable, but success is determined by the combined portfolio quarter.

Threshold interpretation for this portfolio slice:

- `min_net_profit=0.0` applies to the portfolio quarter in USDT;
- `min_profit_factor=1.0` applies to closed portfolio trades in the quarter;
- `min_max_drawdown=-0.35` applies to the portfolio equity curve relative to `10000 USDT`;
- `require_no_feed_gaps=true` applies to all symbols used in the promoted portfolio run.

The report must include a safety-buffer table: distance from each pass threshold for every quarter. A thin pass is not hidden; the preferred robust result has positive net profit, PF above `1.0`, and drawdown materially inside the `-0.35` limit rather than barely touching it.

## Regime segmentation

The portfolio runner must not treat all market conditions as one undifferentiated sample. Before a profile is promoted to full portfolio scoring, the run must label deterministic market regimes from already available public OHLCV context data.

Minimum regime labels:

- `bull_long`: broad market trend and symbol context support long breakout exposure;
- `bear_short_or_avoid`: broad market trend or symbol context is hostile to long breakout exposure and must either route to an explicit short-side experiment or block long entries;
- `neutral_blocked`: trend state is mixed, thin, missing, or ambiguous, so the strategy must not claim this period as validated long or short edge.

The first implementation can use simple, deterministic features already present in the backtest context, such as H4/D1 trend slope, higher-timeframe moving-average position, rolling return, volatility bucket, or BTC/ETH proxy trend when available. It must not require private data, order book data, or live market-cap lookup.

Promotion and reporting rules:

- a promoted portfolio scorecard must state which regimes permit long trades and which regimes require short-side research or risk-off blocking;
- per-quarter reports must include PnL, trade count, max drawdown contribution, and skipped/blocked signals by regime;
- a portfolio `8/8` pass is not accepted if profitability depends on mixing bear/short-or-avoid periods into the long bucket without an explicit regime rule;
- if short-side execution is not implemented, bearish regimes are treated as `avoid/risk-off` evidence rather than simulated shorts.

## Approach

1. Generalize the public downloader and batch runner validation from BTCUSDT-only to a fixed `APPROVED_CRYPTO_RESEARCH_SYMBOLS` allowlist.
2. Keep BTCUSDT as the default symbol and preserve existing behavior when no symbol is provided.
3. Ensure `BatchExperimentSummary.symbol` accepts approved symbols and all artifact paths continue to include `crypto/<symbol>/<run_id>`.
4. Add tests proving unsupported symbols fail closed and approved 50-symbol universe members are accepted only in public-data research mode.
5. Implement a portfolio aggregation runner or summary step that merges same-quarter symbol trades into one time-ordered equity curve with `starting_equity=10000`.
6. Add deterministic regime labeling and per-regime reporting before promoting any portfolio profile to full eight-quarter scoring.
7. Run ETHUSDT as a single-symbol data proof, then run fixed 50-symbol universe smoke/early-falsification using the strongest BTCUSDT-derived profile first.
8. Promote only a portfolio profile that passes smoke/blocker checks and has explicit regime rules to the full eight-quarter portfolio scorecard.
9. Stop only on one portfolio profile reaching realistic-cost portfolio `8/8` with buffer and regime reporting; otherwise archive measured negative evidence.

## Risks

- Some symbols may lack complete Bybit public history for all required timeframes/windows; that must be explicit blocked evidence, not a substitution.
- Smaller symbols may have different cost/spread behavior than BTCUSDT; the realistic-cost model remains deliberately conservative and unchanged for comparability.
- Portfolio aggregation can hide unstable contributors, so per-symbol contribution tables are required alongside portfolio success/failure.
- Regime labeling can overfit if it is tuned after seeing the scorecard; labels must use deterministic predeclared features and report bearish/ambiguous periods separately instead of silently optimizing them away.
- A 50-symbol universe can create long runtimes; use deterministic smoke/early-falsification to promote only promising candidates to full quarterly runs.
- Shared cash/exposure logic is easy to get wrong; tests must prove one `10000 USDT` bankroll is used rather than one independent bankroll per symbol.

## Verification

- Strict OpenSpec validation before implementation.
- Targeted tests for approved/unsupported symbols, default BTCUSDT behavior, fixed universe membership, portfolio cash/exposure accounting, and summary serialization.
- Targeted tests for deterministic regime labels and per-regime summary serialization.
- Full relevant pytest after implementation.
- ETHUSDT command pattern:
  `env UV_CACHE_DIR=.uv-cache uv run python -m src.app.breakout.experiments.crypto_batch --preset quarterly-2023-2024 --symbol ETHUSDT --gate-profile <profile> --reuse-market-data --market-data-dir artifacts/batch-market-data --output-dir artifacts/altcoin-universe-profile-comparison/ETHUSDT/<profile>`
- Portfolio command pattern:
  `env UV_CACHE_DIR=.uv-cache uv run python -m src.app.breakout.experiments.crypto_portfolio_batch --preset quarterly-2023-2024 --universe fixed-50-altcoins --starting-equity 10000 --gate-profile <profile> --reuse-market-data --market-data-dir artifacts/batch-market-data --output-dir artifacts/altcoin-universe-portfolio-comparison/<profile>`
- Realistic-cost summary must include unchanged costs, per-symbol contribution reports, and the combined portfolio scorecard.
