# trading/config.py
import os
from dotenv import load_dotenv
from utils.logger import get_logger

logger = get_logger(__name__)

load_dotenv()


class TradingConfig:
    BYBIT_API_KEY: str = os.getenv("BYBIT_API_KEY", "")
    BYBIT_API_SECRET: str = os.getenv("BYBIT_API_SECRET", "")
    AMOUNT: float = float(os.getenv("AMOUNT", "0"))
    BALANCE: float = float(os.getenv("BALANCE", "0"))

    TP1: float = float(os.getenv("TP1", ""))
    TP2: float = float(os.getenv("TP2", ""))
    TP3: float = float(os.getenv("TP3", ""))
    TP4: float = float(os.getenv("TP4", ""))
    TP5: float = float(os.getenv("TP5", ""))
    TP6: float = float(os.getenv("TP6", ""))
    TP7: float = float(os.getenv("TP7", ""))
    TP8: float = float(os.getenv("TP8", ""))

    @classmethod
    def get_tp_percentages(cls) -> list[float]:
        """Возвращает список процентов TP"""
        return [cls.TP1, cls.TP2, cls.TP3, cls.TP4, cls.TP5, cls.TP6, cls.TP7, cls.TP8]

    @classmethod
    def validate(cls) -> None:
        """Валидация обязательных параметров"""
        if not cls.BYBIT_API_KEY or not cls.BYBIT_API_SECRET:
            logger.error("Отсутствуют BYBIT_API_KEY или BYBIT_API_SECRET")
            raise ValueError("Отсутствуют обязательные параметры Bybit API в .env")

        if cls.AMOUNT <= 0:
            logger.error(f"AMOUNT должен быть больше 0, получено: {cls.AMOUNT}")
            raise ValueError("AMOUNT должен быть положительным числом")

        if cls.BALANCE <= 0:
            logger.error(f"BALANCE должен быть больше 0, получено: {cls.BALANCE}")
            raise ValueError("BALANCE должен быть положительным числом")

        tp_percentages = cls.get_tp_percentages()
        total_tp = sum(tp_percentages)

        if total_tp > 100:
            logger.error(f"Сумма TP превышает 100%: {total_tp}%")
            raise ValueError(f"Сумма всех TP не может превышать 100%, текущая: {total_tp}%")

        if all(tp == 0 for tp in tp_percentages):
            logger.error("Все TP параметры равны 0")
            raise ValueError("Хотя бы один TP должен быть больше 0")


TradingConfig.validate()