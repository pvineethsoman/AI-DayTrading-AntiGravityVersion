import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from pathlib import Path

from src.models.risk import RiskSettings

# Get project root directory
PROJECT_ROOT = Path(__file__).parent.parent
ENV_FILE = PROJECT_ROOT / ".env"

# Explicitly load dotenv to ensure keys are set
from dotenv import load_dotenv
print(f"Loading .env from: {ENV_FILE}")
load_dotenv(ENV_FILE)

class Settings(BaseSettings):
    """Application settings."""
    
    model_config = ConfigDict(
        env_file=str(ENV_FILE),
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

# Debug: Print loaded keys (masked)
print("--- CONFIG DEBUG ---")
print(f"GEMINI_KEY: {'*' * 5 if settings.GEMINI_API_KEY else 'MISSING'}")
print(f"OPENAI_KEY: {'*' * 5 if settings.OPENAI_API_KEY else 'MISSING'}")
print(f"ALPACA_KEY: {'*' * 5 if settings.ALPACA_API_KEY else 'MISSING'}")
print("--------------------")
