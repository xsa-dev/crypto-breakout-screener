"""Защищённые страницы админки: настройки, сигналы, сделки."""

from typing import Any

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import RedirectResponse
from pydantic import ValidationError

from src.database import Database

from .auth import require_auth
from .schemas import SettingsForm
from .templates import templates

# Все роуты этого роутера требуют авторизации.
router = APIRouter(dependencies=[Depends(require_auth)])


@router.get("/")
async def settings_page(request: Request, saved: int = 0):
    """Главная: форма редактирования singleton-настроек."""
    async with Database.session_context() as db:
        settings = await db.settings_repo.get_or_create()
        await db.commit()  # На случай первого запуска — фиксируем созданную строку.

    return templates.TemplateResponse(
        request,
        "settings.html",
        {
            "settings": settings,
            "saved": bool(saved),
            "errors": None,
            "active": "settings",
        },
    )


@router.post("/settings")
async def settings_save(request: Request):
    """Сохранить настройки.

    Принимаем форму целиком, валидируем через `SettingsForm`. Если валидация
    провалилась — перерисовываем форму с ошибками и текущими значениями.
    """
    form = await request.form()
    # Берём только строковые значения формы — файлов в этой админке нет.
    raw: dict[str, Any] = {k: v for k, v in form.items() if isinstance(v, str)}

    # Чекбоксы: если поле не пришло — значит снято. Pydantic поймёт "true"/"false".
    raw.setdefault("enabled", "false")
    raw.setdefault("trading_enabled", "false")

    # Пустая строка из формы для опциональных полей = None.
    if raw.get("min_daily_volume_usdt") == "":
        raw["min_daily_volume_usdt"] = None
    if raw.get("blacklist") == "":
        raw["blacklist"] = None

    try:
        validated = SettingsForm.model_validate(raw)
    except ValidationError as exc:
        # Ошибки валидации — показываем форму заново с тем, что пользователь ввёл.
        async with Database.session_context() as db:
            current = await db.settings_repo.get_or_create()

        # Перекрываем поля current тем, что пришло в форме, чтобы не терять ввод.
        for field, value in raw.items():
            if hasattr(current, field):
                setattr(current, field, value)

        return templates.TemplateResponse(
            request,
            "settings.html",
            {
                "settings": current,
                "saved": False,
                "errors": exc.errors(),
                "active": "settings",
            },
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    # Валидация ок — обновляем поля и коммитим.
    async with Database.session_context() as db:
        current = await db.settings_repo.get_or_create()
        for field, value in validated.model_dump().items():
            setattr(current, field, value)
        await db.commit()

    return RedirectResponse(url="/?saved=1", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/signals")
async def signals_page(request: Request):
    """Таблица последних 100 срабатываний скринера."""
    async with Database.session_context() as db:
        signals = await db.signal_repo.get_last(limit=100)

    return templates.TemplateResponse(
        request,
        "signals.html",
        {"signals": signals, "active": "signals"},
    )


@router.get("/trades")
async def trades_page(request: Request):
    """Таблица последних 100 попыток входа в сделку."""
    async with Database.session_context() as db:
        trades = await db.trade_repo.get_last(limit=100)

    return templates.TemplateResponse(
        request,
        "trades.html",
        {"trades": trades, "active": "trades"},
    )
