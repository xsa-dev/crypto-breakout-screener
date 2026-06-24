__all__ = ["Configuration", "config"]

from dataclasses import dataclass


@dataclass(frozen=True)
class Configuration:
    """Технические константы приложения.

    Меняются только с релизом новой версии — в отличие от runtime-настроек,
    которые лежат в БД и правятся через админку на лету.
    """

    # --- WebSocket-скринер ---
    # Сколько тикеров на один WS-коннект. Меньше — равномернее нагрузка и быстрее реконнект.
    WS_BATCH_SIZE: int = 10
    # Интервал WS-ping в секундах (Bybit понимает стандартный WS-frame ping).
    WS_PING_INTERVAL: int = 20

    # --- Перечитывание настроек и опрос ордеров ---
    # Как часто робот перечитывает settings из БД (горячая перезагрузка без рестарта).
    SETTINGS_REFRESH_SECONDS: int = 10
    # Период опроса статуса выставленного лимитного ордера, секунды.
    ORDER_POLL_INTERVAL: float = 1.0

    # --- Шаблоны ссылок для Telegram-алертов ---
    # {symbol} подставляется как полный символ Bybit, например BTCUSDT.
    # Для фьючерсов TradingView нужен префикс биржи BYBIT: и суффикс .P (см. skill signal-links).
    TRADINGVIEW_URL_TEMPLATE: str = "https://www.tradingview.com/chart/?symbol=BYBIT:{symbol}.P"
    BYBIT_URL_TEMPLATE: str = "https://www.bybit.com/trade/usdt/{symbol}"


config = Configuration()
