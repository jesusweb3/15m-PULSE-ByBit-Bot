# trading/bybit_api.py
from decimal import Decimal, ROUND_DOWN
from pybit.unified_trading import HTTP
from trading.config import TradingConfig
from utils.logger import get_logger

logger = get_logger(__name__)


class BybitAPI:
    def __init__(self):
        self.client = HTTP(
            api_key=TradingConfig.BYBIT_API_KEY,
            api_secret=TradingConfig.BYBIT_API_SECRET,
            testnet=False,
            timeout=10_000
        )

    def check_symbol_trading(self, symbol: str) -> bool:
        """Проверка доступности символа для торговли"""
        try:
            resp = self.client.get_instruments_info(category="linear", symbol=symbol)

            if not isinstance(resp, dict) or resp.get("retCode") != 0:
                logger.error(f"Ошибка проверки символа {symbol}: {resp}")
                return False

            instruments = resp.get("result", {}).get("list", [])
            if not instruments:
                logger.warning(f"Символ {symbol} не найден")
                return False

            status = instruments[0].get("status", "Unknown")

            if status == "Trading":
                return True
            else:
                logger.warning(f"Символ {symbol} недоступен, статус: {status}")
                return False

        except Exception as e:
            logger.error(f"Ошибка проверки символа {symbol}: {e}", exc_info=True)
            return False

    def set_leverage(self, symbol: str, leverage: int) -> bool:
        """Установка плеча для символа"""
        try:
            resp = self.client.set_leverage(
                category="linear",
                symbol=symbol,
                buyLeverage=str(leverage),
                sellLeverage=str(leverage)
            )

            if not isinstance(resp, dict) or resp.get("retCode") != 0:
                logger.error(f"Ошибка установки плеча {leverage}x для {symbol}: {resp}")
                return False

            return True

        except Exception as e:
            error_str = str(e)
            if "110043" in error_str:
                return True
            logger.error(f"Ошибка установки плеча для {symbol}: {e}", exc_info=True)
            return False

    def get_last_price(self, symbol: str) -> float | None:
        """Получение последней цены символа"""
        try:
            resp = self.client.get_tickers(category="linear", symbol=symbol)

            if not isinstance(resp, dict) or resp.get("retCode") != 0:
                logger.error(f"Ошибка получения цены {symbol}: {resp}")
                return None

            tickers = resp.get("result", {}).get("list", [])
            if not tickers:
                logger.error(f"Тикер {symbol} не найден")
                return None

            last_price = float(tickers[0].get("lastPrice", 0))
            return last_price

        except Exception as e:
            logger.error(f"Ошибка получения цены {symbol}: {e}", exc_info=True)
            return None

    def get_symbol_filters(self, symbol: str) -> dict[str, str] | None:
        """Получение фильтров символа"""
        try:
            resp = self.client.get_instruments_info(category="linear", symbol=symbol)

            if not isinstance(resp, dict) or resp.get("retCode") != 0:
                logger.error(f"Ошибка получения фильтров {symbol}: {resp}")
                return None

            instruments = resp.get("result", {}).get("list", [])
            if not instruments:
                logger.error(f"Инструмент {symbol} не найден")
                return None

            inst = instruments[0]
            lot = inst.get("lotSizeFilter", {})
            price = inst.get("priceFilter", {})

            filters = {
                "qty_step": lot.get("qtyStep", ""),
                "min_qty": lot.get("minOrderQty", ""),
                "max_qty": lot.get("maxOrderQty", ""),
                "tick_size": price.get("tickSize", "")
            }

            return filters

        except Exception as e:
            logger.error(f"Ошибка получения фильтров {symbol}: {e}", exc_info=True)
            return None

    @staticmethod
    def round_quantity(qty: float, qty_step: str) -> float:
        """Округление количества по правилам биржи"""
        try:
            qty_decimal = Decimal(str(qty))
            step_decimal = Decimal(qty_step)
            rounded = (qty_decimal / step_decimal).quantize(Decimal("1"), rounding=ROUND_DOWN) * step_decimal
            return float(rounded)
        except Exception as e:
            logger.error(f"Ошибка округления количества {qty}: {e}", exc_info=True)
            return 0.0

    @staticmethod
    def round_price(price: float, tick_size: str) -> float:
        """Округление цены по правилам биржи"""
        try:
            price_decimal = Decimal(str(price))
            tick_decimal = Decimal(tick_size)
            rounded = (price_decimal / tick_decimal).quantize(Decimal("1"), rounding=ROUND_DOWN) * tick_decimal
            return float(rounded)
        except Exception as e:
            logger.error(f"Ошибка округления цены {price}: {e}", exc_info=True)
            return 0.0

    def place_market_order(self, symbol: str, side: str, qty: float, stop_loss: float) -> str | None:
        """Открытие рыночной позиции с Stop Loss"""
        try:
            params = {
                "category": "linear",
                "symbol": symbol,
                "side": side,
                "orderType": "Market",
                "qty": str(qty),
                "stopLoss": str(stop_loss),
                "slTriggerBy": "MarkPrice",
                "tpslMode": "Full",
                "slOrderType": "Market"
            }

            resp = self.client.place_order(**params)

            if not isinstance(resp, dict) or resp.get("retCode") != 0:
                logger.error(f"Ошибка открытия позиции {symbol}: {resp}")
                return None

            order_id = resp.get("result", {}).get("orderId", "")
            direction = "Long" if side == "Buy" else "Short"
            logger.info(
                f"Позиция {direction} по {symbol} успешно выставлена: qty={qty}, SL={stop_loss}, orderId={order_id}")
            return order_id

        except Exception as e:
            logger.error(f"Ошибка открытия позиции {symbol}: {e}", exc_info=True)
            return None

    def place_batch_limit_orders(self, symbol: str, side: str, orders: list[dict[str, float]]) -> bool:
        """Выставление батча лимитных reduce-only ордеров для TP"""
        try:
            if not orders:
                logger.warning("Пустой список ордеров для батча")
                return False

            request = []
            for order in orders:
                request.append({
                    "category": "linear",
                    "symbol": symbol,
                    "side": side,
                    "orderType": "Limit",
                    "price": str(order["price"]),
                    "qty": str(order["qty"]),
                    "timeInForce": "GTC",
                    "reduceOnly": True
                })

            resp = self.client.place_batch_order(category="linear", request=request)

            if not isinstance(resp, dict) or resp.get("retCode") != 0:
                logger.error(f"Ошибка батч-выставления TP для {symbol}: {resp}")
                return False

            logger.info(f"Все {len(orders)}TP успешно выставлены для {symbol}")
            return True

        except Exception as e:
            logger.error(f"Ошибка батч-выставления TP для {symbol}: {e}", exc_info=True)
            return False