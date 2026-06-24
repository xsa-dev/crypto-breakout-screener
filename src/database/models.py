"""ORM-модели приложения.

Три таблицы по ТЗ торгового робота:
- `settings` — singleton (id=1) с runtime-настройками скринера и торговой части.
- `signals` — append-only журнал срабатываний скринера.
- `trades` — append-only журнал попыток входа в сделку.
"""

import datetime

from sqlalchemy import func
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
