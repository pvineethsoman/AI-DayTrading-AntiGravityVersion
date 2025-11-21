import logging
from datetime import datetime
from typing import List, Dict
from src.services.market_data import MarketDataService
from src.analysis.ai_analyst import AIAnalyst
from src.execution.alpaca_engine import AlpacaExecutionEngine
from src.services.scanner import MarketScanner
from src.config import settings
from src.models.trading import OrderSide, OrderType

import threading

logger = logging.getLogger(__name__)

class PortfolioManager:
    """
    Autonomous Agent that manages the portfolio.
    1. Reviews Holdings (Sell Logic)
    2. Scans Market (Buy Logic)
    """
    
    def __init__(self, market_data: MarketDataService, ai_analyst: AIAnalyst, engine: AlpacaExecutionEngine, scanner: MarketScanner):
        self.market_data = market_data
        self.ai_analyst = ai_analyst
        self.engine = engine
        self.scanner = scanner
        self.decisions_log: List[Dict] = []
        self.lock = threading.Lock()
        
    def log_decision(self, symbol: str, action: str, reason: str):
        """Logs a decision for the UI."""
        log_entry = {
            "time": datetime.now().strftime("%H:%M:%S"),
            "symbol": symbol,
            "action": action,
            "reason": reason
        }
        self.decisions_log.insert(0, log_entry) # Prepend
        # Keep log size manageable
        if len(self.decisions_log) > 50:
            self.decisions_log.pop()
            
    def run_cycle(self, persona: str = "General", watchlist: List[str] = None, max_stocks: int = 10):
        """Runs a full agent cycle."""
        if not settings.TRADING_ENABLED:
            self.log_decision("SYSTEM", "SKIP", "Trading Disabled (Kill Switch)")
            return

        # Concurrency Check
        if not self.lock.acquire(blocking=False):
            logger.warning("Agent cycle skipped: Already running.")
            self.log_decision("SYSTEM", "SKIP", "Agent Busy")
            return

        try:
            logger.info(f"Starting Agent Cycle ({persona}, max_stocks={max_stocks})")
            
            # 1. Review Holdings (Sell Logic)
            self.review_holdings(persona)
            
            # 2. Find Opportunities (Buy Logic)
            self.find_opportunities(persona, watchlist, max_stocks)
            
        finally:
            self.lock.release()
        
    def review_holdings(self, persona: str):
        """Analyzes current positions and sells if criteria met."""
        try:
            positions = self.engine.get_positions()
            
            for pos in positions:
                symbol = pos.symbol
                try:
                    # Analyze
                    stock = self.market_data.get_stock_analysis(symbol)
                    insight = self.ai_analyst.analyze_stock(stock, persona=persona)
                    
                    # Decision Logic
                    should_sell = False
                    reason = ""
                    
                    # Technical Sell (Stop Loss / Take Profit - simplified)
                    # In a real app, we'd check pos.unrealized_plpc
                    
                    # AI Sell
                    if "bearish" in insight.lower() or "sell" in insight.lower():
                        should_sell = True
                        reason = f"AI ({persona}) Bearish Outlook"
                        
                    if should_sell:
                        self.engine.place_order(
                            symbol=symbol,
                            side=OrderSide.SELL,
                            quantity=abs(int(pos.qty)), # Sell all
                            order_type=OrderType.MARKET
                        )
                        self.log_decision(symbol, "SELL", reason)
                    else:
                        self.log_decision(symbol, "HOLD", "AI Neutral/Bullish")
                        
                except Exception as e:
                    logger.error(f"Error reviewing holding {symbol}: {e}")
                    self.log_decision(symbol, "ERROR", str(e))
                    
        except Exception as e:
            logger.error(f"Error getting positions: {e}")

    def find_opportunities(self, persona: str, watchlist: List[str] = None, max_stocks: int = 10):
        """Scans market and buys if criteria met."""
        
        # Check Risk Limits (Max Open Positions)
        try:
            positions = self.engine.get_positions()
            if len(positions) >= settings.RISK_SETTINGS.max_open_positions:
                self.log_decision("SYSTEM", "SKIP BUY", "Max Open Positions Reached")
                return
        except:
            pass

        # Get Scan List
        scan_list = self.scanner.get_scan_list(watchlist)
        
        # Analyze Candidates (User-configurable limit)
        for symbol in scan_list[:max_stocks]: 
            try:
                # Skip if already owned
                if any(p.symbol == symbol for p in positions):
                    continue
                    
                # Analyze
                stock = self.market_data.get_stock_analysis(symbol)
                insight = self.ai_analyst.analyze_stock(stock, persona=persona)
                
                # Decision Logic
                should_buy = False
                reason = ""
                
                # AI Buy
                if "bullish" in insight.lower() or "buy" in insight.lower():
                    # Double check RSI isn't overbought
                    if stock.indicators and stock.indicators.rsi < 70:
                        should_buy = True
                        reason = f"AI ({persona}) Bullish + RSI OK"
                
                if should_buy:
                    # Calculate Size
                    position_value = min(1000, settings.RISK_SETTINGS.max_position_size)
                    quantity = int(position_value / stock.current_price)
                    
                    if quantity > 0:
                        self.engine.place_order(
                            symbol=symbol,
                            side=OrderSide.BUY,
                            quantity=quantity,
                            order_type=OrderType.MARKET
                        )
                        self.log_decision(symbol, "BUY", reason)
                        
                        # Stop after one buy per cycle to be conservative
                        return 
                else:
                    self.log_decision(symbol, "PASS", "AI Not Bullish enough")
                    
            except Exception as e:
                logger.error(f"Error analyzing candidate {symbol}: {e}")
                self.log_decision(symbol, "ERROR", str(e))
