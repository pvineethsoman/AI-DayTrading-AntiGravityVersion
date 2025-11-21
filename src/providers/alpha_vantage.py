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
        
        # Fallback to Streamlit Secrets
        if not self.api_key:
            try:
                import streamlit as st
                if hasattr(st, "secrets"):
                    self.api_key = st.secrets.get("ALPHA_VANTAGE_API_KEY")
            except Exception:
                pass
        if self.api_key:
            self.ts = TimeSeries(key=self.api_key, output_format='pandas')
        else:
            self.ts = None

    @RateLimiter(max_calls=5, period=60)
    def get_stock_data(self, symbol: str, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> Stock:
        if not self.ts:
            raise ValueError("Alpha Vantage API key is missing")
            
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

    @RateLimiter(max_calls=5, period=60)
    def get_news_sentiment(self, symbol: Optional[str] = None, limit: int = 5) -> list:
        """Fetches news sentiment data."""
        if not self.api_key:
            return []
            
        import requests
        url = f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT&apikey={self.api_key}&limit={limit}"
        if symbol:
            url += f"&tickers={symbol}"
            
        try:
            response = requests.get(url)
            data = response.json()
            if "feed" not in data:
                # Log error or rate limit message
                if "Note" in data:
                    print(f"Alpha Vantage Limit: {data['Note']}")
                return []
            return data.get('feed', [])
        except Exception as e:
            print(f"Error fetching news: {e}")
            return []

    @RateLimiter(max_calls=5, period=60)
    def get_fundamentals(self, symbol: str) -> dict:
        """Fetches fundamental data (Overview)."""
        if not self.api_key:
            return {}
            
        import requests
        url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={symbol}&apikey={self.api_key}"
        
        try:
            response = requests.get(url)
            data = response.json()
            
            if not data or "Symbol" not in data:
                return {}
                
            # Extract key metrics
            return {
                "PE_Ratio": float(data.get("PERatio", 0) or 0),
                "EPS": float(data.get("EPS", 0) or 0),
                "Market_Cap": float(data.get("MarketCapitalization", 0) or 0),
                "Book_Value": float(data.get("BookValue", 0) or 0),
                "Dividend_Yield": float(data.get("DividendYield", 0) or 0),
                "Profit_Margin": float(data.get("ProfitMargin", 0) or 0),
                "Sector": data.get("Sector", "Unknown"),
                "Industry": data.get("Industry", "Unknown")
            }
        except Exception as e:
            print(f"Error fetching fundamentals: {e}")
            return {}

    def get_current_price(self, symbol: str) -> float:
        # Global Quote endpoint for current price
        # Note: This requires a separate call and might hit rate limits on free tier
        # For simplicity in this iteration, we might just get the last close from daily
        # But let's try to do it right if we can, or just return the last close from get_stock_data
        # To keep it simple and robust for now without extra dependencies/calls:
        data, _ = self.ts.get_quote_endpoint(symbol=symbol)
        return float(data['05. price'][0])
