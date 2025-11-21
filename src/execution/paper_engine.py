import uuid
from datetime import datetime
from typing import List, Optional
from src.models.trading import Portfolio, Order, Trade, Position, OrderSide, OrderType, OrderStatus
from src.models.domain import Stock

class PaperTradingEngine:
    """Simulates trade execution without real money."""
    
    def __init__(self, initial_cash: float = 100000.0):
        self.portfolio = Portfolio(cash=initial_cash)
        self.orders: List[Order] = []
        self.trades: List[Trade] = []

    def get_account(self):
        """Returns a mock account object matching Alpaca's structure."""
        from types import SimpleNamespace
        equity = self.portfolio.total_value
        return SimpleNamespace(
            equity=equity,
            buying_power=self.portfolio.cash,
            last_equity=equity, # Mock, could track history
            status="ACTIVE (PAPER)"
        )

    def get_positions(self):
        """Returns positions matching Alpaca's structure."""
        from types import SimpleNamespace
        result = []
        for symbol, pos in self.portfolio.positions.items():
            mv = pos.market_value
            pnl = pos.unrealized_pnl
            cost = pos.quantity * pos.average_price
            pnlpc = (pnl / cost) if cost else 0
            
            result.append(SimpleNamespace(
                symbol=symbol,
                qty=pos.quantity,
                market_value=mv,
                unrealized_pl=pnl,
                unrealized_plpc=pnlpc,
                current_price=pos.current_price,
                avg_entry_price=pos.average_price
            ))
        return result

    def place_order(self, symbol: str, side: OrderSide, quantity: int, order_type: OrderType = OrderType.MARKET, price: Optional[float] = None) -> Order:
        order = Order(
            id=str(uuid.uuid4()),
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price
        )
        self.orders.append(order)
        
        # In paper trading, we try to fill immediately if MARKET, or check price if LIMIT
        # For simplicity in this iteration, we'll assume immediate fill at "current price" provided externally
        return order

    def process_orders(self, current_prices: dict[str, float]):
        """
        Process pending orders based on current market prices.
        """
        for order in self.orders:
            if order.status == OrderStatus.PENDING:
                current_price = current_prices.get(order.symbol)
                if not current_price:
                    continue
                    
                should_fill = False
                fill_price = current_price
                
                if order.order_type == OrderType.MARKET:
                    should_fill = True
                elif order.order_type == OrderType.LIMIT:
                    if order.side == OrderSide.BUY and current_price <= order.price:
                        should_fill = True
                        fill_price = order.price # Or current_price, usually limit price is better or equal
                    elif order.side == OrderSide.SELL and current_price >= order.price:
                        should_fill = True
                        fill_price = order.price
                
                if should_fill:
                    self._execute_trade(order, fill_price)

    def _execute_trade(self, order: Order, price: float):
        cost = price * order.quantity
        
        if order.side == OrderSide.BUY:
            if self.portfolio.cash >= cost:
                self.portfolio.cash -= cost
                self._update_position(order.symbol, order.quantity, price, OrderSide.BUY)
                order.status = OrderStatus.FILLED
                order.filled_at = datetime.now()
                order.filled_price = price
                self._record_trade(order, price)
            else:
                order.status = OrderStatus.REJECTED # Insufficient funds
                
        elif order.side == OrderSide.SELL:
            position = self.portfolio.positions.get(order.symbol)
            if position and position.quantity >= order.quantity:
                self.portfolio.cash += cost
                self._update_position(order.symbol, order.quantity, price, OrderSide.SELL)
                order.status = OrderStatus.FILLED
                order.filled_at = datetime.now()
                order.filled_price = price
                self._record_trade(order, price)
            else:
                order.status = OrderStatus.REJECTED # Insufficient shares

    def _update_position(self, symbol: str, quantity: int, price: float, side: OrderSide):
        position = self.portfolio.positions.get(symbol)
        
        if side == OrderSide.BUY:
            if position:
                total_cost = (position.quantity * position.average_price) + (quantity * price)
                total_qty = position.quantity + quantity
                position.average_price = total_cost / total_qty
                position.quantity = total_qty
                position.current_price = price
            else:
                self.portfolio.positions[symbol] = Position(
                    symbol=symbol,
                    quantity=quantity,
                    average_price=price,
                    current_price=price
                )
        elif side == OrderSide.SELL:
            if position:
                position.quantity -= quantity
                position.current_price = price
                if position.quantity == 0:
                    del self.portfolio.positions[symbol]

    def _record_trade(self, order: Order, price: float):
        trade = Trade(
            id=str(uuid.uuid4()),
            order_id=order.id,
            symbol=order.symbol,
            side=order.side,
            quantity=order.quantity,
            price=price,
            timestamp=datetime.now()
        )
        self.trades.append(trade)
