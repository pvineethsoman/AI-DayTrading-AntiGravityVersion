from pydantic import BaseModel, Field

class RiskSettings(BaseModel):
    """Risk management settings."""
    max_position_size: float = Field(default=10000.0, description="Maximum capital allocated to a single position")
    max_daily_loss: float = Field(default=500.0, description="Maximum allowable loss per day before stopping trading")
    max_drawdown_pct: float = Field(default=0.02, description="Maximum portfolio drawdown percentage (e.g., 0.02 for 2%)")
    max_open_positions: int = Field(default=5, description="Maximum number of concurrent open positions")
