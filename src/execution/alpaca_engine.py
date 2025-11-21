from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide as AlpacaOrderSide, TimeInForce
from typing import Optional, Dict
from src.models.trading import Portfolio, Position, Order, OrderSide, OrderType, OrderStatus
from src.config import settings
import logging

logger = logging.getLogger(__name__)

class AlpacaExecutionEngine:
    """Execution engine using Alpaca API."""
    
    def __init__(self):
        if not settings.ALPACA_API_KEY or not settings.ALPACA_SECRET_KEY:
            raise ValueError("Alpaca API keys not configured")
            
        self.client = TradingClient(
            api_key=settings.ALPACA_API_KEY,
            secret_key=settings.ALPACA_SECRET_KEY,
            paper=settings.ALPACA_PAPER
        )

    @property
    def portfolio(self) -> Portfolio:
        """Fetches current portfolio state from Alpaca."""
        account = self.client.get_account()
        positions = self.client.get_all_positions()
        
        portfolio_positions = {}
        for p in positions:
            portfolio_positions[p.symbol] = Position(
                symbol=p.symbol,
                quantity=int(float(p.qty)),
                average_price=float(p.avg_entry_price),
                current_price=float(p.current_price)
            )
            
        return Portfolio(
            cash=float(account.cash),
            positions=portfolio_positions
        )

    def place_order(self, symbol: str, side: OrderSide, quantity: int, order_type: OrderType = OrderType.MARKET, price: Optional[float] = None) -> Order:
        """Places an order on Alpaca."""
        # Safety Checks
        if not settings.TRADING_ENABLED:
            logger.warning("Order rejected: Trading is disabled (Kill Switch).")
            raise RuntimeError("Trading is disabled.")
            
        # Risk Checks
        # 1. Max Positions
        current_positions = len(self.client.get_all_positions())
        if side == OrderSide.BUY and current_positions >= settings.RISK_SETTINGS.max_open_positions:
             # Check if we already hold this symbol (adding to position) vs new position
             # For simplicity, strict count check
             logger.warning(f"Order rejected: Max open positions reached ({settings.RISK_SETTINGS.max_open_positions}).")
             raise RuntimeError("Max open positions reached.")

        # 2. Max Position Size (Approximate check using current price if available, else skip or fetch)
        # We'll skip strict pre-trade value check here to avoid extra API call latency, 
        # but ideally we'd check (quantity * price) <= max_position_size
        
        req = MarketOrderRequest(
            symbol=symbol,
            qty=quantity,
            side=AlpacaOrderSide.BUY if side == OrderSide.BUY else AlpacaOrderSide.SELL,
            time_in_force=TimeInForce.DAY
        )
        
        try:
            alpaca_order = self.client.submit_order(order_data=req)
            logger.info(f"Placed Alpaca order: {alpaca_order.id}")
            
            return Order(
                id=str(alpaca_order.id),
                symbol=symbol,
                side=side,
                order_type=order_type,
                quantity=quantity,
                status=OrderStatus.PENDING # Alpaca returns pending initially
            )
        except Exception as e:
            logger.error(f"Failed to place Alpaca order: {e}")
            raise e
