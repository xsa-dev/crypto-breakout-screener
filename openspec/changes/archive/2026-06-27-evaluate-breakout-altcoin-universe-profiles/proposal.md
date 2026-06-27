# Proposal

## Why
The current BTCUSDT-only research line has produced useful negative evidence: large-target profiles can create strong net profit and profit factor on `2024q1`, but BTCUSDT repeatedly fails the `min_max_drawdown=-0.35` threshold after realistic costs. The failure mode now appears less like one missing exit tweak and more like a symbol/universe issue: BTCUSDT may be too crowded or too path-risky for this breakout profile under the current risk thresholds.

The next bounded hypothesis is to keep the strategy family and realistic-cost criteria unchanged while testing whether the same breakout/large-target profile family works better as a portfolio across a broader fixed liquid crypto universe. This changes the evaluation unit from one isolated symbol to one shared-bankroll universe portfolio, not the cost model or drawdown discipline.

## What Changes
Implement a research-only altcoin universe capability for the public crypto batch runner and evaluate the strongest locally observed large-target profile family on a fixed allowlist with a shared portfolio bankroll:

- portfolio starting equity: `10000 USDT` for the whole universe, not per symbol;
- primary symbol: `ETHUSDT`;
- fixed liquid altcoin smoke universe of 50 non-BTC symbols:
  `ETHUSDT`, `SOLUSDT`, `BNBUSDT`, `XRPUSDT`, `DOGEUSDT`, `ADAUSDT`, `AVAXUSDT`, `LINKUSDT`, `TRXUSDT`, `TONUSDT`,
  `DOTUSDT`, `NEARUSDT`, `LTCUSDT`, `BCHUSDT`, `UNIUSDT`, `AAVEUSDT`, `APTUSDT`, `ARBUSDT`, `OPUSDT`, `INJUSDT`,
  `SUIUSDT`, `SEIUSDT`, `ATOMUSDT`, `ETCUSDT`, `FILUSDT`, `ICPUSDT`, `IMXUSDT`, `RUNEUSDT`, `HBARUSDT`, `ALGOUSDT`,
  `VETUSDT`, `THETAUSDT`, `FETUSDT`, `GRTUSDT`, `MKRUSDT`, `LDOUSDT`, `STXUSDT`, `JUPUSDT`, `WIFUSDT`, `PEPEUSDT`,
  `SHIBUSDT`, `FLOKIUSDT`, `BONKUSDT`, `ENAUSDT`, `PENDLEUSDT`, `TIAUSDT`, `TAOUSDT`, `WLDUSDT`, `ONDOUSDT`, `JASMYUSDT`;
- reference candidate family:
  - `conservative-v1-m15-slope-positive-max-trades-8-target-4p0-hold-32`
  - `conservative-v1-m15-slope-positive-max-trades-8-target-3p0-hold-32`
  - `conservative-v1-m15-slope-positive-max-trades-8-close-target-2p0-hold-32`

The implementation SHALL:

- preserve BTCUSDT default behavior unless an explicit non-BTCUSDT symbol or universe profile is selected;
- use only public unauthenticated Bybit OHLCV/kline data;
- reject unsupported symbols outside the fixed research allowlist;
- treat missing/unavailable public history as explicit per-symbol negative or blocked evidence, never as a pass;
- keep M15 execution and H1/H4/D1 context datasets;
- run the exact required quarterly windows `2023q1..2024q4` for any candidate portfolio promoted beyond smoke;
- evaluate realistic costs with `spread=1.0`, `slippage_per_unit=0.5`, `commission_rate=0.00055`, and `funding_rate_per_bar=0.00001`;
- size trades from the shared `10000 USDT` portfolio budget with explicit per-trade and total-exposure caps;
- prevent overlapping signals across symbols from implicitly creating leverage beyond the configured portfolio exposure cap;
- classify and report market regimes before promoted portfolio scoring, including where the strategy is allowed to take long breakout exposure, where short or risk-off treatment is required, and where trading must be skipped because the regime is ambiguous;
- report portfolio scorecards by regime bucket so bull/long, bear/short-or-avoid, and neutral/blocked periods are not hidden inside one averaged result;
- treat success as portfolio `8/8` after realistic costs: all eight quarterly portfolio equity curves must pass in money terms with unchanged drawdown discipline;
- record both per-symbol contribution summaries and the combined portfolio equity curve, so individual bad contributors are visible even when portfolio-level diversification helps.

## Success Criteria
- `ETHUSDT` can be downloaded, cached, backtested, and summarized through the existing public-data runner without private credentials.
- The fixed 50-symbol altcoin universe can be smoke-evaluated deterministically with per-symbol artifacts.
- The universe can be evaluated as one portfolio with `starting_equity=10000`, shared cash/exposure accounting, and one combined equity curve per quarter.
- BTCUSDT default tests and behavior remain unchanged.
- Each evaluated symbol records `symbol`, downloaded CSV paths, manifest metadata, per-quarter contribution, realistic-cost settings, and blockers.
- Each promoted portfolio run records deterministic regime labels, the long/short-or-avoid decision for each regime, and per-regime PnL/drawdown contribution.
- A candidate is considered successful only if the shared-bankroll portfolio reaches realistic-cost `8/8` with unchanged thresholds and reports a non-thin safety buffer to the thresholds.
- If no evaluated portfolio reaches `8/8`, archive the change as falsified/negative research evidence and preserve the best per-symbol and portfolio artifacts for the next hypothesis.

## Non-goals
- No live trading, production approval, broker/private API access, private data, order book/DOM/L2/taker-flow, ML, broad optimization, push, MR, merge, or cloud delivery.
- No dynamic market-cap scraping inside the deterministic runner.
- No automatic substitution of unavailable symbols with unlisted alternatives during a run.
- No independent per-symbol deposits, hidden leverage, weakening thresholds, skipping required quarters, or counting a portfolio pass without per-symbol contribution audit.
