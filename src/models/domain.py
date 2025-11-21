from datetime import datetime
from typing import Dict, Optional, List
from pydantic import BaseModel, Field

class Price(BaseModel):
    """Represents a single price point for a stock."""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    adjusted_close: Optional[float] = None

class TechnicalIndicators(BaseModel):
    """Container for technical analysis indicators."""
    rsi: Optional[float] = Field(None, description="Relative Strength Index")
    macd: Optional[float] = Field(None, description="Moving Average Convergence Divergence")
    macd_signal: Optional[float] = Field(None, description="MACD Signal Line")
    macd_hist: Optional[float] = Field(None, description="MACD Histogram")
    sma_50: Optional[float] = Field(None, description="50-day Simple Moving Average")
    sma_200: Optional[float] = Field(None, description="200-day Simple Moving Average")
    ema_12: Optional[float] = Field(None, description="12-day Exponential Moving Average")
    ema_26: Optional[float] = Field(None, description="26-day Exponential Moving Average")

class Stock(BaseModel):
    """Represents a stock with its price history and analysis."""
    symbol: str
    company_name: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    current_price: Optional[float] = None
    history: List[Price] = []
    indicators: Optional[TechnicalIndicators] = None
    valuation_metrics: Dict[str, float] = {}
    last_updated: datetime = Field(default_factory=datetime.now)

    class Config:
        from_attributes = True
