"""Округление цен и объёмов под фильтры Bybit (tickSize / stepSize).

Тонкий фасад над `unicex.bybit.ExchangeInfo`: вся остальная кодовая база зовёт
округление только через эти функции. Если когда-нибудь понадобится уйти от
unicex на standalone-модуль (`.claude/skills/exchange-rounding/bybit.py`) —
правка будет только здесь.

Алгоритм округления внутри unicex — floor через Decimal, возвращается str:
отправляем результат в параметры ордера как есть, без обратной конвертации.
"""

__all__ = ["start", "stop", "ensure_loaded", "round_price", "round_quantity"]

from unicex.bybit import ExchangeInfo


async def start(update_interval_seconds: int = 60 * 60) -> None:
    """Запускает фоновое обновление правил округления (раз в час по умолчанию)."""
    await ExchangeInfo.start(update_interval_seconds)


def stop() -> None:
    """Останавливает фоновое обновление правил."""
    ExchangeInfo.stop()


async def ensure_loaded() -> None:
    """Принудительно дожидается первой загрузки правил.

    Вызывать сразу после start(), иначе первый round_* может прийтись на момент,
    когда фоновая задача ещё не успела загрузить exchange info.
    """
    await ExchangeInfo.load_exchange_info()


def round_price(symbol: str, price: float) -> str:
    """Округляет цену фьючерсного символа вниз до tickSize. Возвращает str."""
    return ExchangeInfo.round_futures_price(symbol, price)


def round_quantity(symbol: str, quantity: float) -> str:
    """Округляет объём фьючерсного символа вниз до stepSize. Возвращает str."""
    return ExchangeInfo.round_futures_quantity(symbol, quantity)
