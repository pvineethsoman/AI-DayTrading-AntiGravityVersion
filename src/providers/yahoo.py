import yfinance as yf
from datetime import datetime
from typing import Optional
from src.models.domain import Stock, Price
from src.providers.base import StockDataProvider

class YahooFinanceProvider(StockDataProvider):
    """Implementation of StockDataProvider using yfinance."""

    def get_stock_data(self, symbol: str, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> Stock:
        ticker = yf.Ticker(symbol)
        
        # Fetch history
        if start_date and end_date:
            history = ticker.history(start=start_date, end=end_date)
        elif start_date:
            history = ticker.history(start=start_date)
        else:
            history = ticker.history(period="1y")
            
        prices = []
        for index, row in history.iterrows():
            prices.append(Price(
                timestamp=index,
                open=row['Open'],
                high=row['High'],
                low=row['Low'],
                close=row['Close'],
                volume=row['Volume'],
                adjusted_close=row.get('Adj Close') # yfinance might not always return this in history depending on settings
            ))
            
        # Get info
        info = ticker.info
        
        return Stock(
            symbol=symbol,
            company_name=info.get('longName'),
            sector=info.get('sector'),
            industry=info.get('industry'),
            current_price=info.get('currentPrice') or info.get('regularMarketPrice'),
            history=prices
        )

    def get_current_price(self, symbol: str) -> float:
        ticker = yf.Ticker(symbol)
        # Try fast access first
        price = ticker.fast_info.last_price
        if price:
            return price
            
        # Fallback to regular info
        info = ticker.info
        return info.get('currentPrice') or info.get('regularMarketPrice') or 0.0
