"""Local health and degraded-mode checks for breakout runtime safety."""

from datetime import UTC, datetime, timedelta
from typing import Iterable

from pydantic import BaseModel, Field

from src.app.breakout.execution import FakeExecutionAdapter
from src.core.models import (
    ExecutionSnapshot,
    HealthCheck,
    HealthReport,
    MarketSnapshot,
    RiskLimits,
    RiskState,
)


class HealthMonitor(BaseModel):
    """Build local health reports and risk-state degraded flags.

    The monitor is intentionally broker-neutral and local-only: it inspects the
    in-process market snapshot, configuration validation messages, fake adapter
    reconciliation state, and current risk counters. It does not call external
    monitoring systems or live broker APIs.
    """

    max_market_data_age_seconds: int = Field(default=120, gt=0)

    def check(
        self,
        *,
        now: datetime,
        market: MarketSnapshot | None = None,
        config_errors: Iterable[str] = (),
        adapter: FakeExecutionAdapter | None = None,
        expected_snapshot: ExecutionSnapshot | None = None,
        risk_state: RiskState | None = None,
        risk_limits: RiskLimits | None = None,
    ) -> HealthReport:
        """Return a deterministic health report with explicit degraded reasons."""

        checks: list[HealthCheck] = []
        checks.append(self._market_data_check(now=now, market=market))
        checks.append(self._config_check(config_errors=config_errors))
        checks.append(self._broker_state_check(adapter=adapter, expected_snapshot=expected_snapshot))
        checks.append(self._risk_stop_check(state=risk_state, limits=risk_limits))
        return HealthReport(
            status="degraded" if any(check.status == "degraded" for check in checks) else "healthy",
            checks=checks,
            generated_at=now,
        )

    def risk_state_from_report(self, report: HealthReport, base: RiskState | None = None) -> RiskState:
        """Merge degraded health report flags into a risk state for entry blocking."""

        state = base or RiskState()
        reasons = report.degraded_reasons
        feed_degraded = any(reason.startswith("market_data_") for reason in reasons)
        return state.model_copy(
            update={
                "feed_degraded": state.feed_degraded or feed_degraded,
                "broker_state_mismatch": state.broker_state_mismatch
                or "fake_broker_state_mismatch" in reasons,
                "config_invalid": state.config_invalid or "config_invalid" in reasons,
                "degraded_reasons": sorted(set(state.degraded_reasons + reasons)),
            }
        )

    def _market_data_check(self, *, now: datetime, market: MarketSnapshot | None) -> HealthCheck:
        if market is None:
            return HealthCheck(
                name="market_data",
                status="degraded",
                reason="market_data_missing",
                details={"max_age_seconds": self.max_market_data_age_seconds},
            )
        age = now.astimezone(UTC) - market.timestamp.astimezone(UTC)
        max_age = timedelta(seconds=self.max_market_data_age_seconds)
        if age > max_age:
            return HealthCheck(
                name="market_data",
                status="degraded",
                reason="market_data_stale",
                details={"age_seconds": int(age.total_seconds()), "max_age_seconds": self.max_market_data_age_seconds},
            )
        return HealthCheck(
            name="market_data",
            status="healthy",
            details={"age_seconds": max(0, int(age.total_seconds()))},
        )

    def _config_check(self, *, config_errors: Iterable[str]) -> HealthCheck:
        errors = [error for error in config_errors if error]
        if errors:
            return HealthCheck(
                name="config",
                status="degraded",
                reason="config_invalid",
                details={"error_count": len(errors)},
            )
        return HealthCheck(name="config", status="healthy")

    def _broker_state_check(
        self,
        *,
        adapter: FakeExecutionAdapter | None,
        expected_snapshot: ExecutionSnapshot | None,
    ) -> HealthCheck:
        if adapter is None or expected_snapshot is None:
            return HealthCheck(name="fake_broker_state", status="healthy")

        actual = adapter.reconcile()
        actual_order_ids = set(actual.orders)
        expected_order_ids = set(expected_snapshot.orders)
        actual_positions = {symbol: position.quantity for symbol, position in actual.positions.items()}
        expected_positions = {
            symbol: position.quantity for symbol, position in expected_snapshot.positions.items()
        }
        if actual_order_ids != expected_order_ids or actual_positions != expected_positions:
            return HealthCheck(
                name="fake_broker_state",
                status="degraded",
                reason="fake_broker_state_mismatch",
                details={
                    "actual_orders": len(actual_order_ids),
                    "expected_orders": len(expected_order_ids),
                    "actual_positions": len(actual_positions),
                    "expected_positions": len(expected_positions),
                },
            )
        return HealthCheck(name="fake_broker_state", status="healthy")

    def _risk_stop_check(
        self,
        *,
        state: RiskState | None,
        limits: RiskLimits | None,
    ) -> HealthCheck:
        if state is None:
            return HealthCheck(name="risk_stop", status="healthy")
        active_limits = limits or RiskLimits()
        if state.realized_pnl + state.unrealized_pnl <= -active_limits.max_daily_loss:
            return HealthCheck(
                name="risk_stop",
                status="degraded",
                reason="daily_loss_limit",
                details={"max_daily_loss": active_limits.max_daily_loss},
            )
        if state.open_positions >= active_limits.max_open_positions:
            return HealthCheck(
                name="risk_stop",
                status="degraded",
                reason="max_positions",
                details={"max_open_positions": active_limits.max_open_positions},
            )
        return HealthCheck(name="risk_stop", status="healthy")
