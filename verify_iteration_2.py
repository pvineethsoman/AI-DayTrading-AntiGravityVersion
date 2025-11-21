import sys
import os
import logging
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from src.models.domain import Stock, Price
from src.strategies.sma_crossover import SMACrossoverStrategy
from src.strategies.rsi_reversion import RSIMeanReversionStrategy
from src.backtesting.engine import Backtester
from src.providers.yahoo import YahooFinanceProvider

logging.basicConfig(level=logging.INFO)

def main():
    print("Starting Iteration 2 Verification...")
    
    # 1. Fetch Real Data (or Mock if offline)
    symbol = "AAPL"
    print(f"Fetching 1y history for {symbol}...")
    provider = YahooFinanceProvider()
    try:
        stock = provider.get_stock_data(symbol)
        if not stock.history:
            print("❌ No history found. Cannot backtest.")
            return
    except Exception as e:
        print(f"❌ Error fetching data: {e}")
        return

    # 2. Run SMA Backtest
    print("\n--- Running SMA Crossover Backtest ---")
    sma_strategy = SMACrossoverStrategy()
    sma_backtester = Backtester(sma_strategy)
    sma_backtester.run(stock)
    
    # 3. Run RSI Backtest
    print("\n--- Running RSI Mean Reversion Backtest ---")
    rsi_strategy = RSIMeanReversionStrategy()
    rsi_backtester = Backtester(rsi_strategy)
    rsi_backtester.run(stock)

if __name__ == "__main__":
    main()
