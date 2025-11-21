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

# Load Streamlit secrets if available (for Streamlit Cloud)
try:
    import streamlit as st
    # Check if secrets are available (they might not be during build)
    if hasattr(st, "secrets") and st.secrets:
        print("Loading secrets from Streamlit Cloud...")
        for key, value in st.secrets.items():
            # Pydantic expects environment variables to be strings
            if isinstance(value, str):
                os.environ[key] = value
            # Handle nested sections (e.g. [api_keys]) if user used TOML sections
            elif isinstance(value, dict): 
                for sub_key, sub_value in value.items():
                    os.environ[sub_key] = str(sub_value)
except ImportError:
    pass
except Exception as e:
    print(f"Warning: Could not load Streamlit secrets: {e}")

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

# AGGRESSIVE FALLBACK: Manually update settings from os.environ if missing
# This ensures that if Pydantic missed the env vars for some reason, we force them in.
if not settings.GEMINI_API_KEY and "GEMINI_API_KEY" in os.environ:
    print("Forcing GEMINI_API_KEY from environment")
    settings.GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]

if not settings.OPENAI_API_KEY and "OPENAI_API_KEY" in os.environ:
    print("Forcing OPENAI_API_KEY from environment")
    settings.OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

if not settings.ALPACA_API_KEY and "ALPACA_API_KEY" in os.environ:
    print("Forcing ALPACA_API_KEY from environment")
    settings.ALPACA_API_KEY = os.environ["ALPACA_API_KEY"]

# Debug: Print loaded keys (masked)
print("--- CONFIG DEBUG ---")
print(f"Secrets Available: {bool(os.environ.get('GEMINI_API_KEY'))}")
print(f"GEMINI_KEY (Settings): {'*' * 5 if settings.GEMINI_API_KEY else 'MISSING'}")
print(f"OPENAI_KEY (Settings): {'*' * 5 if settings.OPENAI_API_KEY else 'MISSING'}")
print(f"ALPACA_KEY (Settings): {'*' * 5 if settings.ALPACA_API_KEY else 'MISSING'}")
print("--------------------")
