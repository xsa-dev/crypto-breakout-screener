"""Pydantic DTOs for the breakout strategy foundation."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from src.core.enums import LevelType, OperationMode, ScenarioType, Side, TimeFrame


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
    symbols: list[str] = Field(default_factory=lambda: ["EURUSD", "XAUUSD", "BTCUSDT"])
    execution_timeframe: TimeFrame = TimeFrame.M15
    context_timeframes: list[TimeFrame] = Field(
        default_factory=lambda: [TimeFrame.H1, TimeFrame.H4, TimeFrame.D1]
    )
    level_detection: LevelDetectionConfig = Field(default_factory=LevelDetectionConfig)
    setup: SetupConfig = Field(default_factory=SetupConfig)
    trend_filter: TrendFilterConfig = Field(default_factory=TrendFilterConfig)
    score: ScoreConfig = Field(default_factory=ScoreConfig)
    entries: EntryConfig = Field(default_factory=EntryConfig)


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
