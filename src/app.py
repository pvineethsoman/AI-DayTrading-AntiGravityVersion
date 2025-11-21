import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.providers.yahoo import YahooFinanceProvider
from src.strategies.sma_crossover import SMACrossoverStrategy
from src.strategies.rsi_reversion import RSIMeanReversionStrategy
from src.backtesting.engine import Backtester
from src.execution.paper_engine import PaperTradingEngine
from src.analysis.technical import TechnicalAnalyzer
from src.models.domain import Stock

from src.services.market_data import MarketDataService
from src.execution.alpaca_engine import AlpacaExecutionEngine
from src.analysis.ai_analyst import AIAnalyst
from src.config import settings
from src.models.risk import RiskSettings
from src.models.watchlist import WatchlistItem
from src.models.trading import OrderSide, OrderType
import datetime
import random

st.set_page_config(page_title="AI Day Trading Bot", layout="wide")

# Initialize Session State
if 'service' not in st.session_state:
    st.session_state.service = MarketDataService()
if 'ai_analyst' not in st.session_state:
    st.session_state.ai_analyst = AIAnalyst()

# Execution Engine Selection
if 'engine' not in st.session_state:
    # Default to Paper
    st.session_state.engine = PaperTradingEngine()

# Watchlist
if 'watchlist' not in st.session_state:
    st.session_state.watchlist = []

def apply_custom_css():
    st.markdown("""
        <style>
        /* Professional Theme (Schwab-like) */
        .stApp {
            background-color: #f4f6f9;
            color: #333;
        }
        
        /* Sidebar */
        [data-testid="stSidebar"] {
            background-color: #ffffff;
            border-right: 1px solid #e0e0e0;
        }
        
        /* Metrics */
        [data-testid="stMetricValue"] {
            font-family: 'Arial', sans-serif;
            font-weight: 600;
            color: #004687; /* Schwab Blue */
        }
        
        /* Headers */
        h1, h2, h3 {
            font-family: 'Arial', sans-serif;
            color: #1a1a1a;
        }
        
        /* Dataframes */
        [data-testid="stDataFrame"] {
            border: 1px solid #e0e0e0;
            border-radius: 4px;
        }
        
        /* Buttons */
        .stButton button {
            background-color: #004687;
            color: white;
            border-radius: 4px;
            border: none;
            padding: 0.5rem 1rem;
            font-weight: 500;
        }
        .stButton button:hover {
            background-color: #003366;
            color: white;
        }
        
        /* Cards/Containers */
        .css-1r6slb0 {
            background-color: white;
            padding: 1rem;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        </style>
    """, unsafe_allow_html=True)

def main():
    apply_custom_css()
    st.title("📈 AI Institutional Trader")
    
    # Sidebar Config
    st.sidebar.header("Configuration")
    engine_type = st.sidebar.radio("Execution Engine", ["Paper Trading", "Alpaca (Live/Paper)"])
    
    if engine_type == "Alpaca (Live/Paper)":
        if settings.ALPACA_API_KEY:
            if not isinstance(st.session_state.engine, AlpacaExecutionEngine):
                try:
                    st.session_state.engine = AlpacaExecutionEngine()
                    st.sidebar.success("Connected to Alpaca")
                except Exception as e:
                    st.sidebar.error(f"Alpaca Connection Failed: {e}")
        else:
            st.sidebar.warning("Alpaca Keys Missing in .env")
    else:
        if not isinstance(st.session_state.engine, PaperTradingEngine):
            st.session_state.engine = PaperTradingEngine()
    
    page = st.sidebar.radio("Navigation", ["Dashboard", "Market Analysis", "Auto-Trading", "Backtesting", "Settings"])
    
    if page == "Dashboard":
        show_dashboard()
    elif page == "Market Analysis":
        show_analysis()
    elif page == "Auto-Trading":
        show_auto_trading()
    elif page == "Backtesting":
        show_backtesting()
    elif page == "Settings":
        show_settings()

def show_dashboard():
                    with st.expander(f"{item.get('title')} - {item.get('time_published')[:8]}"):
                        st.write(item.get('summary'))
                        st.caption(f"Source: {item.get('source')} | Sentiment: {item.get('overall_sentiment_score')}")
                        st.markdown(f"[Read more]({item.get('url')})")
            else:
                st.info("No news found or provider doesn't support news.")

def show_analysis():
    st.header("Market Analysis")
    
    tab1, tab2 = st.tabs(["Single Stock", "Bulk Analysis"])
    
    with tab1:
        symbol = st.text_input("Enter Stock Symbol", "AAPL").upper()
        
        if st.button("Analyze"):
            with st.spinner(f"Fetching data for {symbol}..."):
                try:
                    # Use service to get analyzed stock
                    stock = st.session_state.service.get_stock_analysis(symbol)
                    
                    # Display Current Info
                    col1, col2 = st.columns(2)
                    col1.metric("Current Price", f"${stock.current_price:.2f}")
                    col2.metric("Company", stock.company_name or "N/A")
                    
                    # Charts
                    plot_stock_data(stock)
                    
                    # AI Insight
                    st.subheader("🤖 AI Analyst Insight")
                    if st.button("Generate Insight", key=f"insight_{symbol}"):
                        with st.spinner("Consulting Gemini..."):
                            insight = st.session_state.ai_analyst.analyze_stock(stock)
                            st.info(insight)
                    
                except Exception as e:
                    st.error(f"Error: {e}")

    with tab2:
        st.subheader("Bulk Stock Analysis")
        symbols_input = st.text_area("Enter symbols (comma separated)", "AAPL, MSFT, GOOG, AMZN")
        
        if st.button("Analyze All"):
            symbols = [s.strip().upper() for s in symbols_input.split(",") if s.strip()]
            results = []
            
            progress_bar = st.progress(0)
            for i, sym in enumerate(symbols):
                try:
                    stock = st.session_state.service.get_stock_analysis(sym)
                    results.append({
                        "Symbol": sym,
                        "Price": f"${stock.current_price:.2f}",
                        "RSI": f"{stock.indicators.rsi:.2f}" if stock.indicators else "N/A",
                        "MACD": f"{stock.indicators.macd:.2f}" if stock.indicators else "N/A",
                        "SMA 50": f"{stock.indicators.sma_50:.2f}" if stock.indicators else "N/A"
                    })
                except Exception as e:
                    results.append({"Symbol": sym, "Error": str(e)})
                progress_bar.progress((i + 1) / len(symbols))
                
            st.dataframe(pd.DataFrame(results))

def show_auto_trading():
    st.header("🤖 Auto-Trading Watchlist")
    
    # Safety Check
    if not settings.TRADING_ENABLED:
        st.error("⚠️ TRADING IS DISABLED - Enable trading in Settings to use Auto-Trading")
        return
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Watchlist")
        
        # Add symbol to watchlist
        new_symbol = st.text_input("Add Symbol to Watchlist", "").upper()
        if st.button("Add to Watchlist") and new_symbol:
            if not any(item.symbol == new_symbol for item in st.session_state.watchlist):
                st.session_state.watchlist.append(WatchlistItem(symbol=new_symbol))
                st.success(f"Added {new_symbol} to watchlist")
            else:
                st.warning(f"{new_symbol} already in watchlist")
        
        # Display watchlist
        if st.session_state.watchlist:
            watchlist_data = []
            for item in st.session_state.watchlist:
                watchlist_data.append({
                    "Symbol": item.symbol,
                    "Auto-Trade": "✅" if item.auto_trade else "❌",
                    "Last Signal": item.last_signal or "N/A",
                    "Last Analyzed": item.last_analyzed.strftime("%Y-%m-%d %H:%M") if item.last_analyzed else "Never"
                })
            st.dataframe(pd.DataFrame(watchlist_data))
            
            # Remove symbol
            remove_symbol = st.selectbox("Remove Symbol", [""] + [item.symbol for item in st.session_state.watchlist])
            if st.button("Remove") and remove_symbol:
                st.session_state.watchlist = [item for item in st.session_state.watchlist if item.symbol != remove_symbol]
                st.success(f"Removed {remove_symbol}")
                st.rerun()
        else:
            st.info("No symbols in watchlist. Add symbols above.")
    
    with col2:
        st.subheader("Actions")
        
        if st.button("🔍 Analyze All", type="primary"):
            if not st.session_state.watchlist:
                st.warning("Watchlist is empty")
            else:
                analyze_and_trade_watchlist()

def analyze_and_trade_watchlist():
    """Analyze all watchlist stocks and execute trades based on signals."""
    st.subheader("Analysis Results")
    
    results = []
    trades_executed = []
    
    progress_bar = st.progress(0)
    for i, item in enumerate(st.session_state.watchlist):
        try:
            # Analyze stock
            stock = st.session_state.service.get_stock_analysis(item.symbol)
            
            # Generate signal based on RSI and AI
            signal = "HOLD"
            reason = ""
            
            if stock.indicators:
                # Simple trading logic
                if stock.indicators.rsi < 30:
                    signal = "BUY"
                    reason = f"RSI oversold ({stock.indicators.rsi:.1f})"
                elif stock.indicators.rsi > 70:
                    signal = "SELL"
                    reason = f"RSI overbought ({stock.indicators.rsi:.1f})"
                
                # Get AI confirmation
                try:
                    ai_insight = st.session_state.ai_analyst.analyze_stock(stock)
                    if "bullish" in ai_insight.lower() and signal != "SELL":
                        signal = "BUY"
                        reason += " + AI Bullish"
                    elif "bearish" in ai_insight.lower() and signal != "BUY":
                        signal = "SELL"
                        reason += " + AI Bearish"
                except:
                    pass
            
            # Update watchlist item
            item.last_analyzed = datetime.datetime.now()
            item.last_signal = signal
            
            results.append({
                "Symbol": item.symbol,
                "Price": f"${stock.current_price:.2f}",
                "Signal": signal,
                "Reason": reason,
                "Auto-Trade": "✅" if item.auto_trade else "❌"
            })
            
            # Execute trade if auto-trade enabled
            if item.auto_trade and signal in ["BUY", "SELL"]:
                try:
                    # Calculate position size (simple: $1000 per trade or max position size)
                    position_value = min(1000, settings.RISK_SETTINGS.max_position_size)
                    quantity = int(position_value / stock.current_price)
                    
                    if quantity > 0:
                        order_side = OrderSide.BUY if signal == "BUY" else OrderSide.SELL
                        order = st.session_state.engine.place_order(
                            symbol=item.symbol,
                            side=order_side,
                            quantity=quantity,
                            order_type=OrderType.MARKET
                        )
                        trades_executed.append({
                            "Symbol": item.symbol,
                            "Action": signal,
                            "Quantity": quantity,
                            "Order ID": order.id
                        })
                except Exception as e:
                    st.error(f"Failed to execute trade for {item.symbol}: {e}")
            
        except Exception as e:
            results.append({
                "Symbol": item.symbol,
                "Error": str(e)
            })
        
        progress_bar.progress((i + 1) / len(st.session_state.watchlist))
    
    # Display results
    st.dataframe(pd.DataFrame(results))
    
    # Display executed trades
    if trades_executed:
        st.success(f"✅ Executed {len(trades_executed)} trades")
        st.dataframe(pd.DataFrame(trades_executed))
    else:
        st.info("No trades executed (no signals or auto-trade disabled)")


def show_settings():
    st.header("Settings & Safety")
    
    # Kill Switch
    st.subheader("🛑 Global Safety")
    trading_enabled = st.toggle("Enable Trading", value=settings.TRADING_ENABLED)
    if trading_enabled != settings.TRADING_ENABLED:
        settings.TRADING_ENABLED = trading_enabled
        if not trading_enabled:
            st.error("TRADING DISABLED - KILL SWITCH ACTIVATED")
        else:
            st.success("Trading Enabled")
            
    # Risk Management
    st.subheader("Risk Management")
    with st.form("risk_settings"):
        max_pos = st.number_input("Max Position Size ($)", value=settings.RISK_SETTINGS.max_position_size)
        max_loss = st.number_input("Max Daily Loss ($)", value=settings.RISK_SETTINGS.max_daily_loss)
        max_dd = st.number_input("Max Drawdown (%)", value=settings.RISK_SETTINGS.max_drawdown_pct)
        max_open = st.number_input("Max Open Positions", value=settings.RISK_SETTINGS.max_open_positions)
        
        if st.form_submit_button("Update Risk Settings"):
            settings.RISK_SETTINGS.max_position_size = max_pos
            settings.RISK_SETTINGS.max_daily_loss = max_loss
            settings.RISK_SETTINGS.max_drawdown_pct = max_dd
            settings.RISK_SETTINGS.max_open_positions = int(max_open)
            st.success("Risk settings updated!")

    # API Keys
    st.subheader("API Configuration")
    with st.form("api_keys"):
        av_key = st.text_input("Alpha Vantage Key", value=settings.ALPHA_VANTAGE_API_KEY or "", type="password")
        gemini_key = st.text_input("Gemini Key", value=settings.GEMINI_API_KEY or "", type="password")
        alpaca_key = st.text_input("Alpaca Key", value=settings.ALPACA_API_KEY or "", type="password")
        alpaca_secret = st.text_input("Alpaca Secret", value=settings.ALPACA_SECRET_KEY or "", type="password")
        
        if st.form_submit_button("Update Keys"):
            settings.ALPHA_VANTAGE_API_KEY = av_key
            settings.GEMINI_API_KEY = gemini_key
            settings.ALPACA_API_KEY = alpaca_key
            settings.ALPACA_SECRET_KEY = alpaca_secret
            st.success("API Keys updated for this session!")

def plot_stock_data(stock: Stock):
    df = pd.DataFrame([p.model_dump() for p in stock.history])
    df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
    df.set_index('timestamp', inplace=True)
    
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                        vertical_spacing=0.03, subplot_titles=('Price', 'RSI'),
                        row_width=[0.2, 0.7])

    # Candlestick
    fig.add_trace(go.Candlestick(x=df.index,
                open=df['open'], high=df['high'],
                low=df['low'], close=df['close'], name='OHLC'), row=1, col=1)
    
    # Indicators
    if stock.indicators:
        # SMA
        if stock.indicators.sma_50:
             # We need full history for SMA line, but stock.indicators only has latest value in our current model
             # To plot lines, we'd need to calculate indicators on the full DF here for visualization
             # Let's recalculate for plotting purposes
             close = df['close']
             sma50 = close.rolling(window=50).mean()
             sma200 = close.rolling(window=200).mean()
             
             fig.add_trace(go.Scatter(x=df.index, y=sma50, line=dict(color='orange', width=1), name='SMA 50'), row=1, col=1)
             fig.add_trace(go.Scatter(x=df.index, y=sma200, line=dict(color='blue', width=1), name='SMA 200'), row=1, col=1)

        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        fig.add_trace(go.Scatter(x=df.index, y=rsi, line=dict(color='purple', width=1), name='RSI'), row=2, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)

    fig.update_layout(height=800, xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)

def show_backtesting():
    st.header("Backtesting")
    
    col1, col2 = st.columns(2)
    symbol = col1.text_input("Symbol", "AAPL", key="bt_sym").upper()
    strategy_name = col2.selectbox("Strategy", ["SMA Crossover", "RSI Mean Reversion"])
    
    if st.button("Run Backtest"):
        with st.spinner("Running backtest..."):
            try:
                # Fetch Data
                stock = st.session_state.service.get_stock_analysis(symbol)
                
                # Select Strategy
                if strategy_name == "SMA Crossover":
                    strategy = SMACrossoverStrategy()
                else:
                    strategy = RSIMeanReversionStrategy()
                
                # Run Backtest
                # We need to capture the engine state from backtester
                # Our current Backtester creates a NEW engine internally.
                # For visualization, we might want to modify Backtester to accept an engine or return trades.
                # For now, we'll just use the standard one and show results textually/chart.
                
                backtester = Backtester(strategy)
                # Capture stdout to show logs? Or just modify backtester to return stats.
                # Let's just run it and show final portfolio value for now.
                # Ideally refactor Backtester to return a Result object.
                
                # Hack: Redirect stdout to capture print statements for now
                import io
                from contextlib import redirect_stdout
                
                f = io.StringIO()
                with redirect_stdout(f):
                    backtester.run(stock)
                
                output = f.getvalue()
                st.text_area("Backtest Logs", output, height=300)
                
                # Show final stats
                final_val = backtester.engine.portfolio.total_value
                st.success(f"Backtest Complete. Final Value: ${final_val:,.2f}")
                
            except Exception as e:
                st.error(f"Backtest failed: {e}")

if __name__ == "__main__":
    main()
