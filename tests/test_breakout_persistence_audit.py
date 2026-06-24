import asyncio
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta
from typing import TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.core.enums import EntryMode, LevelType, RiskRejectionReason, ScenarioType, Side, TimeFrame
from src.core.models import BreakoutScore, BreakoutStrategyConfig, Level, RiskDecision, TradeIntent
from src.core.schemas import Bar
from src.database.models import Base, BreakoutConfigVersionORM, DecisionTraceORM, RiskEventORM
from src.database.repositories import BreakoutAuditRepository

T = TypeVar("T")


async def with_audit_repo(fn: Callable[[BreakoutAuditRepository], Awaitable[T]]) -> T:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    sessionmaker = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with sessionmaker() as session:
        result = await fn(BreakoutAuditRepository(session))
    await engine.dispose()
    return result


def test_breakout_config_hash_is_stable_for_semantically_identical_config() -> None:
    config = BreakoutStrategyConfig()
    reordered_payload = config.model_dump(mode="json")
    reordered_payload = dict(reversed(list(reordered_payload.items())))

    first = BreakoutAuditRepository.config_hash(config)
    second = BreakoutAuditRepository.config_hash(reordered_payload)

    assert first == second
    assert first.startswith("sha256:")
    assert len(first) == len("sha256:") + 64


def test_config_versions_are_reused_by_stable_hash() -> None:
    async def scenario(audit_repo: BreakoutAuditRepository) -> None:
        config = BreakoutStrategyConfig()

        first = await audit_repo.record_config_version(config, label="baseline")
        second = await audit_repo.record_config_version(
            config.model_dump(mode="json"), label="baseline-copy"
        )

        assert first.id == second.id
        assert first.config_hash == BreakoutAuditRepository.config_hash(config)
        rows = (await audit_repo.session.scalars(select(BreakoutConfigVersionORM))).all()
        assert len(rows) == 1

    asyncio.run(with_audit_repo(scenario))


def test_risk_rejection_trace_links_signal_intent_config_and_dataset() -> None:
    async def scenario(audit_repo: BreakoutAuditRepository) -> None:
        config = BreakoutStrategyConfig()
        config_version = await audit_repo.record_config_version(config)
        level = Level(
            level_id="level-1",
            symbol="XAUUSD",
            type=LevelType.PIVOT_HIGH,
            price=100.0,
            timeframe=TimeFrame.M15,
            touches=2,
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
            source_indexes=[1, 2],
        )
        score = BreakoutScore(
            symbol="XAUUSD",
            side=Side.LONG,
            scenario=ScenarioType.CONSOLIDATION_BREAKOUT,
            total=40,
            consolidation=10,
            slow_approach=10,
            trend=10,
            activity=10,
            density=0,
            eligibility="blocked",
            rejection_reasons=[RiskRejectionReason.SCORE_TOO_LOW.value],
        )
        intent = TradeIntent(
            intent_id="intent-1",
            symbol="XAUUSD",
            side=Side.LONG,
            mode=EntryMode.POST_BREAKOUT,
            entry_price=101.0,
            stop_price=99.0,
            quantity=1.5,
            score=score,
        )
        decision = RiskDecision(approved=False, reason=RiskRejectionReason.SCORE_TOO_LOW)
        bars: list[Bar] = [
            {
                "symbol": "XAUUSD",
                "timeframe": "M15",
                "ts": datetime(2026, 1, 1, tzinfo=UTC) + timedelta(minutes=15 * i),
                "open": 99.0 + i,
                "high": 101.0 + i,
                "low": 98.0 + i,
                "close": 100.0 + i,
                "volume": 10.0 + i,
            }
            for i in range(2)
        ]
        dataset_hash = BreakoutAuditRepository.dataset_hash(bars)

        signal = await audit_repo.record_breakout_signal(
            symbol="XAUUSD",
            timestamp=bars[-1]["ts"],
            side=Side.LONG,
            scenario=ScenarioType.CONSOLIDATION_BREAKOUT,
            score=score,
            level=level,
            config_hash=config_version.config_hash,
            dataset_hash=dataset_hash,
        )
        trace = await audit_repo.record_risk_rejection_trace(
            trace_id="trace-1",
            signal=signal,
            intent=intent,
            decision=decision,
            config_hash=config_version.config_hash,
            dataset_hash=dataset_hash,
            level=level,
        )

        risk_event = await audit_repo.session.scalar(select(RiskEventORM))
        stored_trace = await audit_repo.session.get(DecisionTraceORM, trace.id)

        assert stored_trace is not None
        assert risk_event is not None
        assert stored_trace.signal_id == signal.id
        assert stored_trace.trade_intent_id == "intent-1"
        assert stored_trace.config_hash == config_version.config_hash
        assert stored_trace.dataset_hash == dataset_hash
        assert stored_trace.risk_event_id == risk_event.id
        assert stored_trace.score_payload["rejection_reasons"] == ["score_too_low"]
        assert stored_trace.risk_payload["reason"] == "score_too_low"
        assert stored_trace.level_payload["level_id"] == "level-1"

    asyncio.run(with_audit_repo(scenario))


def test_fake_fill_chain_and_operator_override_are_audited() -> None:
    async def scenario(audit_repo: BreakoutAuditRepository) -> None:
        config_hash = BreakoutAuditRepository.config_hash(BreakoutStrategyConfig())
        score = BreakoutScore(
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
        signal = await audit_repo.record_breakout_signal(
            symbol="XAUUSD",
            timestamp=datetime(2026, 1, 1, tzinfo=UTC),
            side=Side.LONG,
            scenario=ScenarioType.CONSOLIDATION_BREAKOUT,
            score=score,
            level=None,
            config_hash=config_hash,
            dataset_hash="sha256:dataset",
        )

        order = await audit_repo.record_order(
            signal=signal,
            order_id="fake-1",
            intent_id="intent-1",
            symbol="XAUUSD",
            side=Side.LONG,
            quantity=2.0,
            price=100.0,
            status="accepted",
            config_hash=config_hash,
        )
        fill = await audit_repo.record_fill(
            order=order,
            fill_id="fill-1",
            timestamp=datetime(2026, 1, 1, 0, 1, tzinfo=UTC),
            price=100.2,
            quantity=2.0,
            fee=0.1,
            source_metadata={"adapter": "fake"},
        )
        position = await audit_repo.record_position(
            symbol="XAUUSD",
            side=Side.LONG,
            quantity=2.0,
            average_price=100.2,
            opening_fill=fill,
            status="open",
        )
        audit = await audit_repo.record_operator_audit(
            action="manual_override",
            actor="operator",
            affected_entity_type="position",
            affected_entity_id=str(position.id),
            reason="semi-auto test override",
        )

        assert order.signal_id == signal.id
        assert fill.order_id == order.id
        assert position.opening_fill_id == fill.id
        assert audit.affected_entity_id == str(position.id)

    asyncio.run(with_audit_repo(scenario))
