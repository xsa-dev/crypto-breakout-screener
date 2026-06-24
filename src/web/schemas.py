"""Pydantic-схемы для валидации форм админки."""

from pydantic import BaseModel, Field


class SettingsForm(BaseModel):
    """Форма редактирования настроек.

    Поля 1-в-1 повторяют `SettingsORM` из `database/models.py`, но с
    дополнительными ограничениями диапазонов — это валидация формы со стороны
    приложения (HTML-валидация в браузере — это только UX-подсказка).
    """

    # Общий рубильник
    enabled: bool = False

    # Скринер
    pump_threshold_percent: float = Field(gt=0)
    window_seconds: int = Field(gt=0)
    min_daily_volume_usdt: int | None = Field(default=None, ge=0)
    blacklist: str | None = None
    cooldown_minutes: int = Field(ge=0)

    # Торговая часть
    trading_enabled: bool = False
    order_size_usdt: float = Field(gt=0)
    max_concurrent_trades: int = Field(gt=0)
    entry_fib_level: float = Field(ge=0, le=1)
    order_ttl_seconds: int = Field(gt=0)
    # TP/SL без ограничений: уровень <0 ставит цену ниже минимума окна, >1 — выше
    # точки обнаружения. Оба варианта осмысленны (стоп под началом / тейк за пиком).
    take_profit_fib: float
    stop_loss_fib: float
