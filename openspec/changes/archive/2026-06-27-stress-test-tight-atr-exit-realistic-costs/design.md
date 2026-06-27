# Design

## Cost Model Extension
Extend `BacktestCostModel` with optional notional rates:

- `commission_rate`: non-negative fraction of notional per side. Example: `0.00055` means `0.055%` per side.
- `funding_rate_per_bar`: signed or non-negative fraction of notional per holding bar. For conservative stress, use a positive cost for long positions.

The current per-unit fields remain unchanged:

- `spread`
- `commission_per_unit`
- `slippage_per_unit`
- `funding_per_bar`

Backtest trade cost calculation SHALL include both legacy per-unit costs and notional costs:

- entry notional: `entry_price * quantity`
- exit notional: `exit_price * quantity`
- notional commission: `(entry_notional + exit_notional) * commission_rate`
- notional funding: `entry_notional * funding_rate_per_bar * holding_bars`

Default values for new notional fields SHALL be zero to preserve existing deterministic outputs.

## Batch Runner Stress Inputs
Add CLI and function-level cost parameters to the BTCUSDT batch runner:

- `--spread`
- `--slippage`
- `--commission-per-unit`
- `--funding-per-bar`
- `--commission-rate`
- `--funding-rate-per-bar`

These values SHALL be passed into `run_crypto_experiment`.

The batch runner also supports `--reuse-market-data` for deterministic local
stress reruns against already downloaded Bybit CSV files. This avoids treating
network/DNS availability as part of the hypothesis result.

## Reporting
Every batch summary SHALL include cost model settings at the summary level and in each window row so stress artifacts are self-describing. CSV SHALL include a deterministic `cost_model_settings_json` field.

If exact quarterly reruns are too slow for an interactive verification loop,
ledger-level additive stress may be recorded as negative robustness evidence.
Ledger-level stress preserves the original entries/exits and subtracts explicit
additional costs from each realized trade; it must be labelled separately from
an exact signal rerun because cost-dependent gates can change later trades.

## Stress Scenarios
Run the discovered profile with at least these local research stress scenarios:

- baseline compatibility: existing defaults plus zero notional rates;
- realistic taker-fee assumption: non-zero notional commission rate;
- stressed execution: increased spread/slippage plus non-zero notional commission;
- stressed execution plus funding: increased spread/slippage, non-zero commission rate, and non-zero funding rate per M15 bar.

Do not claim that these are exact current exchange fees; they are explicit robustness assumptions for local research.

## Risk Interpretation
If the profile fails under realistic cost scenarios, the correct conclusion is that the original `8/8` is execution-cost sensitive. If it passes, the correct conclusion is improved robustness evidence, not production approval.
