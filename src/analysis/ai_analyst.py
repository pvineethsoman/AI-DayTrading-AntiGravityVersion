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
        
        Provide a concise trading insight (Bullish/Bearish/Neutral) and a brief reasoning based on these indicators.
        Keep it under 3 sentences.
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Gemini analysis failed: {e}")
            return f"Error generating analysis: {e}"
