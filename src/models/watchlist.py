from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class WatchlistItem(BaseModel):
    """Watchlist item for auto-trading."""
    symbol: str
    auto_trade: bool = Field(default=True, description="Enable automatic trading for this symbol")
    last_analyzed: Optional[datetime] = None
    last_signal: Optional[str] = None  # "BUY", "SELL", "HOLD"
