from typing import List, Type
from datetime import datetime
import pandas as pd
from src.models.domain import Stock, Price
from src.models.trading import OrderSide
from src.strategies.base import Strategy, SignalType
from src.execution.paper_engine import PaperTradingEngine
from src.analysis.technical import TechnicalAnalyzer

class Backtester:
    """Runs a strategy against historical data."""
    
    def __init__(self, strategy: Strategy, initial_cash: float = 100000.0):
        self.strategy = strategy
        self.engine = PaperTradingEngine(initial_cash=initial_cash)
        
    def run(self, stock_data: Stock):
        """
        Simulates trading over the historical data of the stock.
        """
        print(f"Starting backtest for {self.strategy.name} on {stock_data.symbol}")
        
        # We need to iterate through history, calculating indicators at each step
        # to avoid look-ahead bias. For simplicity/performance in this MVP,
        # we might pre-calculate indicators but only "reveal" them sequentially.
        # However, TechnicalAnalyzer calculates on the whole history.
        # So we will simulate by slicing the history.
        
        full_history = stock_data.history
        if not full_history:
            print("No history to backtest.")
            return

        # Sort by timestamp
        full_history.sort(key=lambda x: x.timestamp)
        
        # We need at least enough data for the longest indicator (e.g. 200 days)
        min_periods = 200
        
        for i in range(min_periods, len(full_history)):
            # Slice history up to current point
            current_slice = full_history[:i+1]
            current_price_point = current_slice[-1]
            
            # Create a temporary stock object for analysis
            # Convert history to dicts to avoid Pydantic class mismatch during reloading
            temp_stock = Stock(
                symbol=stock_data.symbol,
                history=[p.model_dump() for p in current_slice],
                current_price=current_price_point.close
            )
            
            # Calculate indicators for this slice
            temp_stock.indicators = TechnicalAnalyzer.calculate_indicators(temp_stock)
            
            # Get Signal
            signal = self.strategy.analyze(temp_stock)
            
            # Execute Signal
            if signal.signal_type == SignalType.BUY:
                # Buy logic: e.g., buy 10 shares
                self.engine.place_order(stock_data.symbol, OrderSide.BUY, 10)
            elif signal.signal_type == SignalType.SELL:
                # Sell logic: e.g., sell all shares
                position = self.engine.portfolio.positions.get(stock_data.symbol)
                if position:
                    self.engine.place_order(stock_data.symbol, OrderSide.SELL, position.quantity)
            
            # Process orders with current price
            self.engine.process_orders({stock_data.symbol: current_price_point.close})
            
        self._print_results(stock_data)

    def _print_results(self, stock: Stock):
        portfolio_value = self.engine.portfolio.total_value
        initial_cash = 100000.0 # Should match init
        return_pct = ((portfolio_value - initial_cash) / initial_cash) * 100
        
        print("-" * 30)
        print(f"Backtest Results: {self.strategy.name}")
        print(f"Initial Value: ${initial_cash:,.2f}")
        print(f"Final Value:   ${portfolio_value:,.2f}")
        print(f"Total Return:  {return_pct:.2f}%")
        print(f"Total Trades:  {len(self.engine.trades)}")
        print("-" * 30)
