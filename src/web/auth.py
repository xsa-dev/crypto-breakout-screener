"""Простой логин-флоу: одно поле «пароль» + cookie-сессия.

Без логина и пользователей — `ADMIN_PASSWORD` из `.env` сравнивается с тем,
что прислала форма. Если совпало — в session-cookie кладётся флаг `authed=True`.
Cookie подписана `ADMIN_SESSION_SECRET` через `SessionMiddleware` (см. `app.py`).
"""

import hmac

from fastapi import APIRouter, Form, HTTPException, Request, status
from fastapi.responses import RedirectResponse

from src.core.env import env

from .templates import templates

# Ключ в session-cookie, по которому проверяем, авторизован ли пользователь.
_SESSION_KEY = "authed"

router = APIRouter()


def require_auth(request: Request) -> None:
    """Dependency для защищённых страниц.

    Если в сессии нет флага авторизации — бросаем 401, его перехватит
    exception handler в `app.py` и редиректнет на `/login`.
    """
    if request.session.get(_SESSION_KEY) is not True:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)


def _is_authed(request: Request) -> bool:
    """Возвращает True, если в сессии есть валидный флаг авторизации."""
    return request.session.get(_SESSION_KEY) is True


@router.get("/login")
async def login_page(request: Request):
    """Страница логина. Если уже авторизованы — сразу на главную."""
    if _is_authed(request):
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse(request, "login.html", {"error": None})


@router.post("/login")
async def login_submit(request: Request, password: str = Form(...)):
    """Проверяем пароль и, если совпал, ставим флаг в сессии."""
    # hmac.compare_digest — защита от timing-атак.
    if hmac.compare_digest(password, env.admin_password):
        request.session[_SESSION_KEY] = True
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

    # Пароль не совпал — перерисовываем форму с ошибкой.
    return templates.TemplateResponse(
        request,
        "login.html",
        {"error": "Неверный пароль"},
        status_code=status.HTTP_401_UNAUTHORIZED,
    )


@router.get("/logout")
async def logout(request: Request):
    """Чистим сессию и отправляем обратно на логин."""
    request.session.clear()
    return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
