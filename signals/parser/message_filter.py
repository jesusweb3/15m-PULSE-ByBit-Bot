# signals/parser/message_filter.py
from pyrogram.types import Message


class MessageFilter:
    REQUIRED_KEYWORDS = [
        "Entry Targets:",
        "Take-Profit Targets:",
        "Stop Targets:"
    ]

    SIGNAL_INDICATORS = ["🟩", "🟥", "(Long)", "(Short)"]

    @staticmethod
    def is_signal_message(message: Message) -> bool:
        """Проверка является ли сообщение торговым сигналом"""
        if not message.text:
            return False

        text = message.text

        has_all_keywords = all(keyword in text for keyword in MessageFilter.REQUIRED_KEYWORDS)

        if not has_all_keywords:
            return False

        has_signal_indicator = any(indicator in text for indicator in MessageFilter.SIGNAL_INDICATORS)

        return has_signal_indicator