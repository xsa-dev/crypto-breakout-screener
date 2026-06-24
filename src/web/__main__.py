"""FastAPI-приложение админки.

Запуск: `uvicorn src.web.__main__:app --host 0.0.0.0 --port 8000`.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import HTTPException
from fastapi.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

from src.core.env import env
from src.database import init_models

from . import auth, routes


@asynccontextmanager
async def _lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """На старте — создаём таблицы (идемпотентно)."""
    await init_models()
    yield


app = FastAPI(title="Tradebot Admin", lifespan=_lifespan)

# Подписанная cookie-сессия. max_age=14 дней — пользователь не логинится каждый день.
app.add_middleware(
    SessionMiddleware,
    secret_key=env.admin_session_secret,
    max_age=14 * 24 * 60 * 60,
    same_site="lax",
)


@app.exception_handler(HTTPException)
async def _redirect_unauthorized(request: Request, exc: HTTPException):
    """401 от `require_auth` превращаем в редирект на `/login`.

    Остальные HTTPException-ы возвращаем как есть, чтобы не глотать ошибки.
    """
    if exc.status_code == status.HTTP_401_UNAUTHORIZED:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    raise exc


app.include_router(auth.router)
app.include_router(routes.router)
