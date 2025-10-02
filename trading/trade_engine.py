# trading/trade_engine.py
from signals.parser.models import Signal
from trading.bybit_api import BybitAPI
from trading.config import TradingConfig
from utils.logger import get_logger

logger = get_logger(__name__)


class TradeEngine:
    def __init__(self):
        self.api = BybitAPI()

    def execute_signal(self, signal: Signal) -> None:
        """Исполнение торгового сигнала"""
        try:
            symbol = signal.ticker.replace("/", "")

            if not self.api.check_symbol_trading(symbol):
                logger.warning(f"Символ {symbol} недоступен для торговли, пропускаем сигнал")
                return

            if not self.api.set_leverage(symbol, signal.leverage):
                logger.error(f"Не удалось установить плечо для {symbol}, пропускаем сигнал")
                return

            last_price = self.api.get_last_price(symbol)
            if not last_price:
                logger.error(f"Не удалось получить цену для {symbol}, пропускаем сигнал")
                return

            filters = self.api.get_symbol_filters(symbol)
            if not filters:
                logger.error(f"Не удалось получить фильтры для {symbol}, пропускаем сигнал")
                return

            margin = TradingConfig.BALANCE * TradingConfig.AMOUNT / 100
            notional = margin * signal.leverage
            qty = notional / last_price
            qty_rounded = self.api.round_quantity(qty, filters["qty_step"])

            if qty_rounded < float(filters["min_qty"]):
                logger.error(f"Объём {qty_rounded} меньше минимального {filters['min_qty']}, пропускаем сигнал")
                return

            side = "Buy" if signal.direction == "Long" else "Sell"
            sl_rounded = self.api.round_price(signal.stop_loss, filters["tick_size"])

            order_id = self.api.place_market_order(symbol, side, qty_rounded, sl_rounded)
            if not order_id:
                logger.error(f"Не удалось открыть позицию для {symbol}, пропускаем сигнал")
                return

            self._place_take_profits(signal, symbol, qty_rounded, filters)

            logger.info(f"Сигнал {symbol} {signal.direction} успешно обработан")

        except Exception as e:
            logger.error(f"Ошибка исполнения сигнала {signal.ticker}: {e}", exc_info=True)

    def _place_take_profits(self, signal: Signal, symbol: str, total_qty: float, filters: dict) -> None:
        """Выставление Take Profit ордеров батчем"""
        try:
            tp_percentages = TradingConfig.get_tp_percentages()
            tp_side = "Sell" if signal.direction == "Long" else "Buy"

            batch_orders = []

            for i, (tp_price, tp_percent) in enumerate(zip(signal.take_profits, tp_percentages), start=1):
                if tp_percent <= 0:
                    continue

                tp_qty = total_qty * tp_percent / 100
                tp_qty_rounded = self.api.round_quantity(tp_qty, filters["qty_step"])

                if tp_qty_rounded < float(filters["min_qty"]):
                    logger.warning(f"TP{i}: объём {tp_qty_rounded} меньше минимального, пропускаем")
                    continue

                tp_price_rounded = self.api.round_price(tp_price, filters["tick_size"])

                batch_orders.append({
                    "price": tp_price_rounded,
                    "qty": tp_qty_rounded
                })

            if batch_orders:
                self.api.place_batch_limit_orders(symbol, tp_side, batch_orders)
            else:
                logger.warning(f"Нет валидных TP для выставления по {symbol}")

        except Exception as e:
            logger.error(f"Ошибка выставления TP для {symbol}: {e}", exc_info=True)