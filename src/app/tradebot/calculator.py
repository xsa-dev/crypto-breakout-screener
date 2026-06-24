"""Чистые расчёты для стратегии «лонг на ретрейс пампа».

Без I/O и округления — только формулы из ТЗ. Округление под фильтры биржи
делается в Tradebot перед отправкой ордера (skill `exchange-rounding`).
"""

__all__ = ["fib_price", "quantity_from_usdt"]


def fib_price(window_min: float, current_price: float, level: float) -> float:
    """Считает цену по уровню Фибоначчи на размахе пампа.

    Единая формула для входа, тейка и стопа: минимум окна (начало пампа) — это
    уровень 0, текущая цена (точка обнаружения) — уровень 1. Любой уровень между
    ними (или за их пределами) — линейная доля размаха.

    Цена = window_min + (current_price − window_min) × level.

    Пример: window_min=100, current_price=110 (размах 10), level=0.3 → 103.

    Args:
        window_min: минимальная цена за окно (уровень 0).
        current_price: текущая цена, точка обнаружения пампа (уровень 1).
        level: уровень Фибоначчи, доля размаха.

    Returns:
        Цена, соответствующая заданному уровню.
    """
    return window_min + (current_price - window_min) * level


def quantity_from_usdt(usdt: float, entry: float) -> float:
    """Сырой объём в монетах из суммы в USDT: usdt / цена входа.

    Результат ещё нужно округлить по stepSize перед ордером.
    """
    return usdt / entry
