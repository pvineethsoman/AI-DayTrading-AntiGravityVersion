from src.strategies.base import Strategy, Signal, SignalType
from src.models.domain import Stock

class SMACrossoverStrategy(Strategy):
    """
    Simple Moving Average Crossover Strategy.
    Buy when SMA 50 crosses above SMA 200 (Golden Cross).
    Sell when SMA 50 crosses below SMA 200 (Death Cross).
    """
    
    def __init__(self):
        super().__init__(name="SMA Crossover")

    def analyze(self, stock: Stock) -> Signal:
        if not stock.indicators or stock.indicators.sma_50 is None or stock.indicators.sma_200 is None:
            return Signal(symbol=stock.symbol, signal_type=SignalType.HOLD, reason="Insufficient data for SMA")

        sma_50 = stock.indicators.sma_50
        sma_200 = stock.indicators.sma_200
        
        # Simple logic: just check current relationship
        # In a real system, we'd check if the cross happened *just now* (requires previous state)
        # For this iteration, we'll be state-less and just indicate trend
        
        if sma_50 > sma_200:
            return Signal(
                symbol=stock.symbol, 
                signal_type=SignalType.BUY, 
                strength=0.8, 
                reason=f"Golden Cross: SMA50 ({sma_50:.2f}) > SMA200 ({sma_200:.2f})"
            )
        elif sma_50 < sma_200:
            return Signal(
                symbol=stock.symbol, 
                signal_type=SignalType.SELL, 
                strength=0.8, 
                reason=f"Death Cross: SMA50 ({sma_50:.2f}) < SMA200 ({sma_200:.2f})"
            )
            
        return Signal(symbol=stock.symbol, signal_type=SignalType.HOLD)
