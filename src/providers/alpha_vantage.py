import os
from alpha_vantage.timeseries import TimeSeries
from datetime import datetime
from typing import Optional
from src.models.domain import Stock, Price
from src.providers.base import StockDataProvider
from src.infrastructure.throttling import RateLimiter

class AlphaVantageProvider(StockDataProvider):
    """Implementation of StockDataProvider using Alpha Vantage."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('ALPHA_VANTAGE_API_KEY')
        if not self.api_key:
            raise ValueError("Alpha Vantage API key is required")
        self.ts = TimeSeries(key=self.api_key, output_format='pandas')

    @RateLimiter(max_calls=5, period=60)
    def get_stock_data(self, symbol: str, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> Stock:
        # Alpha Vantage free tier has limits, so we'll use daily adjusted
        data, meta_data = self.ts.get_daily_adjusted(symbol=symbol, outputsize='full')
        
        # Filter by date if provided
        if start_date:
            data = data[data.index >= start_date]
        if end_date:
            data = data[data.index <= end_date]
            
        prices = []
        for index, row in data.iterrows():
            prices.append(Price(
                timestamp=index,
                open=row['1. open'],
                high=row['2. high'],
                low=row['3. low'],
                close=row['4. close'],
                volume=int(row['6. volume']),
                adjusted_close=row['5. adjusted close']
            ))
            
        # Sort prices by timestamp (Alpha Vantage returns reverse chronological)
        prices.sort(key=lambda x: x.timestamp)

        return Stock(
            symbol=symbol,
            history=prices,
            # Alpha Vantage TS endpoint doesn't give company info, would need Fundamental Data endpoint
            # For now we leave these as None or could fetch separately
        )

    def get_current_price(self, symbol: str) -> float:
        # Global Quote endpoint for current price
        # Note: This requires a separate call and might hit rate limits on free tier
        # For simplicity in this iteration, we might just get the last close from daily
        # But let's try to do it right if we can, or just return the last close from get_stock_data
        # To keep it simple and robust for now without extra dependencies/calls:
        data, _ = self.ts.get_quote_endpoint(symbol=symbol)
        return float(data['05. price'][0])
