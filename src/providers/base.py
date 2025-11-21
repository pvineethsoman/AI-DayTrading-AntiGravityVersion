from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime
from src.models.domain import Stock, Price

class StockDataProvider(ABC):
    """Abstract base class for stock data providers."""

    @abstractmethod
    def get_stock_data(self, symbol: str, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> Stock:
        """
        Fetches stock data for the given symbol.
        
        Args:
            symbol: The stock ticker symbol.
            start_date: The start date for historical data.
            end_date: The end date for historical data.
            
        Returns:
            A Stock object populated with data.
        """
        pass
    
    @abstractmethod
    def get_current_price(self, symbol: str) -> float:
        """
        Fetches the current price for the given symbol.
        
        Args:
            symbol: The stock ticker symbol.
            
        Returns:
            The current price as a float.
        """
        pass
