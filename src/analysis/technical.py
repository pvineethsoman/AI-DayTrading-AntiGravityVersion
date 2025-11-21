import pandas as pd
import numpy as np
from src.models.domain import TechnicalIndicators, Stock

class TechnicalAnalyzer:
    """Calculates technical indicators for a stock."""

    @staticmethod
    def calculate_indicators(stock: Stock) -> TechnicalIndicators:
        if not stock.history:
            return TechnicalIndicators()

        df = pd.DataFrame([p.model_dump() for p in stock.history])
        df.set_index('timestamp', inplace=True)
        df.sort_index(inplace=True)
        
        close = df['close']
        
        # SMA
        sma_50 = close.rolling(window=50).mean().iloc[-1]
        sma_200 = close.rolling(window=200).mean().iloc[-1]
        
        # EMA
        ema_12 = close.ewm(span=12, adjust=False).mean().iloc[-1]
        ema_26 = close.ewm(span=26, adjust=False).mean().iloc[-1]
        
        # MACD
        macd_line = close.ewm(span=12, adjust=False).mean() - close.ewm(span=26, adjust=False).mean()
        signal_line = macd_line.ewm(span=9, adjust=False).mean()
        macd_hist = macd_line - signal_line
        
        # RSI
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return TechnicalIndicators(
            rsi=rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else None,
            macd=macd_line.iloc[-1] if not pd.isna(macd_line.iloc[-1]) else None,
            macd_signal=signal_line.iloc[-1] if not pd.isna(signal_line.iloc[-1]) else None,
            macd_hist=macd_hist.iloc[-1] if not pd.isna(macd_hist.iloc[-1]) else None,
            sma_50=sma_50 if not pd.isna(sma_50) else None,
            sma_200=sma_200 if not pd.isna(sma_200) else None,
            ema_12=ema_12 if not pd.isna(ema_12) else None,
            ema_26=ema_26 if not pd.isna(ema_26) else None
        )
