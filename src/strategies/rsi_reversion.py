from src.strategies.base import Strategy, Signal, SignalType
from src.models.domain import Stock

class RSIMeanReversionStrategy(Strategy):
    """
    RSI Mean Reversion Strategy.
    Buy when RSI < 30 (Oversold).
    Sell when RSI > 70 (Overbought).
    """
    
    def __init__(self, oversold_threshold: float = 30.0, overbought_threshold: float = 70.0):
        super().__init__(name="RSI Mean Reversion")
        self.oversold_threshold = oversold_threshold
        self.overbought_threshold = overbought_threshold

    def analyze(self, stock: Stock) -> Signal:
        if not stock.indicators or stock.indicators.rsi is None:
            return Signal(symbol=stock.symbol, signal_type=SignalType.HOLD, reason="Insufficient data for RSI")

        rsi = stock.indicators.rsi
        
        if rsi < self.oversold_threshold:
            return Signal(
                symbol=stock.symbol, 
                signal_type=SignalType.BUY, 
                strength=(self.oversold_threshold - rsi) / self.oversold_threshold, # Higher strength if deeper oversold
                reason=f"RSI Oversold: {rsi:.2f} < {self.oversold_threshold}"
            )
        elif rsi > self.overbought_threshold:
            return Signal(
                symbol=stock.symbol, 
                signal_type=SignalType.SELL, 
                strength=(rsi - self.overbought_threshold) / (100 - self.overbought_threshold),
                reason=f"RSI Overbought: {rsi:.2f} > {self.overbought_threshold}"
            )
            
        return Signal(symbol=stock.symbol, signal_type=SignalType.HOLD, reason=f"RSI Neutral: {rsi:.2f}")
