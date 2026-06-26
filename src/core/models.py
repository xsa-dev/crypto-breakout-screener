"""Pydantic DTOs for the breakout strategy foundation."""

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from src.core.enums import (
    EntryMode,
    FsmState,
    LevelType,
    OperationMode,
    RiskRejectionReason,
    ScenarioType,
    Side,
    TimeFrame,
)


class LevelDetectionConfig(BaseModel):
    """Configuration for level detection."""

    pivot_left_bars: int = Field(default=3, ge=1)
    pivot_right_bars: int = Field(default=3, ge=1)
    min_touches: int = Field(default=2, ge=1)
    recent_break_lookback_bars: int = Field(default=96, ge=1)
    touch_tolerance_atr: float = Field(default=0.10, ge=0)
    min_reaction_atr: float = Field(default=1.0, ge=0)
    round_step: dict[str, float] = Field(default_factory=dict)
    cascade_min_count: int = Field(default=2, ge=2)
    cascade_gap_atr: float = Field(default=0.80, ge=0)


class SetupConfig(BaseModel):
    """Configuration for setup scoring."""

    atr_period: int = Field(default=14, ge=1)
    consolidation_bars: int = Field(default=8, ge=2)
    consolidation_max_range_atr: float = Field(default=1.20, gt=0)
    slow_approach_max_velocity: float = Field(default=0.35, ge=0)
    protorgovka_range_percent: tuple[float, float] = Field(default=(0.3, 2.0))

    @field_validator("protorgovka_range_percent")
    @classmethod
    def validate_protorgovka_range(cls, value: tuple[float, float]) -> tuple[float, float]:
        lower, upper = value
        if lower < 0 or upper <= lower:
            msg = "protorgovka_range_percent must be a positive increasing range"
            raise ValueError(msg)
        return value


class TrendFilterConfig(BaseModel):
    """Configuration for trend filters."""

    enabled: bool = True
    ema_fast: int = Field(default=50, ge=1)
    ema_slow: int = Field(default=200, ge=1)
    adx_period: int = Field(default=14, ge=1)
    adx_threshold: float = Field(default=25.0, ge=0)

    @model_validator(mode="after")
    def validate_ema_order(self) -> "TrendFilterConfig":
        if self.ema_fast >= self.ema_slow:
            msg = "ema_fast must be lower than ema_slow"
            raise ValueError(msg)
        return self


class ContextFilterConfig(BaseModel):
    """Configuration for local setup context filters."""

    enabled: bool = True
    hard_block_threshold: float = Field(default=0.80, ge=0, le=1)
    full_strength_penalty: int = Field(default=20, ge=0, le=100)


class ContextDriverSignal(BaseModel):
    """Deterministic upstream context-driver opposition signal."""

    name: str = Field(min_length=1)
    opposes_side: Side
    strength: float = Field(ge=0, le=1)
    reason: str | None = None


class ScoreConfig(BaseModel):
    """Configuration for breakout score weighting."""

    threshold_normal: int = Field(default=70, ge=0, le=100)
    threshold_reduced: int = Field(default=50, ge=0, le=100)
    weight_consolidation: int = Field(default=20, ge=0, le=100)
    weight_slow_approach: int = Field(default=20, ge=0, le=100)
    weight_trend: int = Field(default=20, ge=0, le=100)
    weight_activity: int = Field(default=20, ge=0, le=100)
    weight_density: int = Field(default=20, ge=0, le=100)

    @model_validator(mode="after")
    def validate_thresholds(self) -> "ScoreConfig":
        if self.threshold_reduced >= self.threshold_normal:
            msg = "threshold_reduced must be lower than threshold_normal"
            raise ValueError(msg)
        return self


class EntryConfig(BaseModel):
    """Configuration for entry shares and buffers."""

    pre_entry_share: float = Field(default=0.30, gt=0, lt=1)
    at_level_share: float = Field(default=0.30, gt=0, lt=1)
    post_breakout_share: float = Field(default=0.40, gt=0, lt=1)
    breakout_buffer_atr: float = Field(default=0.05, ge=0)
    lower_protorgovka_entry_enabled: bool = False

    @model_validator(mode="after")
    def validate_total_share(self) -> "EntryConfig":
        total = self.pre_entry_share + self.at_level_share + self.post_breakout_share
        if abs(total - 1.0) > 1e-9:
            msg = "entry shares must sum to 1.0"
            raise ValueError(msg)
        return self


class BreakoutStrategyConfig(BaseModel):
    """Baseline configuration for the breakout foundation."""

    strategy_name: str = "breakout_retest_v1"
    mode: OperationMode = OperationMode.SEMI_AUTO
    full_auto_contract_validation_only: bool = False
    symbols: list[str] = Field(default_factory=lambda: ["EURUSD", "XAUUSD", "BTCUSDT"])
    execution_timeframe: TimeFrame = TimeFrame.M15
    context_timeframes: list[TimeFrame] = Field(
        default_factory=lambda: [TimeFrame.H1, TimeFrame.H4, TimeFrame.D1]
    )
    level_detection: LevelDetectionConfig = Field(default_factory=LevelDetectionConfig)
    setup: SetupConfig = Field(default_factory=SetupConfig)
    trend_filter: TrendFilterConfig = Field(default_factory=TrendFilterConfig)
    context_filter: ContextFilterConfig = Field(default_factory=ContextFilterConfig)
    score: ScoreConfig = Field(default_factory=ScoreConfig)
    entries: EntryConfig = Field(default_factory=EntryConfig)
    fast_exit_for_low_breakouts: bool = False

    @model_validator(mode="after")
    def validate_full_auto_guard(self) -> "BreakoutStrategyConfig":
        if self.mode is OperationMode.FULL_AUTO and not self.full_auto_contract_validation_only:
            msg = (
                "full_auto mode requires a dedicated full-auto OpenSpec change "
                "before production activation"
            )
            raise ValueError(msg)
        return self


class Level(BaseModel):
    """Detected and auditable market level."""

    level_id: str
    symbol: str
    type: LevelType
    price: float
    timeframe: TimeFrame
    touches: int = Field(default=1, ge=1)
    created_at: datetime
    source_indexes: list[int] = Field(default_factory=list)
    metadata: dict[str, float | int | str | bool] = Field(default_factory=dict)
    invalidated_at: datetime | None = None
    invalidation_reason: str | None = None


class FeatureVector(BaseModel):
    """Calculated setup feature vector."""

    symbol: str
    timestamp: datetime
    atr: float = Field(ge=0)
    ema_fast: float | None = None
    ema_slow: float | None = None
    adx: float | None = Field(default=None, ge=0)
    consolidation_range_atr: float | None = Field(default=None, ge=0)
    approach_velocity: float | None = Field(default=None, ge=0)
    activity_ratio: float | None = Field(default=None, ge=0)
    density_available: bool = False
    density_supports_breakout: bool | None = None


class BreakoutScore(BaseModel):
    """Factor scores and resulting eligibility."""

    symbol: str
    side: Side
    scenario: ScenarioType
    total: int = Field(ge=0, le=100)
    consolidation: int = Field(ge=0, le=100)
    slow_approach: int = Field(ge=0, le=100)
    trend: int = Field(ge=0, le=100)
    activity: int = Field(ge=0, le=100)
    density: int = Field(ge=0, le=100)
    eligibility: Literal["normal", "reduced", "blocked"]
    rejection_reasons: list[str] = Field(default_factory=list)


class MarketSnapshot(BaseModel):
    """Minimal market state used by deterministic entry/risk tests."""

    symbol: str
    timestamp: datetime
    price: float
    close: float
    high: float
    low: float
    bars_since_breakout: int = Field(default=0, ge=0)
    micro_impulse: bool = False


class TradeIntent(BaseModel):
    """Broker-neutral trade or add-on intent created before execution."""

    intent_id: str
    symbol: str
    side: Side
    mode: EntryMode
    entry_price: float
    stop_price: float
    quantity: float = Field(gt=0)
    score: BreakoutScore
    is_addon: bool = False
    metadata: dict[str, float | int | str | bool] = Field(default_factory=dict)


class DensitySupportPlan(BaseModel):
    """Deterministic local plan for density-backed trade support."""

    symbol: str
    side: Side
    density_reference: float
    stop_price: float
    affected_quantity: float = Field(gt=0)
    remaining_base_quantity: float = Field(ge=0)
    stop_placement_rule: str = "behind_density"
    exit_on_density_eating_rule: Literal["reduce_affected_quantity"] = "reduce_affected_quantity"
    metadata: dict[str, float | int | str | bool] = Field(default_factory=dict)


class DensityInvalidationDecision(BaseModel):
    """Local density invalidation/reset decision with no broker side effects."""

    action: Literal["hold", "reduce_affected_quantity"]
    reason: Literal["density_still_valid", "density_eaten"]
    affected_quantity: float = Field(ge=0)
    remaining_base_quantity: float = Field(ge=0)
    metadata: dict[str, float | int | str | bool] = Field(default_factory=dict)


class AddonRollbackDecision(BaseModel):
    """Local add-on rollback/reset decision with no broker side effects."""

    action: Literal["hold", "reduce_added_quantity"]
    reason: Literal["addon_level_intact", "addon_level_rollback"]
    affected_quantity: float = Field(ge=0)
    remaining_base_quantity: float = Field(ge=0)
    metadata: dict[str, float | int | str | bool] = Field(default_factory=dict)


class RiskLimits(BaseModel):
    """Configurable local risk limits for deterministic approval tests."""

    equity: float = Field(default=10_000.0, gt=0)
    risk_pct: float = Field(default=0.01, gt=0, le=1)
    contract_multiplier: float = Field(default=1.0, gt=0)
    min_stop_distance: float = Field(default=1e-9, gt=0)
    max_daily_loss: float = Field(default=1_000.0, gt=0)
    max_open_positions: int = Field(default=3, ge=0)
    max_total_risk_pct: float = Field(default=0.02, gt=0, le=1)
    addon_min_share: float = Field(default=0.10, gt=0, lt=1)
    addon_max_share: float = Field(default=0.20, gt=0, lt=1)
    max_addons: int = Field(default=2, ge=0)
    degrade_avg_price_limit_atr: float = Field(default=1.0, ge=0)
    density_stop_buffer: float = Field(default=0.0, ge=0)


class RiskState(BaseModel):
    """Runtime risk counters supplied to the risk manager."""

    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0
    open_positions: int = 0
    open_risk: float = 0.0
    addon_count: int = 0
    feed_degraded: bool = False
    broker_state_mismatch: bool = False
    config_invalid: bool = False
    degraded_reasons: list[str] = Field(default_factory=list)
    context_filter_blocked: bool = False


class RiskDecision(BaseModel):
    """Risk approval or rejection result."""

    approved: bool
    quantity: float = 0.0
    reason: RiskRejectionReason | None = None
    planned_risk: float = 0.0
    metadata: dict[str, str | int | float | bool | list[str]] = Field(default_factory=dict)


class HealthCheck(BaseModel):
    """Single local health check result used for degraded-mode decisions."""

    name: str
    status: Literal["healthy", "degraded"] = "healthy"
    reason: str | None = None
    details: dict[str, str | int | float | bool] = Field(default_factory=dict)


class HealthReport(BaseModel):
    """Aggregated local health report with machine-readable degraded reasons."""

    status: Literal["healthy", "degraded"] = "healthy"
    checks: list[HealthCheck] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(tz=UTC))

    @property
    def degraded_reasons(self) -> list[str]:
        return [check.reason for check in self.checks if check.status == "degraded" and check.reason]


class PositionState(BaseModel):
    """Local broker-neutral position snapshot."""

    symbol: str
    side: Side
    quantity: float = Field(ge=0)
    average_price: float


class ExecutionRequest(BaseModel):
    """Idempotent fake execution order request."""

    request_id: str
    intent_id: str
    symbol: str
    side: Side
    quantity: float = Field(gt=0)
    price: float


class ExecutionOrder(BaseModel):
    """Recorded fake order lifecycle."""

    order_id: str
    request_id: str
    intent_id: str
    symbol: str
    side: Side
    quantity: float
    price: float
    filled_quantity: float = 0.0
    fill_price: float | None = None
    status: str = "accepted"


class ExecutionSnapshot(BaseModel):
    """Fake adapter reconciliation snapshot."""

    orders: dict[str, ExecutionOrder] = Field(default_factory=dict)
    positions: dict[str, PositionState] = Field(default_factory=dict)


class LifecycleTransition(BaseModel):
    """Auditable finite-state-machine transition."""

    from_state: FsmState
    to_state: FsmState
    reason: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(tz=UTC))


class ExitPlan(BaseModel):
    """Deterministic local exit framework for a planned position."""

    fast_exit: bool = False
    reason: str
    quantities: dict[str, float]


class BacktestCostModel(BaseModel):
    """Explicit local trading-cost assumptions for acceptance-quality backtests."""

    spread: float = Field(default=0.0, ge=0)
    commission_per_unit: float = Field(default=0.0, ge=0)
    slippage_per_unit: float = Field(default=0.0, ge=0)
    funding_per_bar: float = Field(default=0.0, ge=0)
    acceptance_quality: bool = True


class BacktestResearchGateConfig(BaseModel):
    """Disabled-by-default local research gates for backtest overtrading diagnostics."""

    min_entry_score: int | None = Field(default=None, ge=0, le=100)
    cooldown_bars_after_trade: int = Field(default=0, ge=0)
    cooldown_bars_after_loss: int = Field(default=0, ge=0)
    block_immediate_reentry: bool = False
    max_trades_per_day: int | None = Field(default=None, ge=1)
    daily_stop_loss: float | None = Field(default=None, gt=0)


class BacktestFeatureFilterConfig(BaseModel):
    """Disabled-by-default local research filters for feature-profile comparisons."""

    require_m15_ema_slope_positive: bool = False
    require_h1_trend_long: bool = False
    min_atr_percentile: float | None = Field(default=None, ge=0, le=1)
    max_breakout_distance_atr: float | None = Field(default=None, gt=0)
    min_candle_body_ratio: float | None = Field(default=None, ge=0)
    max_candle_body_ratio: float | None = Field(default=None, gt=0)

    @property
    def configured(self) -> bool:
        return bool(
            self.require_m15_ema_slope_positive
            or self.require_h1_trend_long
            or self.min_atr_percentile is not None
            or self.max_breakout_distance_atr is not None
            or self.min_candle_body_ratio is not None
            or self.max_candle_body_ratio is not None
        )

    @model_validator(mode="after")
    def validate_candle_body_bounds(self) -> "BacktestFeatureFilterConfig":
        if (
            self.min_candle_body_ratio is not None
            and self.max_candle_body_ratio is not None
            and self.min_candle_body_ratio >= self.max_candle_body_ratio
        ):
            msg = "min_candle_body_ratio must be below max_candle_body_ratio"
            raise ValueError(msg)
        return self


class BacktestConfirmationFilterConfig(BaseModel):
    """Disabled-by-default local research filters for false-breakout confirmation."""

    required_closes_above_breakout: int = Field(default=0, ge=0, le=2)
    min_close_position: float | None = Field(default=None, ge=0, le=1)
    cancel_on_return_inside_range: bool = False

    @property
    def configured(self) -> bool:
        return bool(
            self.required_closes_above_breakout > 0
            or self.min_close_position is not None
            or self.cancel_on_return_inside_range
        )

    @model_validator(mode="after")
    def validate_confirmation_requirements(self) -> "BacktestConfirmationFilterConfig":
        if self.min_close_position is not None and self.required_closes_above_breakout < 1:
            msg = "min_close_position requires at least one confirmation close"
            raise ValueError(msg)
        if self.cancel_on_return_inside_range and self.required_closes_above_breakout < 1:
            msg = "cancel_on_return_inside_range requires at least one confirmation close"
            raise ValueError(msg)
        return self


class BacktestExitProfileConfig(BaseModel):
    """Disabled-by-default local research exit profiles."""

    fixed_holding_bars: int = Field(default=1, ge=1, le=16)
    stop_atr: float | None = Field(default=None, gt=0)
    target_atr: float | None = Field(default=None, gt=0)

    @property
    def configured(self) -> bool:
        return self.fixed_holding_bars != 1 or self.stop_atr is not None or self.target_atr is not None

    @model_validator(mode="after")
    def validate_exit_profile(self) -> "BacktestExitProfileConfig":
        if (self.stop_atr is None) != (self.target_atr is None):
            msg = "stop_atr and target_atr must be configured together"
            raise ValueError(msg)
        return self


class BacktestConfig(BaseModel):
    """Deterministic local backtest configuration."""

    initial_equity: float = Field(default=10_000.0, gt=0)
    base_quantity: float = Field(default=1.0, gt=0)
    stop_distance: float = Field(default=1.0, gt=0)
    min_warmup_bars: int = Field(default=20, ge=1)
    random_seed: int = 0
    cost_model: BacktestCostModel = Field(default_factory=BacktestCostModel)
    research_gates: BacktestResearchGateConfig = Field(default_factory=BacktestResearchGateConfig)
    feature_filters: BacktestFeatureFilterConfig = Field(default_factory=BacktestFeatureFilterConfig)
    confirmation_filters: BacktestConfirmationFilterConfig = Field(
        default_factory=BacktestConfirmationFilterConfig
    )
    exit_profile: BacktestExitProfileConfig = Field(default_factory=BacktestExitProfileConfig)
    strategy: BreakoutStrategyConfig = Field(default_factory=BreakoutStrategyConfig)
    export_parquet: bool = False
    forward_path_diagnostics: bool = False
    forward_path_horizons: tuple[int, ...] = (1, 2, 4, 8, 16)
    path_risk_diagnostics: bool = False
    path_risk_favorable_atr_thresholds: tuple[float, ...] = (0.5, 1.0, 1.5, 2.0)
    path_risk_adverse_atr_thresholds: tuple[float, ...] = (0.5, 1.0, 1.5, 2.0)
    path_risk_trailing_giveback_atr: tuple[float, ...] = (0.5, 1.0)

    @model_validator(mode="after")
    def validate_acceptance_costs(self) -> "BacktestConfig":
        if self.cost_model.acceptance_quality and (
            self.cost_model.spread <= 0
            and self.cost_model.commission_per_unit <= 0
            and self.cost_model.slippage_per_unit <= 0
            and self.cost_model.funding_per_bar <= 0
        ):
            msg = "acceptance-quality backtests require explicit non-zero cost assumptions"
            raise ValueError(msg)
        return self

    @model_validator(mode="after")
    def validate_forward_path_horizons(self) -> "BacktestConfig":
        if not self.forward_path_horizons:
            msg = "forward_path_horizons must not be empty"
            raise ValueError(msg)
        if any(horizon <= 0 for horizon in self.forward_path_horizons):
            msg = "forward_path_horizons must contain positive integers"
            raise ValueError(msg)
        if tuple(sorted(set(self.forward_path_horizons))) != self.forward_path_horizons:
            msg = "forward_path_horizons must be unique and sorted ascending"
            raise ValueError(msg)
        return self

    @model_validator(mode="after")
    def validate_path_risk_thresholds(self) -> "BacktestConfig":
        for name, values in (
            ("path_risk_favorable_atr_thresholds", self.path_risk_favorable_atr_thresholds),
            ("path_risk_adverse_atr_thresholds", self.path_risk_adverse_atr_thresholds),
            ("path_risk_trailing_giveback_atr", self.path_risk_trailing_giveback_atr),
        ):
            if not values:
                msg = f"{name} must not be empty"
                raise ValueError(msg)
            if any(value <= 0 for value in values):
                msg = f"{name} must contain positive values"
                raise ValueError(msg)
            if tuple(sorted(set(values))) != values:
                msg = f"{name} must be unique and sorted ascending"
                raise ValueError(msg)
        return self


class BacktestTrade(BaseModel):
    """Single deterministic simulated trade."""

    trade_id: str
    symbol: str
    side: Side
    entry_time: datetime
    exit_time: datetime
    entry_price: float
    exit_price: float
    quantity: float
    gross_pnl: float
    total_cost: float
    net_pnl: float
    holding_bars: int
    scenario: ScenarioType
    score: int
    slippage: float
    metadata: dict[str, float | int | str | bool] = Field(default_factory=dict)


class BacktestWindow(BaseModel):
    """Named contiguous validation window."""

    name: str
    start_index: int
    end_index: int
    role: Literal["is", "oos", "train", "validate", "forward"]


class MonteCarloResult(BaseModel):
    """Seeded local Monte Carlo robustness summary."""

    seed: int
    iterations: int
    method: str
    median_net_pnl: float
    worst_net_pnl: float
    best_net_pnl: float


class ProductionOosThresholds(BaseModel):
    """Explicit local production OOS/business-validity thresholds."""

    min_oos_performance: float | None = None
    max_drawdown_floor: float | None = None
    min_win_rate: float | None = Field(default=None, ge=0, le=1)
    min_profit_factor: float | None = Field(default=None, ge=0)
    min_trade_count: int | None = Field(default=None, ge=1)

    @property
    def configured(self) -> bool:
        return any(
            value is not None
            for value in (
                self.min_oos_performance,
                self.max_drawdown_floor,
                self.min_win_rate,
                self.min_profit_factor,
                self.min_trade_count,
            )
        )


class ProductionOosMetricCheck(BaseModel):
    """Auditable comparison of one backtest metric against one threshold."""

    metric: Literal[
        "oos_performance",
        "max_drawdown",
        "win_rate",
        "profit_factor",
        "trade_count",
    ]
    actual: float
    threshold: float
    operator: Literal["gte"] = "gte"
    passed: bool


class ProductionOosGateDecision(BaseModel):
    """Fail-closed local decision for production OOS/business-validity review."""

    approved: bool
    reason: Literal[
        "approved",
        "missing_oos_thresholds",
        "oos_metric_missing",
        "oos_metric_unavailable",
        "oos_threshold_failed",
    ]
    checked_metrics: list[ProductionOosMetricCheck] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)


class BacktestReport(BaseModel):
    """Reproducible backtest report artifact manifest and payload."""

    run_id: str
    config_hash: str
    dataset_hash: str
    time_range: tuple[datetime, datetime]
    parameter_snapshot: dict[str, object]
    metrics: dict[str, float | int | str | None]
    unavailable_reasons: dict[str, str] = Field(default_factory=dict)
    equity_curve: list[dict[str, float | str]] = Field(default_factory=list)
    drawdown_curve: list[dict[str, float | str]] = Field(default_factory=list)
    return_distribution: list[float] = Field(default_factory=list)
    trades: list[BacktestTrade] = Field(default_factory=list)
    scenario_breakdown: dict[str, int] = Field(default_factory=dict)
    score_distribution: dict[str, int] = Field(default_factory=dict)
    false_breakout_analysis: dict[str, int] = Field(default_factory=dict)
    slippage_report: dict[str, float] = Field(default_factory=dict)
    windows: list[BacktestWindow] = Field(default_factory=list)
    monte_carlo: MonteCarloResult | None = None
    forward_path_diagnostics: list[dict[str, object]] = Field(default_factory=list)
    holding_horizon_diagnostics: list[dict[str, object]] = Field(default_factory=list)
    path_risk_diagnostics: list[dict[str, object]] = Field(default_factory=list)
    path_risk_threshold_summary: list[dict[str, object]] = Field(default_factory=list)
    artifact_paths: list[str] = Field(default_factory=list)
