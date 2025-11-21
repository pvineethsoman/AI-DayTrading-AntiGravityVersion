import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import ConfigDict

from src.models.risk import RiskSettings

class Settings(BaseSettings):
    """Application settings."""
    
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra='ignore'
    )
    
    # App
    APP_NAME: str = "AI Day Trading Bot"
    DEBUG: bool = False
    TRADING_ENABLED: bool = True
    
    # Risk Management
    RISK_SETTINGS: RiskSettings = RiskSettings()
    
    # API Keys
    ALPHA_VANTAGE_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    ALPACA_API_KEY: Optional[str] = None
    ALPACA_SECRET_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    ALPACA_PAPER: bool = True
    
    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

settings = Settings()
