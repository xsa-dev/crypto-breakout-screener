"""Setup scoring for the breakout strategy foundation."""

from typing import Literal

from src.core.enums import ScenarioType, Side
from src.core.models import BreakoutScore, FeatureVector, ScoreConfig

Eligibility = Literal["normal", "reduced", "blocked"]


class SetupEvaluator:
    """Calculates deterministic breakout setup scores from feature vectors."""

    def __init__(self, config: ScoreConfig | None = None) -> None:
        self.config = config or ScoreConfig()

    def score(
        self,
        features: FeatureVector,
        *,
        side: Side = Side.LONG,
        scenario: ScenarioType = ScenarioType.CONSOLIDATION_BREAKOUT,
    ) -> BreakoutScore:
        """Calculate weighted 0-100 breakout score."""

        consolidation = self._score_consolidation(features)
        slow_approach = self._score_slow_approach(features)
        trend = self._score_trend(features, side=side)
        activity = self._score_activity(features)
        density = self._score_density(features)
        total = consolidation + slow_approach + trend + activity + density

        return BreakoutScore(
            symbol=features.symbol,
            side=side,
            scenario=scenario,
            total=total,
            consolidation=consolidation,
            slow_approach=slow_approach,
            trend=trend,
            activity=activity,
            density=density,
            eligibility=self.eligibility(total),
        )

    def eligibility(self, total: int) -> Eligibility:
        """Return baseline eligibility bucket for a score."""

        if total >= self.config.threshold_normal:
            return "normal"
        if total >= self.config.threshold_reduced:
            return "reduced"
        return "blocked"

    def _score_consolidation(self, features: FeatureVector) -> int:
        if features.consolidation_range_atr is None:
            return 0
        if features.consolidation_range_atr <= 1.2:
            return self.config.weight_consolidation
        if features.consolidation_range_atr <= 2.0:
            return self.config.weight_consolidation // 2
        return 0

    def _score_slow_approach(self, features: FeatureVector) -> int:
        if features.approach_velocity is None:
            return 0
        if features.approach_velocity <= 0.35:
            return self.config.weight_slow_approach
        if features.approach_velocity <= 0.70:
            return self.config.weight_slow_approach // 2
        return 0

    def _score_trend(self, features: FeatureVector, *, side: Side) -> int:
        if features.ema_fast is None or features.ema_slow is None:
            return 0

        long_ok = features.ema_fast > features.ema_slow
        short_ok = features.ema_fast < features.ema_slow
        side_ok = long_ok if side is Side.LONG else short_ok
        adx_ok = features.adx is None or features.adx >= 25.0
        return self.config.weight_trend if side_ok and adx_ok else 0

    def _score_activity(self, features: FeatureVector) -> int:
        if features.activity_ratio is None:
            return 0
        if features.activity_ratio >= 1.2:
            return self.config.weight_activity
        if features.activity_ratio >= 1.0:
            return self.config.weight_activity // 2
        return 0

    def _score_density(self, features: FeatureVector) -> int:
        if not features.density_available:
            return 0
        return self.config.weight_density if features.density_supports_breakout else 0
