"""Репозитории — операции с конкретными таблицами.

Плоские классы без наследования: каждый репозиторий принимает `AsyncSession`
и делает `session.add(...) + flush()`. Коммит вызывает фасад `Database`,
чтобы одной операцией закрывать сразу несколько изменений.
"""

import hashlib
import json
from collections.abc import Mapping, Sequence
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.enums import ScenarioType, Side
from src.core.models import BreakoutScore, Level, RiskDecision, TradeIntent

from .models import (
    BacktestRunORM,
    BreakoutConfigVersionORM,
    BreakoutLevelORM,
    BreakoutSignalORM,
    DecisionTraceORM,
    ExecutionFillORM,
    ExecutionOrderORM,
    OperatorAuditORM,
    PositionORM,
    RiskEventORM,
    SettingsORM,
    SignalORM,
    TradeIntentORM,
    TradeORM,
)


class SettingsRepository:
    """Настройки приложения. Singleton: всегда работаем с id=1."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self) -> SettingsORM | None:
        """Получить текущие настройки или `None`, если строки ещё нет."""
        return await self.session.get(SettingsORM, 1)

    async def get_or_create(self) -> SettingsORM:
        """Получить настройки или создать строку с дефолтами из модели."""
        existing = await self.get()
        if existing is not None:
            return existing

        # Все дефолты заданы прямо на полях SettingsORM — конструируем пустой объект.
        new = SettingsORM(id=1)
        self.session.add(new)
        await self.session.flush()
        return new


class SignalRepository:
    """Журнал срабатываний скринера."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(
        self,
        symbol: str,
        price: float,
        price_change_percent: float,
    ) -> SignalORM:
        """Записать новое срабатывание скринера."""
        signal = SignalORM(
            symbol=symbol,
            price=price,
            price_change_percent=price_change_percent,
        )
        self.session.add(signal)
        await self.session.flush()
        return signal

    async def get_last(self, limit: int = 50) -> Sequence[SignalORM]:
        """Последние N сигналов, новые сверху."""
        stmt = select(SignalORM).order_by(SignalORM.id.desc()).limit(limit)
        return (await self.session.scalars(stmt)).all()


class TradeRepository:
    """Журнал попыток робота войти в сделку."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(
        self,
        symbol: str,
        status: str,
        entry_price: float | None = None,
        reject_reason: str | None = None,
        error: str | None = None,
    ) -> TradeORM:
        """Записать решение робота: `executed` (с `entry_price`) или `rejected` (с `reject_reason`)."""
        trade = TradeORM(
            symbol=symbol,
            status=status,
            entry_price=entry_price,
            reject_reason=reject_reason,
            error=error,
        )
        self.session.add(trade)
        await self.session.flush()
        return trade

    async def get_last(self, limit: int = 50) -> Sequence[TradeORM]:
        """Последние N попыток входа, новые сверху."""
        stmt = select(TradeORM).order_by(TradeORM.id.desc()).limit(limit)
        return (await self.session.scalars(stmt)).all()


class BreakoutAuditRepository:
    """Persistence helpers for reproducible breakout config, replay, and audit records."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @staticmethod
    def config_hash(config: BaseModel | Mapping[str, Any]) -> str:
        """Return a stable content hash for a validated breakout configuration."""

        return _stable_hash(config)

    @staticmethod
    def dataset_hash(records: Sequence[Mapping[str, Any] | BaseModel]) -> str:
        """Return a deterministic replay dataset hash from canonical records."""

        return _stable_hash(records)

    async def record_config_version(
        self,
        config: BaseModel | Mapping[str, Any],
        *,
        label: str | None = None,
    ) -> BreakoutConfigVersionORM:
        payload = _normalize(config)
        if not isinstance(payload, dict):
            msg = "breakout config payload must normalize to an object"
            raise TypeError(msg)
        config_hash = _stable_hash(payload)
        existing = await self.session.scalar(
            select(BreakoutConfigVersionORM).where(BreakoutConfigVersionORM.config_hash == config_hash)
        )
        if existing is not None:
            return existing

        version = BreakoutConfigVersionORM(config_hash=config_hash, label=label, payload=payload)
        self.session.add(version)
        await self.session.flush()
        return version

    async def record_level(self, level: Level) -> BreakoutLevelORM:
        existing = await self.session.scalar(
            select(BreakoutLevelORM).where(BreakoutLevelORM.level_id == level.level_id)
        )
        if existing is not None:
            return existing

        payload = _normalize(level)
        record = BreakoutLevelORM(
            level_id=level.level_id,
            symbol=level.symbol,
            type=level.type.value,
            price=level.price,
            timeframe=level.timeframe.value,
            touches=level.touches,
            created_at=level.created_at,
            source_indexes=list(level.source_indexes),
            payload=payload if isinstance(payload, dict) else {},
        )
        self.session.add(record)
        await self.session.flush()
        return record

    async def record_breakout_signal(
        self,
        *,
        symbol: str,
        timestamp: datetime,
        side: Side,
        scenario: ScenarioType,
        score: BreakoutScore,
        level: Level | None,
        config_hash: str,
        dataset_hash: str | None = None,
    ) -> BreakoutSignalORM:
        level_record = await self.record_level(level) if level is not None else None
        level_payload = _normalize(level) if level is not None else None
        score_payload = _normalize(score)
        signal = BreakoutSignalORM(
            symbol=symbol,
            timestamp=timestamp,
            side=side.value,
            scenario=scenario.value,
            score=score.total,
            level_id=level_record.id if level_record is not None else None,
            level_payload=level_payload if isinstance(level_payload, dict) else None,
            score_payload=score_payload if isinstance(score_payload, dict) else {},
            config_hash=config_hash,
            dataset_hash=dataset_hash,
        )
        self.session.add(signal)
        await self.session.flush()
        return signal

    async def record_trade_intent(
        self,
        *,
        intent: TradeIntent,
        signal: BreakoutSignalORM | None,
        config_hash: str,
    ) -> TradeIntentORM:
        existing = await self.session.scalar(
            select(TradeIntentORM).where(TradeIntentORM.intent_id == intent.intent_id)
        )
        if existing is not None:
            return existing

        payload = _normalize(intent)
        record = TradeIntentORM(
            intent_id=intent.intent_id,
            signal_id=signal.id if signal is not None else None,
            symbol=intent.symbol,
            side=intent.side.value,
            entry_mode=intent.mode.value,
            entry_price=intent.entry_price,
            stop_price=intent.stop_price,
            quantity=intent.quantity,
            is_addon=intent.is_addon,
            config_hash=config_hash,
            payload=payload if isinstance(payload, dict) else {},
        )
        self.session.add(record)
        await self.session.flush()
        return record

    async def record_risk_event(
        self,
        *,
        event_id: str,
        signal: BreakoutSignalORM | None,
        intent: TradeIntent | None,
        decision: RiskDecision,
        config_hash: str,
        dataset_hash: str | None,
        risk_inputs: Mapping[str, Any] | None = None,
    ) -> RiskEventORM:
        payload = _normalize(decision)
        risk_event = RiskEventORM(
            event_id=event_id,
            signal_id=signal.id if signal is not None else None,
            trade_intent_id=intent.intent_id if intent is not None else None,
            approved=decision.approved,
            reason=decision.reason.value if decision.reason is not None else None,
            config_hash=config_hash,
            dataset_hash=dataset_hash,
            risk_inputs=_normalize(risk_inputs or {}),
            payload=payload if isinstance(payload, dict) else {},
        )
        self.session.add(risk_event)
        await self.session.flush()
        return risk_event

    async def record_risk_rejection_trace(
        self,
        *,
        trace_id: str,
        signal: BreakoutSignalORM,
        intent: TradeIntent,
        decision: RiskDecision,
        config_hash: str,
        dataset_hash: str | None,
        level: Level | None = None,
        risk_inputs: Mapping[str, Any] | None = None,
    ) -> DecisionTraceORM:
        await self.record_trade_intent(intent=intent, signal=signal, config_hash=config_hash)
        risk_event = await self.record_risk_event(
            event_id=f"{trace_id}:risk",
            signal=signal,
            intent=intent,
            decision=decision,
            config_hash=config_hash,
            dataset_hash=dataset_hash,
            risk_inputs=risk_inputs,
        )
        score_payload = _normalize(intent.score)
        risk_payload = _normalize(decision)
        level_payload = _normalize(level) if level is not None else signal.level_payload
        trace = DecisionTraceORM(
            trace_id=trace_id,
            signal_id=signal.id,
            trade_intent_id=intent.intent_id,
            risk_event_id=risk_event.id,
            config_hash=config_hash,
            dataset_hash=dataset_hash,
            symbol=intent.symbol,
            side=intent.side.value,
            scenario=intent.score.scenario.value,
            entry_mode=intent.mode.value,
            status="risk_rejected" if not decision.approved else "risk_approved",
            level_payload=level_payload if isinstance(level_payload, dict) else None,
            score_payload=score_payload if isinstance(score_payload, dict) else {},
            risk_payload=risk_payload if isinstance(risk_payload, dict) else {},
        )
        self.session.add(trace)
        await self.session.flush()
        return trace

    async def record_order(
        self,
        *,
        signal: BreakoutSignalORM | None,
        order_id: str,
        intent_id: str,
        symbol: str,
        side: Side,
        quantity: float,
        price: float,
        status: str,
        config_hash: str,
        source: str = "fake",
        payload: Mapping[str, Any] | None = None,
    ) -> ExecutionOrderORM:
        order = ExecutionOrderORM(
            order_id=order_id,
            signal_id=signal.id if signal is not None else None,
            intent_id=intent_id,
            symbol=symbol,
            side=side.value,
            quantity=quantity,
            price=price,
            status=status,
            config_hash=config_hash,
            source=source,
            payload=_normalize(payload or {}),
        )
        self.session.add(order)
        await self.session.flush()
        return order

    async def record_fill(
        self,
        *,
        order: ExecutionOrderORM,
        fill_id: str,
        timestamp: datetime,
        price: float,
        quantity: float,
        fee: float | None = None,
        source_metadata: Mapping[str, Any] | None = None,
    ) -> ExecutionFillORM:
        fill = ExecutionFillORM(
            fill_id=fill_id,
            order_id=order.id,
            timestamp=timestamp,
            fill_price=price,
            fill_quantity=quantity,
            fee=fee,
            source_metadata=_normalize(source_metadata or {}),
        )
        self.session.add(fill)
        await self.session.flush()
        return fill

    async def record_position(
        self,
        *,
        symbol: str,
        side: Side,
        quantity: float,
        average_price: float,
        opening_fill: ExecutionFillORM | None = None,
        status: str = "open",
        payload: Mapping[str, Any] | None = None,
    ) -> PositionORM:
        position = PositionORM(
            symbol=symbol,
            side=side.value,
            quantity=quantity,
            average_price=average_price,
            opening_fill_id=opening_fill.id if opening_fill is not None else None,
            status=status,
            payload=_normalize(payload or {}),
        )
        self.session.add(position)
        await self.session.flush()
        return position

    async def record_backtest_run(
        self,
        *,
        run_id: str,
        config_hash: str,
        dataset_hash: str,
        started_at: datetime,
        ended_at: datetime,
        metrics_payload: Mapping[str, Any] | None = None,
        artifact_paths: Sequence[str] = (),
    ) -> BacktestRunORM:
        run = BacktestRunORM(
            run_id=run_id,
            config_hash=config_hash,
            dataset_hash=dataset_hash,
            started_at=started_at,
            ended_at=ended_at,
            metrics_payload=_normalize(metrics_payload or {}),
            artifact_paths=list(artifact_paths),
        )
        self.session.add(run)
        await self.session.flush()
        return run

    async def record_operator_audit(
        self,
        *,
        action: str,
        actor: str,
        affected_entity_type: str,
        affected_entity_id: str,
        reason: str | None = None,
        payload: Mapping[str, Any] | None = None,
    ) -> OperatorAuditORM:
        audit = OperatorAuditORM(
            action=action,
            actor=actor,
            affected_entity_type=affected_entity_type,
            affected_entity_id=affected_entity_id,
            reason=reason,
            payload=_normalize(payload or {}),
        )
        self.session.add(audit)
        await self.session.flush()
        return audit


def _stable_hash(value: Any) -> str:
    canonical = json.dumps(_normalize(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return f"sha256:{hashlib.sha256(canonical.encode('utf-8')).hexdigest()}"


def _normalize(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return _normalize(value.model_dump(mode="json"))
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Mapping):
        return {str(key): _normalize(value[key]) for key in sorted(value)}
    if isinstance(value, tuple | list):
        return [_normalize(item) for item in value]
    return value
