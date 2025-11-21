import sys
import os
import logging

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from src.services.market_data import MarketDataService
from src.providers.yahoo import YahooFinanceProvider
from src.infrastructure.cache import RedisCache
import redis

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    print("Starting verification...")
    
    # 1. Test Redis Connection
    try:
        cache = RedisCache()
        if cache.exists("test_key"):
            pass
        print("✅ Redis connection successful")
    except redis.ConnectionError:
        print("⚠️ Redis not running. Caching will fail. Please start Redis.")
        # Continue without cache for testing provider
        cache = None

    # 2. Test Yahoo Provider via Service
    try:
        service = MarketDataService(provider=YahooFinanceProvider(), cache=cache)
        symbol = "AAPL"
        print(f"Fetching data for {symbol}...")
        stock = service.get_stock_analysis(symbol)
        
        print(f"✅ Data fetched for {stock.company_name} ({stock.symbol})")
        print(f"   Current Price: ${stock.current_price}")
        
        if stock.indicators:
            print("✅ Technical Indicators calculated:")
            print(f"   RSI: {stock.indicators.rsi:.2f}")
            print(f"   MACD: {stock.indicators.macd:.2f}")
            print(f"   SMA 50: {stock.indicators.sma_50:.2f}")
        else:
            print("❌ Technical Indicators missing")
            
    except Exception as e:
        print(f"❌ Error fetching data: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
