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
        api_key = settings.ALPACA_API_KEY
        secret_key = settings.ALPACA_SECRET_KEY
        paper = settings.ALPACA_PAPER
        
        # Direct Streamlit Secrets Access (Fallback)
        if not api_key or not secret_key:
            try:
                import streamlit as st
                if hasattr(st, "secrets"):
                    if not api_key:
                        api_key = st.secrets.get("ALPACA_API_KEY")
                    if not secret_key:
                        secret_key = st.secrets.get("ALPACA_SECRET_KEY")
                    
                    # Handle paper mode override from secrets if needed
                    if "ALPACA_PAPER" in st.secrets:
                        paper_val = st.secrets.get("ALPACA_PAPER")
                        if isinstance(paper_val, str):
                            paper = paper_val.lower() == "true"
                        else:
                            paper = bool(paper_val)
            except Exception:
                pass

        if not api_key or not secret_key:
            raise ValueError("Alpaca API keys not configured")
            
        self.client = TradingClient(
            api_key=api_key,
            secret_key=secret_key,
            paper=paper
        )

    def get_account(self):
        """Fetches account information."""
        return self.client.get_account()

    def get_positions(self):
        """Fetches all open positions."""
        return self.client.get_all_positions()

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
