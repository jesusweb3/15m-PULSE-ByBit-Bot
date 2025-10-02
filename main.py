# main.py
import asyncio
from signals.auth.telegram_auth import TelegramAuth
from signals.parser.channel_listener import ChannelListener
from signals.config import SignalsConfig
from utils.logger import get_logger

logger = get_logger(__name__)


async def main():
    """Точка входа приложения"""
    auth = None
    listener = None

    try:
        logger.info("Запуск торгового бота")

        auth = TelegramAuth.from_config()
        client = await auth.connect()

        listener = ChannelListener(
            client=client,
            channel_name=SignalsConfig.CHANNEL_NAME,
            polling_interval=2
        )

        await listener.start()

    except KeyboardInterrupt:
        logger.info("Получен сигнал остановки (Ctrl+C)")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}", exc_info=True)
    finally:
        if listener:
            await listener.stop()
        if auth:
            await auth.disconnect()
        logger.info("Бот остановлен")


if __name__ == "__main__":
    asyncio.run(main())