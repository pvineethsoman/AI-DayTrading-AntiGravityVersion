import logging
from typing import List
from src.providers.alpha_vantage import AlphaVantageProvider
from src.config import settings
from src.infrastructure.throttling import RateLimiter

logger = logging.getLogger(__name__)

# Static list of major index constituents to scan if API fails or for rotation
SP500_TOP = ["AAPL", "MSFT", "AMZN", "NVDA", "GOOGL", "META", "TSLA", "BRK.B", "LLY", "V", "JPM"]
NASDAQ_TOP = ["ADBE", "AMD", "NFLX", "INTC", "CSCO", "CMCSA", "PEP", "COST", "TMUS", "AVGO"]

class MarketScanner:
    """Scans the market for trading opportunities."""
    
    def __init__(self, provider: AlphaVantageProvider = None):
        self.provider = provider or AlphaVantageProvider(api_key=settings.ALPHA_VANTAGE_API_KEY)
        
    @RateLimiter(max_calls=5, period=60)
    def get_top_gainers_losers(self) -> List[str]:
        """Fetches top gainers, losers, and most active from Alpha Vantage."""
        import requests
        
        if not self.provider.api_key:
            return []
            
        url = f"https://www.alphavantage.co/query?function=TOP_GAINERS_LOSERS&apikey={self.provider.api_key}"
        
        try:
            response = requests.get(url)
            data = response.json()
            
            symbols = []
            
            # Extract top 3 from each category to avoid overwhelming the system
            if "top_gainers" in data:
                symbols.extend([item['ticker'] for item in data['top_gainers'][:3]])
            if "top_losers" in data:
                symbols.extend([item['ticker'] for item in data['top_losers'][:3]])
            if "most_actively_traded" in data:
                symbols.extend([item['ticker'] for item in data['most_actively_traded'][:3]])
                
            return list(set(symbols)) # Deduplicate
            
        except Exception as e:
            logger.error(f"Error fetching top gainers/losers: {e}")
            return []

    def get_index_constituents(self) -> List[str]:
        """Returns a list of major index constituents."""
        # In a real app, we might fetch this dynamically.
        # For now, we return a combined static list.
        return list(set(SP500_TOP + NASDAQ_TOP))

    def get_scan_list(self, user_watchlist: List[str] = None) -> List[str]:
        """
        Generates a prioritized list of stocks to scan.
        Priority:
        1. User Watchlist
        2. Top Gainers/Losers (Trending)
        3. Index Constituents
        """
        scan_list = []
        
        # 1. User Watchlist
        if user_watchlist:
            scan_list.extend(user_watchlist)
            
        # 2. Trending (Top Gainers/Losers)
        # Only fetch if we have quota/capability
        try:
            trending = self.get_top_gainers_losers()
            scan_list.extend(trending)
        except Exception as e:
            logger.warning(f"Could not fetch trending stocks: {e}")
            
        # 3. Index Constituents
        # Add a few index stocks to ensure we always have something to look at
        # We can rotate these or add all. Let's add all for now, the Agent will throttle analysis.
        scan_list.extend(self.get_index_constituents())
        
        # Deduplicate and return
        # Use dict.fromkeys to preserve order (Python 3.7+)
        return list(dict.fromkeys(scan_list))
