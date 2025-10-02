# signals/parser/signal_parser.py
import re
from datetime import datetime
from signals.parser.models import Signal
from utils.logger import get_logger

logger = get_logger(__name__)


class SignalParser:
    TICKER_PATTERN = r'([A-Z0-9]+/USDT)\s+\((Long|Short)\)'
    LEVERAGE_PATTERN = r'Leverage:.*?\((\d+)X\)'
    TAKE_PROFIT_PATTERN = r'Take-Profit Targets:\s*((?:\d+\)\s*[\d.]+\s*)+)'
    STOP_LOSS_PATTERN = r'Stop Targets:\s*([\d.]+)'

    @staticmethod
    def parse(message_text: str) -> Signal | None:
        """Парсинг текста сообщения в объект Signal"""
        try:
            ticker_match = re.search(SignalParser.TICKER_PATTERN, message_text)
            if not ticker_match:
                logger.warning("Не удалось извлечь тикер и направление")
                return None

            ticker = ticker_match.group(1)
            direction = ticker_match.group(2)

            leverage_match = re.search(SignalParser.LEVERAGE_PATTERN, message_text)
            if not leverage_match:
                logger.warning(f"Не удалось извлечь плечо для {ticker}")
                return None
            leverage = int(leverage_match.group(1))

            tp_match = re.search(SignalParser.TAKE_PROFIT_PATTERN, message_text, re.DOTALL)
            if not tp_match:
                logger.warning(f"Не удалось извлечь take-profit для {ticker}")
                return None

            tp_text = tp_match.group(1)
            take_profits = re.findall(r'\d+\)\s*([\d.]+)', tp_text)
            take_profits = [float(tp) for tp in take_profits if tp]

            if not take_profits:
                logger.warning(f"Список take-profit пуст для {ticker}")
                return None

            sl_match = re.search(SignalParser.STOP_LOSS_PATTERN, message_text)
            if not sl_match:
                logger.warning(f"Не удалось извлечь stop-loss для {ticker}")
                return None
            stop_loss = float(sl_match.group(1))

            signal = Signal(
                ticker=ticker,
                direction=direction,
                leverage=leverage,
                take_profits=take_profits,
                stop_loss=stop_loss,
                timestamp=datetime.now(),
                raw_message=message_text
            )

            return signal

        except Exception as e:
            logger.error(f"Ошибка парсинга сигнала: {e}", exc_info=True)
            return None