from datetime import datetime
from typing import List, Dict, Optional
from enum import Enum
from pydantic import BaseModel, Field

class OrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"

class OrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"

class OrderStatus(str, Enum):
    PENDING = "PENDING"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"

class Order(BaseModel):
    """Represents a trading order."""
    id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: int
    price: Optional[float] = None # Required for LIMIT orders
    status: OrderStatus = OrderStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.now)
    filled_at: Optional[datetime] = None
    filled_price: Optional[float] = None

class Trade(BaseModel):
    """Represents a completed trade."""
    id: str
    order_id: str
    symbol: str
    side: OrderSide
    quantity: int
    price: float
    timestamp: datetime
    commission: float = 0.0

class Position(BaseModel):
    """Represents a current holding."""
    symbol: str
    quantity: int
    average_price: float
    current_price: float
    
    @property
    def market_value(self) -> float:
        return self.quantity * self.current_price
    
    @property
    def unrealized_pnl(self) -> float:
        return (self.current_price - self.average_price) * self.quantity

class Portfolio(BaseModel):
    """Represents the trader's portfolio."""
    cash: float
    positions: Dict[str, Position] = {}
    
    @property
    def total_value(self) -> float:
        return self.cash + sum(p.market_value for p in self.positions.values())
