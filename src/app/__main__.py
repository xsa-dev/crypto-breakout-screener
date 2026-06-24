"""Точка входа торгового робота.

Поднимает три фоновые задачи: producer (сбор данных с Bybit), consumer
(детект пампов) и цикл перечитывания настроек. Связка producer→consumer→
signal_manager→tradebot описана в skill `tradebot-architecture`.

Запуск: `python -m src.app` (через uv — `uv run python -m src.app`).
"""

import asyncio

from src.app.screener.consumer import Consumer
from src.app.screener.producer import Producer
from src.app.tradebot import SignalManager
from src.core import exchange_info
from src.core.logger import setup_logger
from src.database import init_models

logger = setup_logger(name="tradebot")


async def main() -> None:
    """Запускает робота и держит его до отмены, затем корректно гасит."""
    logger.info("Tradebot starting")

    # Таблицы БД (идемпотентно) и правила округления Bybit.
    await init_models()
    await exchange_info.start()
    await exchange_info.ensure_loaded()

    producer = Producer()
    signal_manager = SignalManager()
    consumer = Consumer(producer=producer, signal_manager=signal_manager)

    # Создаёт приватный клиент, читает первый снапшот настроек и чистит висящие ордера.
    await signal_manager.start()

    tasks = [
        asyncio.create_task(producer.run()),
        asyncio.create_task(consumer.run()),
        asyncio.create_task(signal_manager.refresh_settings_loop()),
    ]

    logger.info("Tradebot started")
    try:
        await asyncio.gather(*tasks)
    except asyncio.CancelledError:
        pass
    finally:
        # Graceful shutdown: гасим циклы, отменяем задачи, дожидаемся активных сделок.
        producer.stop()
        consumer.stop()
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        await signal_manager.shutdown()
        await producer.shutdown()
        exchange_info.stop()
        logger.info("Tradebot stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
