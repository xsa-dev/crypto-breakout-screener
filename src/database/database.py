"""Database фасад: engine, session, репозитории."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.core.env import env

from .models import Base
from .repositories import (
    BreakoutAuditRepository,
    SettingsRepository,
    SignalRepository,
    TradeRepository,
)


class Database:
    """Точка входа во все операции с БД.

    Использование:
        async with Database.session_context() as db:
            settings = await db.settings_repo.get_or_create()
            settings.trading_enabled = True
            await db.commit()
    """

    engine: AsyncEngine = create_async_engine(
        url=f"sqlite+aiosqlite:///{env.db_path}",
        echo=False,
    )
    sessionmaker = async_sessionmaker(bind=engine, expire_on_commit=False)

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.settings_repo = SettingsRepository(session)
        self.signal_repo = SignalRepository(session)
        self.trade_repo = TradeRepository(session)
        self.breakout_audit_repo = BreakoutAuditRepository(session)

    @classmethod
    @asynccontextmanager
    async def session_context(cls) -> AsyncGenerator["Database", None]:
        """Открыть сессию и собрать на ней репозитории."""
        async with cls.sessionmaker() as session:
            yield cls(session)

    async def commit(self) -> None:
        """Зафиксировать все изменения, накопленные в сессии."""
        await self.session.commit()


async def init_models() -> None:
    """Создать таблицы при первом запуске. Идемпотентно.

    На учебном этапе курса миграций нет — при изменении схемы пересоздаём
    файл БД (после подтверждения пользователя и бэкапа).
    """
    async with Database.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
