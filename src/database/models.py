"""ORM-модели приложения.

Три таблицы по ТЗ торгового робота:
- `settings` — singleton (id=1) с runtime-настройками скринера и торговой части.
- `signals` — append-only журнал срабатываний скринера.
- `trades` — append-only журнал попыток входа в сделку.
"""

import datetime
from typing import Any

from sqlalchemy import JSON, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Базовый класс для всех ORM-моделей."""


class SettingsORM(Base):
    """Настройки скринера и торгового робота.

    Singleton: всегда ровно одна строка с `id=1`. Меняется через веб-админку,
    робот перечитывает их из БД на лету (см. skill `graceful-config-reload`).
    """

    __tablename__ = "settings"

    id: Mapped[int] = mapped_column(primary_key=True, default=1)

    # --- Общий флаг ---------------------------------------------------------

    enabled: Mapped[bool] = mapped_column(default=True)
    """Главный рубильник. `false` — скринер крутится, но сигналы не превращаются в сделки."""

    # --- Скринер ------------------------------------------------------------

    pump_threshold_percent: Mapped[float] = mapped_column(default=3.0)
    """Порог пампа: на сколько процентов текущая цена должна быть выше минимума за окно."""

    window_seconds: Mapped[int] = mapped_column(default=30)
    """Размер окна, на котором ищем минимум цены, секунды."""

    min_daily_volume_usdt: Mapped[int | None] = mapped_column(default=None)
    """Фильтр по 24h-объёму тикера. `None` — без фильтра."""

    blacklist: Mapped[str | None] = mapped_column(default=None)
    """Тикеры через запятую: 'BTC,ETH,SOL'. Парсится в `parse_blacklist()`."""

    cooldown_minutes: Mapped[int] = mapped_column(default=15)
    """Кулдаун по тикеру: не открывать новую сделку по тому же символу N минут после предыдущей."""

    # --- Торговая часть -----------------------------------------------------

    trading_enabled: Mapped[bool] = mapped_column(default=False)
    """Отдельный флаг для торговли. По дефолту off — сначала смотрим сигналы, потом включаем ордера."""

    order_size_usdt: Mapped[float] = mapped_column(default=5.0)
    """Размер одной сделки в USDT."""

    max_concurrent_trades: Mapped[int] = mapped_column(default=3)
    """Максимум одновременно открытых сделок."""

    entry_fib_level: Mapped[float] = mapped_column(default=0.5)
    """Куда ставим лимитку относительно импульса (доля Фибоначчи)."""

    order_ttl_seconds: Mapped[int] = mapped_column(default=60)
    """Сколько ждём исполнения лимитки. После — отмена."""

    take_profit_fib: Mapped[float] = mapped_column(default=0.9)
    """TP как уровень Фибоначчи на размахе пампа (0 — минимум окна, 1 — точка обнаружения)."""

    stop_loss_fib: Mapped[float] = mapped_column(default=0.3)
    """SL как уровень Фибоначчи на размахе пампа (0 — минимум окна, 1 — точка обнаружения)."""

    def parse_blacklist(self) -> list[str]:
        """Распарсить `blacklist` ('BTC,ETH,SOL') в список тикеров в верхнем регистре."""
        if not self.blacklist:
            return []
        return [s.strip().upper() for s in self.blacklist.split(",") if s.strip()]


class SignalORM(Base):
    """Журнал срабатываний скринера. Только append, не редактируется."""

    __tablename__ = "signals"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    created_at: Mapped[datetime.datetime] = mapped_column(server_default=func.now())
    symbol: Mapped[str]
    price: Mapped[float]
    """Цена в момент сигнала."""

    price_change_percent: Mapped[float]
    """На сколько процентов текущая цена выше минимума за окно."""


class TradeORM(Base):
    """Журнал попыток робота войти в сделку.

    Каждая строка — одно решение робота. Если позиция реально открылась — `status='executed'`
    с фактической `entry_price`. Если робот отказался (торговля выключена, лимит сделок,
    лимитка не исполнилась за TTL, биржа отвергла) — `status='rejected'` + `reject_reason`.

    Запись **никогда не обновляется** после создания. Постфактумную судьбу позиции
    (TP/SL, P&L) смотрим на бирже — в БД её не дублируем.
    """

    __tablename__ = "trades"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    created_at: Mapped[datetime.datetime] = mapped_column(server_default=func.now())
    symbol: Mapped[str]
    status: Mapped[str]
    """`executed` или `rejected`."""

    entry_price: Mapped[float | None] = mapped_column(default=None)
    """Фактическая цена входа с биржи. `None` для `rejected`."""

    reject_reason: Mapped[str | None] = mapped_column(default=None)
    """Если `rejected` — короткий текст: `trading_disabled`, `not_filled`, `cooldown`,
    `blacklist`, `low_volume`, `concurrent_limit`, `exchange_error`. `None` для `executed`."""

    error: Mapped[str | None] = mapped_column(default=None)
    """Если по ходу попытки прилетела ошибка от биржи или из кода — короткий текст исключения."""


class BreakoutConfigVersionORM(Base):
    """Validated strategy config snapshot addressed by a stable content hash."""

    __tablename__ = "breakout_config_versions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    created_at: Mapped[datetime.datetime] = mapped_column(server_default=func.now())
    config_hash: Mapped[str] = mapped_column(unique=True, index=True)
    label: Mapped[str | None] = mapped_column(default=None)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON)


class MarketBarORM(Base):
    """Canonical OHLCV bar persisted for replay/backtest datasets."""

    __tablename__ = "market_bars"
    __table_args__ = (UniqueConstraint("symbol", "timeframe", "ts", name="uq_market_bar_key"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(index=True)
    timeframe: Mapped[str] = mapped_column(index=True)
    ts: Mapped[datetime.datetime] = mapped_column(index=True)
    open: Mapped[float]
    high: Mapped[float]
    low: Mapped[float]
    close: Mapped[float]
    volume: Mapped[float]
    source_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


class MarketTickORM(Base):
    """Canonical tick persisted when replay requires tick-level data."""

    __tablename__ = "market_ticks"
    __table_args__ = (UniqueConstraint("symbol", "ts", name="uq_market_tick_key"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(index=True)
    ts: Mapped[datetime.datetime] = mapped_column(index=True)
    bid: Mapped[float | None] = mapped_column(default=None)
    ask: Mapped[float | None] = mapped_column(default=None)
    last: Mapped[float | None] = mapped_column(default=None)
    volume: Mapped[float | None] = mapped_column(default=None)
    source_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


class BreakoutLevelORM(Base):
    """Persisted level reference used by signals and decision traces."""

    __tablename__ = "breakout_levels"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    level_id: Mapped[str] = mapped_column(unique=True, index=True)
    symbol: Mapped[str] = mapped_column(index=True)
    type: Mapped[str]
    price: Mapped[float]
    timeframe: Mapped[str]
    touches: Mapped[int]
    created_at: Mapped[datetime.datetime]
    source_indexes: Mapped[list[int]] = mapped_column(JSON, default=list)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


class BreakoutSignalORM(Base):
    """Audited breakout signal with score factors and replay identifiers."""

    __tablename__ = "breakout_signals"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    created_at: Mapped[datetime.datetime] = mapped_column(server_default=func.now())
    symbol: Mapped[str] = mapped_column(index=True)
    timestamp: Mapped[datetime.datetime] = mapped_column(index=True)
    side: Mapped[str]
    scenario: Mapped[str]
    score: Mapped[int]
    level_id: Mapped[int | None] = mapped_column(ForeignKey("breakout_levels.id"), default=None)
    level_payload: Mapped[dict[str, Any] | None] = mapped_column(JSON, default=None)
    score_payload: Mapped[dict[str, Any]] = mapped_column(JSON)
    config_hash: Mapped[str] = mapped_column(index=True)
    dataset_hash: Mapped[str | None] = mapped_column(default=None, index=True)


class TradeIntentORM(Base):
    """Broker-neutral intent generated before risk/execution decisions."""

    __tablename__ = "trade_intents"
    __table_args__ = (UniqueConstraint("intent_id", name="uq_trade_intent_id"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    intent_id: Mapped[str] = mapped_column(index=True)
    signal_id: Mapped[int | None] = mapped_column(ForeignKey("breakout_signals.id"), default=None)
    symbol: Mapped[str] = mapped_column(index=True)
    side: Mapped[str]
    entry_mode: Mapped[str]
    entry_price: Mapped[float]
    stop_price: Mapped[float]
    quantity: Mapped[float]
    is_addon: Mapped[bool] = mapped_column(default=False)
    config_hash: Mapped[str] = mapped_column(index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON)


class RiskEventORM(Base):
    """Risk approval/rejection event linked to a signal or trade intent."""

    __tablename__ = "risk_events"
    __table_args__ = (UniqueConstraint("event_id", name="uq_risk_event_id"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    event_id: Mapped[str] = mapped_column(index=True)
    created_at: Mapped[datetime.datetime] = mapped_column(server_default=func.now())
    signal_id: Mapped[int | None] = mapped_column(ForeignKey("breakout_signals.id"), default=None)
    trade_intent_id: Mapped[str | None] = mapped_column(default=None, index=True)
    approved: Mapped[bool]
    reason: Mapped[str | None] = mapped_column(default=None, index=True)
    config_hash: Mapped[str] = mapped_column(index=True)
    dataset_hash: Mapped[str | None] = mapped_column(default=None, index=True)
    risk_inputs: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON)


class ExecutionOrderORM(Base):
    """Order request/response record for fake or broker execution."""

    __tablename__ = "execution_orders"
    __table_args__ = (UniqueConstraint("order_id", name="uq_execution_order_id"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    order_id: Mapped[str] = mapped_column(index=True)
    signal_id: Mapped[int | None] = mapped_column(ForeignKey("breakout_signals.id"), default=None)
    intent_id: Mapped[str] = mapped_column(index=True)
    symbol: Mapped[str] = mapped_column(index=True)
    side: Mapped[str]
    quantity: Mapped[float]
    price: Mapped[float]
    status: Mapped[str]
    config_hash: Mapped[str] = mapped_column(index=True)
    source: Mapped[str] = mapped_column(default="fake")
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


class ExecutionFillORM(Base):
    """Fill record linked to an execution order."""

    __tablename__ = "execution_fills"
    __table_args__ = (UniqueConstraint("fill_id", name="uq_execution_fill_id"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    fill_id: Mapped[str] = mapped_column(index=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("execution_orders.id"), index=True)
    timestamp: Mapped[datetime.datetime]
    fill_price: Mapped[float]
    fill_quantity: Mapped[float]
    fee: Mapped[float | None] = mapped_column(default=None)
    source_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


class PositionORM(Base):
    """Position snapshot linked to fills or aggregated execution state."""

    __tablename__ = "positions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(index=True)
    side: Mapped[str]
    quantity: Mapped[float]
    average_price: Mapped[float]
    opening_fill_id: Mapped[int | None] = mapped_column(ForeignKey("execution_fills.id"), default=None)
    status: Mapped[str] = mapped_column(default="open")
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


class BacktestRunORM(Base):
    """Backtest/replay run metadata with config and dataset hashes."""

    __tablename__ = "backtest_runs"
    __table_args__ = (UniqueConstraint("run_id", name="uq_backtest_run_id"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(index=True)
    created_at: Mapped[datetime.datetime] = mapped_column(server_default=func.now())
    config_hash: Mapped[str] = mapped_column(index=True)
    dataset_hash: Mapped[str] = mapped_column(index=True)
    started_at: Mapped[datetime.datetime]
    ended_at: Mapped[datetime.datetime]
    metrics_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    artifact_paths: Mapped[list[str]] = mapped_column(JSON, default=list)


class OperatorAuditORM(Base):
    """Manual operator action audit record."""

    __tablename__ = "operator_audits"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    created_at: Mapped[datetime.datetime] = mapped_column(server_default=func.now())
    action: Mapped[str] = mapped_column(index=True)
    actor: Mapped[str]
    affected_entity_type: Mapped[str]
    affected_entity_id: Mapped[str]
    reason: Mapped[str | None] = mapped_column(default=None)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


class DecisionTraceORM(Base):
    """First-class replay/audit trace for one breakout decision."""

    __tablename__ = "decision_traces"
    __table_args__ = (UniqueConstraint("trace_id", name="uq_decision_trace_id"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    trace_id: Mapped[str] = mapped_column(index=True)
    created_at: Mapped[datetime.datetime] = mapped_column(server_default=func.now())
    signal_id: Mapped[int | None] = mapped_column(ForeignKey("breakout_signals.id"), default=None)
    trade_intent_id: Mapped[str | None] = mapped_column(default=None, index=True)
    risk_event_id: Mapped[int | None] = mapped_column(ForeignKey("risk_events.id"), default=None)
    config_hash: Mapped[str] = mapped_column(index=True)
    dataset_hash: Mapped[str | None] = mapped_column(default=None, index=True)
    symbol: Mapped[str] = mapped_column(index=True)
    side: Mapped[str | None] = mapped_column(default=None)
    scenario: Mapped[str | None] = mapped_column(default=None)
    entry_mode: Mapped[str | None] = mapped_column(default=None)
    status: Mapped[str]
    level_payload: Mapped[dict[str, Any] | None] = mapped_column(JSON, default=None)
    feature_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    score_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    risk_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    execution_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    position_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    exit_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    transitions_payload: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    manual_override_ids: Mapped[list[int]] = mapped_column(JSON, default=list)
