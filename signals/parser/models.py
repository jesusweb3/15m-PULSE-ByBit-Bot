# signals/parser/models.py
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Signal:
    ticker: str
    direction: str
    leverage: int
    take_profits: list[float]
    stop_loss: float
    timestamp: datetime
    raw_message: str

    def __post_init__(self):
        if self.direction not in ["Long", "Short"]:
            raise ValueError(f"Неверное направление: {self.direction}. Должно быть 'Long' или 'Short'")

        if self.leverage <= 0:
            raise ValueError(f"Неверное плечо: {self.leverage}. Должно быть больше 0")

        if not self.take_profits:
            raise ValueError("Список take-profit не может быть пустым")

        if self.stop_loss <= 0:
            raise ValueError(f"Неверный stop-loss: {self.stop_loss}. Должен быть больше 0")

    def __str__(self) -> str:
        tp_list = ", ".join([str(tp) for tp in self.take_profits])
        return (
            f"{self.ticker} {self.direction} {self.leverage}x | "
            f"TP: [{tp_list}] | SL: {self.stop_loss}"
        )