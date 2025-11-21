from typing import Optional
from datetime import datetime
from src.models.domain import Stock
from src.providers.base import StockDataProvider
from src.providers.yahoo import YahooFinanceProvider
from src.analysis.technical import TechnicalAnalyzer
from src.infrastructure.cache import RedisCache
import logging

logger = logging.getLogger(__name__)

from src.config import settings
from src.providers.alpha_vantage import AlphaVantageProvider

class MarketDataService:
    """Service to fetch market data with caching and analysis."""
    
    def __init__(self, provider: StockDataProvider = None, cache: RedisCache = None):
        if provider:
            self.provider = provider
        elif settings.ALPHA_VANTAGE_API_KEY:
            logger.info("Using Alpha Vantage Provider")
            self.provider = AlphaVantageProvider(api_key=settings.ALPHA_VANTAGE_API_KEY)
        else:
            logger.info("Using Yahoo Finance Provider (Fallback)")
            self.provider = YahooFinanceProvider()
            
        self.cache = cache or RedisCache(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB)
        
    def get_stock_analysis(self, symbol: str, force_refresh: bool = False) -> Stock:
        """
        Get stock data with full analysis. Tries cache first.
        """
        cache_key = f"stock_analysis:{symbol}"
        
        if not force_refresh:
            try:
                cached_data = self.cache.get(cache_key)
                if cached_data:
                    logger.info(f"Cache hit for {symbol}")
                    return Stock.model_validate(cached_data)
            except Exception as e:
                logger.warning(f"Cache read failed: {e}")
                
        logger.info(f"Fetching fresh data for {symbol}")
        
        try:
            # Fetch fresh data
            stock = self.provider.get_stock_data(symbol)
            
            # Run analysis
            stock.indicators = TechnicalAnalyzer.calculate_indicators(stock)
            
            # Cache result (serialize to dict/json)
            try:
                self.cache.set(cache_key, stock.model_dump(mode='json'), expire=300) # 5 min cache
            except Exception as e:
                logger.warning(f"Cache write failed: {e}")
            
            return stock
            
        except Exception as e:
            logger.error(f"Failed to fetch/analyze stock {symbol}: {e}")
            raise e
