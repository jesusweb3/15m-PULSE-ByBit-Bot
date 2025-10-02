# signals/parser/channel_listener.py
import asyncio
from pyrogram import Client
from pyrogram.types import Message
from signals.parser.message_filter import MessageFilter
from signals.parser.signal_parser import SignalParser
from utils.logger import get_logger

logger = get_logger(__name__)


class ChannelListener:
    def __init__(self, client: Client, channel_name: str, polling_interval: int = 2):
        self.client = client
        self.channel_name = channel_name
        self.polling_interval = polling_interval
        self.last_message_id: int = 0
        self.is_running: bool = False

    async def start(self) -> None:
        """Запуск прослушивания канала"""
        try:
            chat = await self.client.get_chat(self.channel_name)
            logger.info(f"Успешное подключение к каналу: {chat.title} (ID: {chat.id})")
        except Exception as e:
            logger.error(f"Не удалось подключиться к каналу {self.channel_name}: {e}")
            raise

        await self._initialize_last_message_id()

        self.is_running = True

        while self.is_running:
            try:
                await self._poll_new_messages()
                await asyncio.sleep(self.polling_interval)
            except asyncio.CancelledError:
                logger.info("Получен сигнал завершения")
                break
            except Exception as e:
                logger.error(f"Ошибка в цикле polling: {e}", exc_info=True)
                await asyncio.sleep(self.polling_interval)

    async def stop(self) -> None:
        """Остановка прослушивания канала"""
        self.is_running = False

    async def _initialize_last_message_id(self) -> None:
        """Инициализация last_message_id последним сообщением из канала"""
        try:
            async for message in self.client.get_chat_history(self.channel_name, limit=1):
                self.last_message_id = message.id
                break
        except Exception as e:
            logger.error(f"Ошибка инициализации last_message_id: {e}")
            self.last_message_id = 0

    async def _poll_new_messages(self) -> None:
        """Получение новых сообщений из канала"""
        try:
            messages: list[Message] = []

            async for message in self.client.get_chat_history(self.channel_name, limit=20):
                if message.id <= self.last_message_id:
                    break
                messages.append(message)

            messages.reverse()

            for message in messages:
                self._process_message(message)
                self.last_message_id = message.id

        except Exception as e:
            logger.error(f"Ошибка получения новых сообщений: {e}", exc_info=True)

    @staticmethod
    def _process_message(message: Message) -> None:
        """Обработка одного сообщения"""
        if not MessageFilter.is_signal_message(message):
            return

        signal = SignalParser.parse(message.text)

        if signal:
            logger.info(f"Получен новый сигнал: {signal}")