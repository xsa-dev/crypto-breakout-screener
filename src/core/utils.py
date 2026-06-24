"""Утилиты приложения: переиспользуемые, неспецифичные хелперы."""

__all__ = ["TelegramBot", "TimeoutTracker"]

import time

import aiohttp
from loguru import logger


class TelegramBot:
    """HTTP-клиент для отправки сообщений через Telegram Bot API."""

    def __init__(self, bot_token: str) -> None:
        """Инициализирует бота. HTTP-сессия создаётся лениво при первой отправке.

        Args:
            bot_token: Токен Telegram-бота из @BotFather.
        """
        self._bot_token = bot_token
        self._session: aiohttp.ClientSession | None = None

    async def send_message(self, chat_id: int, text: str) -> None:
        """Отправляет HTML-сообщение в чат.

        Ошибка отправки только логируется — алерт best-effort и не должен
        ронять скринер или бота. Если токен или chat_id пустые — молча выходим
        (робот работает «всухую» без Telegram).

        Args:
            chat_id: ID чата получателя. Для каналов — ID со знаком минус.
            text: Текст сообщения. Поддерживается HTML-разметка Telegram.
        """
        # Без токена/чата Telegram не настроен — это штатный режим без алертов.
        if not self._bot_token or not chat_id:
            return

        url = f"https://api.telegram.org/bot{self._bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }
        try:
            session = self._get_session()
            async with session.post(url, json=payload) as resp:
                if resp.status != 200:
                    body = await resp.text()
                    logger.error(f"Telegram send failed: status={resp.status} body={body}")
        except Exception as e:
            logger.exception(f"Telegram send error: {e}")

    async def close(self) -> None:
        """Закрывает HTTP-сессию. Вызывать при остановке приложения."""
        if self._session and not self._session.closed:
            await self._session.close()

    def _get_session(self) -> aiohttp.ClientSession:
        """Возвращает живую HTTP-сессию, создавая её при первом обращении."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session


class TimeoutTracker[T]:
    """Блокирует объект на заданное время. Используется для кулдаунов сигналов."""

    def __init__(self) -> None:
        self._blocked_items: dict[T, float] = {}

    def is_blocked(self, item: T) -> bool:
        """Проверяет, заблокирован ли объект.

        Если срок блокировки истёк — автоматически удаляет запись.
        """
        if item in self._blocked_items:
            if time.time() < self._blocked_items[item]:
                return True
            del self._blocked_items[item]
        return False

    def block(self, item: T, duration: int) -> None:
        """Блокирует объект на duration секунд."""
        self._blocked_items[item] = time.time() + duration
