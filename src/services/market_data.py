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
        self.yahoo_provider = YahooFinanceProvider()
        self.av_provider = None
        
        if provider:
            self.primary_provider = provider
        elif settings.ALPHA_VANTAGE_API_KEY:
            logger.info("Using Alpha Vantage Provider as Primary")
            self.av_provider = AlphaVantageProvider(api_key=settings.ALPHA_VANTAGE_API_KEY)
            self.primary_provider = self.av_provider
        else:
            logger.info("Using Yahoo Finance Provider as Primary")
            self.primary_provider = self.yahoo_provider
            
        self.cache = cache or RedisCache(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB)
        
    def get_stock_analysis(self, symbol: str, force_refresh: bool = False) -> Stock:
        """
        Get stock data with full analysis. Tries cache first.
        Implements failover: Alpha Vantage -> Yahoo Finance.
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
        
        stock = None
        try:
            # Try Primary Provider
            stock = self.primary_provider.get_stock_data(symbol)
            
            # If Primary is Alpha Vantage, try to fetch rich data (Fundamentals & Sentiment)
            if self.primary_provider == self.av_provider:
                try:
                    # Fundamentals
                    stock.fundamentals = self.av_provider.get_fundamentals(symbol)
                    
                    # Sentiment
                    sentiment_data = self.av_provider.get_news_sentiment(symbol)
                    if sentiment_data:
                        # Calculate average sentiment score
                        scores = [float(item.get('overall_sentiment_score', 0)) for item in sentiment_data]
                        stock.sentiment_score = sum(scores) / len(scores) if scores else 0
                        # Use the summary of the most relevant/recent news
                        stock.sentiment_summary = sentiment_data[0].get('summary', '') if sentiment_data else None
                        
                except Exception as e:
                    logger.warning(f"Failed to fetch rich data from Alpha Vantage: {e}")
                    
        except Exception as e:
            logger.warning(f"Primary provider failed for {symbol}: {e}")
            
            # Failover to Yahoo if primary was not Yahoo
            if self.primary_provider != self.yahoo_provider:
                logger.info(f"Failing over to Yahoo Finance for {symbol}")
                try:
                    stock = self.yahoo_provider.get_stock_data(symbol)
                except Exception as ye:
                    logger.error(f"Fallback provider also failed: {ye}")
                    raise ye
            else:
                raise e
        
        if not stock:
            raise Exception(f"Failed to fetch data for {symbol}")

        try:
            # Run analysis
            stock.indicators = TechnicalAnalyzer.calculate_indicators(stock)
            
            # Cache result (serialize to dict/json)
            try:
                self.cache.set(cache_key, stock.model_dump(mode='json'), expire=300) # 5 min cache
            except Exception as e:
                logger.warning(f"Cache write failed: {e}")
            
            return stock
            
        except Exception as e:
            logger.error(f"Analysis failed for {symbol}: {e}")
            raise e

    def get_market_news(self, symbol: str = None, limit: int = 5) -> list:
        """Fetches market news, preferring Alpha Vantage if available."""
        if self.av_provider:
            try:
                return self.av_provider.get_news_sentiment(symbol, limit)
            except Exception as e:
                logger.warning(f"AV News failed: {e}")
        
        # Fallback could go here (e.g. Yahoo News RSS)
        return []
