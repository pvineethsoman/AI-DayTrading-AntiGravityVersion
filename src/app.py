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
from src.services.scanner import MarketScanner
from src.services.portfolio_manager import PortfolioManager
from src.services.scheduler import AgentScheduler

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

# Agent Services
if 'scanner' not in st.session_state:
    st.session_state.scanner = MarketScanner()
if 'portfolio_manager' not in st.session_state:
    st.session_state.portfolio_manager = PortfolioManager(
        st.session_state.service,
        st.session_state.ai_analyst,
        st.session_state.engine,
        st.session_state.scanner
    )
if 'scheduler' not in st.session_state:
    st.session_state.scheduler = AgentScheduler(st.session_state.portfolio_manager)
    st.session_state.scheduler.start()

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
    
    # Sidebar Layout
    st.sidebar.image("https://img.icons8.com/fluency/96/bullish.png", width=64)
    st.sidebar.title("AI Trader")
    
    # Navigation (Top Priority)
    page = st.sidebar.radio("Navigation", ["Dashboard", "Market Analysis", "Agent Command Center", "Backtesting", "Settings"])
    
    st.sidebar.markdown("---")
    
    # AI Strategy
    st.sidebar.subheader("🧠 AI Strategy")
    ai_persona = st.sidebar.selectbox(
        "Persona",
        ["General", "Warren Buffett", "Peter Lynch", "Benjamin Graham"],
        index=0
    )
    st.session_state.ai_persona = ai_persona
    
    st.sidebar.markdown("---")

    # Execution Config
    st.sidebar.caption("Execution Mode")
    engine_type = st.sidebar.radio("Engine", ["Paper Trading", "Alpaca (Live/Paper)"], label_visibility="collapsed")
    
    if engine_type == "Alpaca (Live/Paper)":
        if settings.ALPACA_API_KEY:
            if not isinstance(st.session_state.engine, AlpacaExecutionEngine):
                try:
                    st.session_state.engine = AlpacaExecutionEngine()
                    st.sidebar.success("Connected: Alpaca")
                except Exception as e:
                    st.sidebar.error(f"Alpaca Error: {e}")
        else:
            st.sidebar.warning("Alpaca Keys Missing")
    else:
        if not isinstance(st.session_state.engine, PaperTradingEngine):
            st.session_state.engine = PaperTradingEngine()
    
    if page == "Dashboard":
        show_dashboard()
    elif page == "Market Analysis":
        show_analysis()
    elif page == "Agent Command Center":
        show_agent_dashboard()
    elif page == "Backtesting":
        show_backtesting()
    elif page == "Settings":
        show_settings()

def show_dashboard():
    st.header("Dashboard")
    
    # Portfolio Summary
    st.subheader("Portfolio Summary")
    try:
        account = st.session_state.engine.get_account()
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Equity", f"${float(account.equity):,.2f}")
        c2.metric("Buying Power", f"${float(account.buying_power):,.2f}")
        
        # Calculate P&L (Simple approximation if not provided directly)
        # Alpaca account object usually has 'last_equity'
        last_equity = float(account.last_equity)
        equity = float(account.equity)
        pnl = equity - last_equity
        pnl_pct = (pnl / last_equity) * 100 if last_equity else 0
        
        c3.metric("Today's P&L", f"${pnl:,.2f}", f"{pnl_pct:.2f}%")
        c4.metric("Status", account.status)
        
    except Exception as e:
        st.error(f"Failed to fetch account info: {e}")

    # Active Positions
    st.subheader("Active Positions")
    try:
        positions = st.session_state.engine.get_positions()
        if positions:
            pos_data = []
            for p in positions:
                pos_data.append({
                    "Symbol": p.symbol,
                    "Qty": p.qty,
                    "Value": f"${float(p.market_value):,.2f}",
                    "P&L": f"${float(p.unrealized_pl):,.2f}",
                    "P&L %": f"{float(p.unrealized_plpc)*100:.2f}%"
                })
            st.dataframe(pd.DataFrame(pos_data), use_container_width=True)
        else:
            st.info("No active positions.")
    except Exception as e:
        st.error(f"Failed to fetch positions: {e}")

    # Market News (Trending)
    st.subheader("Market News")
    try:
        # Use AAPL as a default for news if no specific context
        news = st.session_state.service.get_market_news("AAPL") 
        if news:
            for item in news[:5]:
                with st.expander(f"{item.get('title')} - {item.get('time_published')[:8]}"):
                    st.write(item.get('summary'))
                    st.caption(f"Source: {item.get('source')} | Sentiment: {item.get('overall_sentiment_score')}")
                    st.markdown(f"[Read more]({item.get('url')})")
        else:
            st.info("No news found.")
    except Exception as e:
        st.warning(f"Could not fetch news: {e}")

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
                        with st.spinner(f"Consulting {st.session_state.ai_persona}..."):
                            insight = st.session_state.ai_analyst.analyze_stock(stock, persona=st.session_state.ai_persona)
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

def show_agent_dashboard():
    st.header("🤖 Agent Command Center")
    
    # Safety Check
    if not settings.TRADING_ENABLED:
        st.error("⚠️ TRADING IS DISABLED - Enable trading in Settings to use the Agent")
        return
    
    # Agent Controls
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        next_run = st.session_state.scheduler.get_next_run()
        next_run_str = next_run.strftime("%H:%M") if next_run else "N/A"
        st.metric("Next Run", next_run_str, "Scheduled")
    with col2:
        st.metric("Active Persona", st.session_state.ai_persona)
    with col3:
        if st.button("🚀 Run Agent Cycle Now", type="primary", use_container_width=True):
            with st.status("Agent Running...", expanded=True) as status:
                st.write("🔍 Scanning Market & Watchlist...")
                watchlist_symbols = [item.symbol for item in st.session_state.watchlist]
                
                st.session_state.portfolio_manager.run_cycle(
                    persona=st.session_state.ai_persona,
                    watchlist=watchlist_symbols
                )
                status.update(label="Agent Cycle Complete", state="complete", expanded=False)
                st.rerun()

    # Activity Log
    st.subheader("📜 Agent Activity Log")
    if st.session_state.portfolio_manager.decisions_log:
        log_df = pd.DataFrame(st.session_state.portfolio_manager.decisions_log)
        st.dataframe(
            log_df, 
            column_config={
                "time": "Time",
                "symbol": "Symbol",
                "action": st.column_config.TextColumn("Action", help="Buy/Sell/Hold"),
                "reason": "Reason"
            },
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No activity logged yet. Run the agent to see decisions.")

    # Watchlist Management (Input for Agent)
    st.subheader("🎯 Priority Watchlist")
    with st.expander("Manage Watchlist"):
        c1, c2 = st.columns([3, 1])
        with c1:
            new_symbol = st.text_input("Add Symbol", "").upper()
        with c2:
            if st.button("Add") and new_symbol:
                if not any(item.symbol == new_symbol for item in st.session_state.watchlist):
                    st.session_state.watchlist.append(WatchlistItem(symbol=new_symbol))
                    st.success(f"Added {new_symbol}")
                    st.rerun()
        
        if st.session_state.watchlist:
            wl_df = pd.DataFrame([{"Symbol": i.symbol, "Added": "User"} for i in st.session_state.watchlist])
            st.dataframe(wl_df, use_container_width=True, hide_index=True)
            
            to_remove = st.selectbox("Remove", [""] + [i.symbol for i in st.session_state.watchlist])
            if st.button("Remove Symbol") and to_remove:
                st.session_state.watchlist = [i for i in st.session_state.watchlist if i.symbol != to_remove]
                st.rerun()


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
        openai_key = st.text_input("OpenAI Key", value=settings.OPENAI_API_KEY or "", type="password")
        alpaca_key = st.text_input("Alpaca Key", value=settings.ALPACA_API_KEY or "", type="password")
        alpaca_secret = st.text_input("Alpaca Secret", value=settings.ALPACA_SECRET_KEY or "", type="password")
        
        if st.form_submit_button("Update Keys"):
            settings.ALPHA_VANTAGE_API_KEY = av_key
            settings.GEMINI_API_KEY = gemini_key
            settings.OPENAI_API_KEY = openai_key
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
