from datetime import UTC, datetime, timedelta

from src.app.breakout.execution import FakeExecutionAdapter
from src.app.breakout.health import HealthMonitor
from src.app.breakout.risk_manager import RiskManager
from src.core.enums import EntryMode, RiskRejectionReason, ScenarioType, Side
from src.core.models import (
    BreakoutScore,
    ExecutionRequest,
    ExecutionSnapshot,
    MarketSnapshot,
    RiskLimits,
    RiskState,
    TradeIntent,
)
from src.core.utils import redact_secret_values


def score() -> BreakoutScore:
    return BreakoutScore(
        symbol="XAUUSD",
        side=Side.LONG,
        scenario=ScenarioType.CONSOLIDATION_BREAKOUT,
        total=80,
        consolidation=20,
        slow_approach=20,
        trend=20,
        activity=20,
        density=0,
        eligibility="normal",
    )


def intent() -> TradeIntent:
    return TradeIntent(
        intent_id="entry-1",
        symbol="XAUUSD",
        side=Side.LONG,
        mode=EntryMode.POST_BREAKOUT,
        entry_price=100.0,
        stop_price=98.0,
        quantity=1.0,
        score=score(),
    )


def market_at(timestamp: datetime) -> MarketSnapshot:
    return MarketSnapshot(
        symbol="XAUUSD",
        timestamp=timestamp,
        price=100.0,
        close=100.0,
        high=100.2,
        low=99.8,
    )


def test_health_monitor_detects_feed_gap_config_error_and_blocks_entries() -> None:
    now = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
    monitor = HealthMonitor(max_market_data_age_seconds=60)

    report = monitor.check(
        now=now,
        market=market_at(now - timedelta(seconds=90)),
        config_errors=["entry shares must sum to 1.0"],
        risk_state=RiskState(),
    )
    degraded_state = monitor.risk_state_from_report(report)
    decision = RiskManager().evaluate(intent(), degraded_state)

    assert report.status == "degraded"
    assert set(report.degraded_reasons) >= {"market_data_stale", "config_invalid"}
    assert degraded_state.feed_degraded is True
    assert degraded_state.config_invalid is True
    assert decision.approved is False
    assert decision.reason is RiskRejectionReason.FEED_DEGRADED
    assert decision.metadata["degraded_reasons"] == ["config_invalid", "market_data_stale"]


def test_missing_market_data_is_a_degraded_feed_state() -> None:
    report = HealthMonitor().check(now=datetime(2026, 1, 1, tzinfo=UTC), market=None)
    degraded_state = HealthMonitor().risk_state_from_report(report)

    assert report.degraded_reasons == ["market_data_missing"]
    assert degraded_state.feed_degraded is True


def test_health_monitor_detects_fake_adapter_reconciliation_mismatch() -> None:
    adapter = FakeExecutionAdapter()
    request = ExecutionRequest(
        request_id="req-1",
        intent_id="intent-1",
        symbol="XAUUSD",
        side=Side.LONG,
        quantity=2.0,
        price=100.0,
    )
    adapter.submit_order(request)
    expected_empty_snapshot = ExecutionSnapshot()

    report = HealthMonitor().check(
        now=datetime(2026, 1, 1, tzinfo=UTC),
        market=market_at(datetime(2026, 1, 1, tzinfo=UTC)),
        adapter=adapter,
        expected_snapshot=expected_empty_snapshot,
    )
    degraded_state = HealthMonitor().risk_state_from_report(report)

    assert "fake_broker_state_mismatch" in report.degraded_reasons
    assert degraded_state.broker_state_mismatch is True
    assert RiskManager().evaluate(intent(), degraded_state).reason is RiskRejectionReason.BROKER_STATE_MISMATCH


def test_health_monitor_detects_risk_stop_states() -> None:
    limits = RiskLimits(max_daily_loss=100.0, max_open_positions=1)
    report = HealthMonitor().check(
        now=datetime(2026, 1, 1, tzinfo=UTC),
        market=market_at(datetime(2026, 1, 1, tzinfo=UTC)),
        risk_state=RiskState(realized_pnl=-100.0),
        risk_limits=limits,
    )

    assert report.status == "degraded"
    assert report.degraded_reasons == ["daily_loss_limit"]


def test_secret_redaction_removes_known_values_and_token_shapes() -> None:
    secret = "123456:abcdefghijklmnopqrstuvwxyz"
    message = f"request failed for {secret} and api-key-abc"

    redacted = redact_secret_values(message, (secret, "api-key-abc"))

    assert secret not in redacted
    assert "api-key-abc" not in redacted
    assert redacted.count("[REDACTED]") == 2
