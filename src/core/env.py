__all__ = ["Environment", "env"]

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(BaseSettings):
    """Переменные окружения приложения."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Путь к файлу SQLite. Локально — `app.db` в корне; на VPS — `/var/lib/tradebot/app.db`.
    db_path: str = Field(default="app.db")

    # Пароль для входа в веб-админку. Логина нет — только пароль.
    admin_password: str = Field(default="changeme")

    # Секрет для подписи cookie-сессии админки. В .env должен быть длинной случайной строкой.
    admin_session_secret: str = Field(default="changeme-please-generate-random")

    # Ключ и секрет Bybit API (право Futures Trade). Пустые — робот работает «всухую»:
    # скринер крутится, но реальные ордера не выставляются.
    bybit_api_key: str = Field(default="")
    bybit_api_secret: str = Field(default="")

    # Токен Telegram-бота и id чата для алертов. Пустые — уведомления не отправляются.
    tg_bot_token: str = Field(default="")
    tg_chat_id: int = Field(default=0)


env = Environment()  # type: ignore[call-arg]
