"""Blocking risk manager for broker-neutral breakout intents."""

from src.core.enums import RiskRejectionReason, Side
from src.core.models import (
    DensityInvalidationDecision,
    DensitySupportPlan,
    PositionState,
    RiskDecision,
    RiskLimits,
    RiskState,
    TradeIntent,
)


class RiskManager:
    """Approves or rejects entry/add-on intents before execution."""

    def __init__(self, limits: RiskLimits | None = None) -> None:
        self.limits = limits or RiskLimits()

    def evaluate(
        self,
        intent: TradeIntent,
        state: RiskState,
        *,
        position: PositionState | None = None,
        atr: float | None = None,
    ) -> RiskDecision:
        """Return a blocking approval decision and sized quantity for an intent."""

        if intent.score.eligibility == "blocked":
            return self._reject(RiskRejectionReason.SCORE_TOO_LOW)
        if state.context_filter_blocked:
            return self._reject(RiskRejectionReason.CONTEXT_FILTER_BLOCKED)
        if state.realized_pnl + state.unrealized_pnl <= -self.limits.max_daily_loss:
            return self._reject(RiskRejectionReason.DAILY_LOSS_LIMIT)
        if state.open_positions >= self.limits.max_open_positions:
            return self._reject(RiskRejectionReason.MAX_POSITIONS)
        if state.feed_degraded:
            return self._reject(RiskRejectionReason.FEED_DEGRADED, state.degraded_reasons)
        if state.broker_state_mismatch:
            return self._reject(RiskRejectionReason.BROKER_STATE_MISMATCH, state.degraded_reasons)
        if state.config_invalid:
            return self._reject(RiskRejectionReason.CONFIG_INVALID, state.degraded_reasons)
        if state.degraded_reasons:
            return self._reject(RiskRejectionReason.HEALTH_DEGRADED, state.degraded_reasons)

        stop_distance = abs(intent.entry_price - intent.stop_price)
        if stop_distance <= self.limits.min_stop_distance:
            return self._reject(RiskRejectionReason.INVALID_STOP_DISTANCE)

        planned_risk = intent.quantity * stop_distance * self.limits.contract_multiplier
        if intent.is_addon:
            addon_rejection = self._evaluate_addon(intent, state, position, atr, planned_risk)
            if addon_rejection is not None:
                return self._reject(addon_rejection)
            return RiskDecision(approved=True, quantity=intent.quantity, planned_risk=planned_risk)

        max_risk = self.limits.equity * self.limits.risk_pct
        quantity = min(intent.quantity, max_risk / (stop_distance * self.limits.contract_multiplier))
        return RiskDecision(
            approved=True,
            quantity=quantity,
            planned_risk=quantity * stop_distance * self.limits.contract_multiplier,
        )

    def plan_density_support(
        self,
        *,
        symbol: str,
        side: Side,
        density_reference: float,
        affected_quantity: float,
        base_position: PositionState,
    ) -> DensitySupportPlan:
        """Plan side-symmetric density-backed support and stop behavior locally."""

        if side is Side.LONG:
            stop_price = density_reference - self.limits.density_stop_buffer
        else:
            stop_price = density_reference + self.limits.density_stop_buffer
        remaining_base_quantity = max(0.0, base_position.quantity - affected_quantity)
        return DensitySupportPlan(
            symbol=symbol,
            side=side,
            density_reference=density_reference,
            stop_price=stop_price,
            affected_quantity=affected_quantity,
            remaining_base_quantity=remaining_base_quantity,
            metadata={
                "density_reference": density_reference,
                "base_quantity": base_position.quantity,
                "base_average_price": base_position.average_price,
            },
        )

    def evaluate_density_invalidation(
        self,
        plan: DensitySupportPlan,
        *,
        density_eaten: bool,
    ) -> DensityInvalidationDecision:
        """Return a deterministic local decision when density support is eaten."""

        if not density_eaten:
            return DensityInvalidationDecision(
                action="hold",
                reason="density_still_valid",
                affected_quantity=0.0,
                remaining_base_quantity=plan.remaining_base_quantity + plan.affected_quantity,
                metadata={
                    "density_reference": plan.density_reference,
                    "stop_price": plan.stop_price,
                },
            )
        return DensityInvalidationDecision(
            action=plan.exit_on_density_eating_rule,
            reason="density_eaten",
            affected_quantity=plan.affected_quantity,
            remaining_base_quantity=plan.remaining_base_quantity,
            metadata={
                "density_reference": plan.density_reference,
                "stop_price": plan.stop_price,
                "stop_placement_rule": plan.stop_placement_rule,
            },
        )

    def _evaluate_addon(
        self,
        intent: TradeIntent,
        state: RiskState,
        position: PositionState | None,
        atr: float | None,
        planned_risk: float,
    ) -> RiskRejectionReason | None:
        if position is None or position.quantity <= 0:
            return RiskRejectionReason.INSUFFICIENT_RISK_BUDGET
        if state.addon_count >= self.limits.max_addons:
            return RiskRejectionReason.INSUFFICIENT_RISK_BUDGET

        share = intent.quantity / position.quantity
        if share < self.limits.addon_min_share or share > self.limits.addon_max_share:
            return RiskRejectionReason.INSUFFICIENT_RISK_BUDGET

        max_total_risk = self.limits.equity * self.limits.max_total_risk_pct
        if state.open_risk + planned_risk > max_total_risk:
            return RiskRejectionReason.INSUFFICIENT_RISK_BUDGET

        if atr is not None and atr > 0:
            new_average = self._average_after_addon(intent, position)
            degradation = self._average_degradation(intent.side, position.average_price, new_average)
            if degradation > self.limits.degrade_avg_price_limit_atr * atr:
                return RiskRejectionReason.ADDON_DEGRADES_AVERAGE
        return None

    def _average_after_addon(self, intent: TradeIntent, position: PositionState) -> float:
        total_quantity = position.quantity + intent.quantity
        return (position.average_price * position.quantity + intent.entry_price * intent.quantity) / total_quantity

    def _average_degradation(self, side: Side, old_average: float, new_average: float) -> float:
        if side is Side.LONG:
            return max(0.0, new_average - old_average)
        return max(0.0, old_average - new_average)

    def _reject(
        self,
        reason: RiskRejectionReason,
        degraded_reasons: list[str] | None = None,
    ) -> RiskDecision:
        metadata: dict[str, str | int | float | bool | list[str]] = (
            {"degraded_reasons": degraded_reasons} if degraded_reasons else {}
        )
        return RiskDecision(approved=False, reason=reason, metadata=metadata)
