import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings."""
    
    # App
    APP_NAME: str = "AI Day Trading Bot"
    DEBUG: bool = False
    
    # API Keys
    ALPHA_VANTAGE_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    ALPACA_API_KEY: Optional[str] = None
    ALPACA_SECRET_KEY: Optional[str] = None
    ALPACA_PAPER: bool = True
    
    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
