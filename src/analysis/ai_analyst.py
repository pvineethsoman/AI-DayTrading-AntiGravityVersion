import google.generativeai as genai
from src.models.domain import Stock
from src.config import settings
from src.infrastructure.throttling import RateLimiter
import logging

logger = logging.getLogger(__name__)

class AIAnalyst:
    """Uses Google Gemini to analyze stock data."""
    
    def __init__(self):
        if not settings.GEMINI_API_KEY:
            logger.warning("Gemini API key not configured. AI features disabled.")
            self.model = None
            return
            
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-pro')

    @RateLimiter(max_calls=60, period=60)
    def analyze_stock(self, stock: Stock) -> str:
        """Generates a text analysis of the stock."""
        if not self.model:
            return "AI Analysis Unavailable (Missing Key)"
            
        if not stock.indicators:
            return "Insufficient data for AI analysis."
            
        prompt = f"""
        Analyze the following stock data for {stock.symbol} ({stock.company_name}):
        Current Price: ${stock.current_price}
        
        Technical Indicators:
        - RSI: {stock.indicators.rsi:.2f}
        - MACD: {stock.indicators.macd:.2f}
        - SMA 50: {stock.indicators.sma_50:.2f}
        - SMA 200: {stock.indicators.sma_200:.2f}
        
        Fundamental Data:
        - P/E Ratio: {stock.fundamentals.get('PE_Ratio', 'N/A')}
        - EPS: {stock.fundamentals.get('EPS', 'N/A')}
        - Market Cap: {stock.fundamentals.get('Market_Cap', 'N/A')}
        - Sector: {stock.fundamentals.get('Sector', 'N/A')}
        
        News Sentiment:
        - Score: {stock.sentiment_score if stock.sentiment_score is not None else 'N/A'} (-1 to 1)
        - Summary: {stock.sentiment_summary or 'N/A'}
        
        Provide a concise trading insight (Bullish/Bearish/Neutral) and a brief reasoning based on Technicals, Fundamentals, and Sentiment.
        Keep it under 3 sentences.
        """
        
        try:
            # Check if we have a recent cached response (simulated for now, or use streamlit cache if we move this to a function)
            # For now, we'll rely on the app-level caching or just handle errors gracefully
            response = self.model.generate_content(prompt)
            if response.text:
                return response.text
            else:
                return "AI returned empty response."
        except Exception as e:
            logger.error(f"Gemini analysis failed: {e}")
            if "429" in str(e):
                return "AI Rate Limit Exceeded. Try again later."
            return f"Error generating analysis: {str(e)[:100]}..."
