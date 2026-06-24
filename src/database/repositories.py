"""Репозитории — операции с конкретными таблицами.

Плоские классы без наследования: каждый репозиторий принимает `AsyncSession`
и делает `session.add(...) + flush()`. Коммит вызывает фасад `Database`,
чтобы одной операцией закрывать сразу несколько изменений.
"""

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import SettingsORM, SignalORM, TradeORM


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
