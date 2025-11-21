import google.generativeai as genai
from openai import OpenAI
from src.models.domain import Stock
from src.config import settings
from src.infrastructure.throttling import RateLimiter
from src.analysis.prompts import PERSONA_PROMPTS
import logging

logger = logging.getLogger(__name__)

class AIAnalyst:
    """Uses Google Gemini (Primary) and OpenAI (Failover) to analyze stock data."""
    
    def __init__(self):
        # Try to get keys from settings, or fallback to st.secrets directly
        gemini_key = settings.GEMINI_API_KEY
        openai_key = settings.OPENAI_API_KEY
        
        # Direct Streamlit Secrets Access (Fallback)
        if not gemini_key:
            try:
                import streamlit as st
                if hasattr(st, "secrets"):
                    gemini_key = st.secrets.get("GEMINI_API_KEY")
            except Exception: 
                pass
            
        if not openai_key:
            try:
                import streamlit as st
                if hasattr(st, "secrets"):
                    openai_key = st.secrets.get("OPENAI_API_KEY")
            except Exception: 
                pass

        # Gemini Setup
        if gemini_key:
            genai.configure(api_key=gemini_key)
            self.gemini_model = genai.GenerativeModel('gemini-pro')
        else:
            logger.warning("Gemini API key not configured.")
            self.gemini_model = None
            
        # OpenAI Setup
        if openai_key:
            self.openai_client = OpenAI(api_key=openai_key)
        else:
            logger.warning("OpenAI API key not configured.")
            self.openai_client = None

    @RateLimiter(max_calls=60, period=60)
    def analyze_stock(self, stock: Stock, persona: str = "General") -> str:
        """Generates a text analysis of the stock using the selected persona."""
        
        if not stock.indicators:
            return "Insufficient data for AI analysis."
            
        # Prepare Prompt
        prompt_template = PERSONA_PROMPTS.get(persona, PERSONA_PROMPTS["General"])
        
        # Safe formatting
        try:
            prompt = prompt_template.format(
                symbol=stock.symbol,
                company_name=stock.company_name or "Unknown",
                current_price=f"{stock.current_price:.2f}" if stock.current_price else "N/A",
                rsi=f"{stock.indicators.rsi:.2f}" if stock.indicators.rsi else "N/A",
                macd=f"{stock.indicators.macd:.2f}" if stock.indicators.macd else "N/A",
                sma_50=f"{stock.indicators.sma_50:.2f}" if stock.indicators.sma_50 else "N/A",
                sma_200=f"{stock.indicators.sma_200:.2f}" if stock.indicators.sma_200 else "N/A",
                pe_ratio=stock.fundamentals.get('PE_Ratio', 'N/A'),
                eps=stock.fundamentals.get('EPS', 'N/A'),
                market_cap=stock.fundamentals.get('Market_Cap', 'N/A'),
                sector=stock.fundamentals.get('Sector', 'N/A'),
                sentiment_score=f"{stock.sentiment_score:.2f}" if stock.sentiment_score is not None else "N/A",
                sentiment_summary=stock.sentiment_summary or "No significant news."
            )
        except Exception as e:
            logger.error(f"Error formatting prompt: {e}")
            return "Error preparing analysis data."
        
        # 1. Try Gemini (Primary)
        gemini_error = None
        if self.gemini_model:
            try:
                response = self.gemini_model.generate_content(prompt)
                if response.text:
                    return f"**[Gemini - {persona}]**: {response.text}"
            except Exception as e:
                gemini_error = str(e)
                logger.warning(f"Gemini analysis failed: {e}. Failing over to OpenAI...")
        
        # 2. Try OpenAI (Failover)
        if self.openai_client:
            try:
                response = self.openai_client.chat.completions.create(
                    model="gpt-4o", # Using GPT-4o for best results
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=150
                )
                return f"**[OpenAI - {persona}]**: {response.choices[0].message.content}"
            except Exception as e:
                logger.error(f"OpenAI analysis failed: {e}")
                return f"Error: Both AI models failed.\n\nGemini Error: {gemini_error}\nOpenAI Error: {e}"
                
        # If we get here, it means:
        # 1. No models configured OR
        # 2. Gemini failed and OpenAI not configured
        
        if gemini_error:
            return f"**AI Analysis Failed**\n\nGemini Error: {gemini_error}\n\n(OpenAI failover not configured)"
            
        return """**AI Analysis Unavailable**

No AI models are configured. To enable AI analysis, add at least one API key to your `.env` file or Streamlit Secrets:

- `GEMINI_API_KEY` - Get from https://makersuite.google.com/app/apikey
- `OPENAI_API_KEY` - Get from https://platform.openai.com/api-keys

Then restart the application."""

