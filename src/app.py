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

# AI Persona
if 'ai_persona' not in st.session_state:
    st.session_state.ai_persona = "General"


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
        
        /* Sidebar Text - Force Dark Color */
        [data-testid="stSidebar"] * {
            color: #1a1a1a !important;
        }
        
        /* Sidebar Headers */
        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3 {
            color: #004687 !important;
        }
        
        /* Sidebar Radio/Selectbox Labels */
        [data-testid="stSidebar"] label {
            color: #333 !important;
        }
        
        /* Selectbox Dropdown - Fix visibility */
        [data-testid="stSidebar"] select,
        [data-testid="stSidebar"] option {
            background-color: #ffffff !important;
            color: #1a1a1a !important;
        }
        
        /* Main Content Area - All Labels Visible */
        label, .stTextInput label, .stNumberInput label, .stSelectbox label {
            color: #1a1a1a !important;
            font-weight: 500;
        }
        
        /* Text Inputs - Ensure visibility */
        input[type="text"], input[type="number"], input[type="password"] {
            background-color: #ffffff !important;
            color: #1a1a1a !important;
            border: 1px solid #ccc !important;
        }
        
        /* Selectbox in main area */
        select {
            background-color: #ffffff !important;
            color: #1a1a1a !important;
            border: 1px solid #ccc !important;
        }
        
        option {
            background-color: #ffffff !important;
            color: #1a1a1a !important;
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
        
        /* Buttons - Ensure High Contrast */
        .stButton > button,
        button[kind="primary"],
        button[kind="secondary"],
        button[type="submit"],
        .stFormSubmitButton > button {
            background-color: #004687 !important;
            color: white !important;
            border-radius: 4px !important;
            border: none !important;
            padding: 0.5rem 1rem !important;
            font-weight: 500 !important;
        }
        .stButton > button:hover,
        button[kind="primary"]:hover,
        button[kind="secondary"]:hover,
        button[type="submit"]:hover,
        .stFormSubmitButton > button:hover {
            background-color: #003366 !important;
            color: white !important;
        }
        
        /* Radio Buttons - Fix visibility */
        .stRadio > label,
        .stRadio > div {
            color: #1a1a1a !important;
        }
        
        .stRadio > div > label {
            color: #1a1a1a !important;
            background-color: transparent !important;
        }
        
        .stRadio input[type="radio"] {
            accent-color: #004687 !important;
        }
        
        /* Radio button text */
        .stRadio > div > label > div {
            color: #1a1a1a !important;
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
    
    # DEBUG: Show available secrets (Keys only, for security)
    if hasattr(st, "secrets"):
        try:
            # Convert to list to avoid showing actual values
            secret_keys = list(st.secrets.keys())
            st.sidebar.warning(f"DEBUG: Secrets Found: {secret_keys}")
            if not secret_keys:
                 st.sidebar.error("DEBUG: st.secrets is EMPTY!")
        except Exception as e:
            st.sidebar.error(f"DEBUG: Error reading secrets: {e}")
    else:
        st.sidebar.error("DEBUG: st.secrets attribute MISSING")

    st.title("📈 AI Institutional Trader")
    
    # Sidebar Layout
    st.sidebar.image("https://img.icons8.com/fluency/96/bullish.png", width=64)
    st.sidebar.title("AI Trader")
    
    # Navigation (Top Priority)
    page = st.sidebar.radio("Navigation", ["Dashboard", "Market Analysis", "Agent Command Center", "Backtesting", "Settings"])
    
    st.sidebar.markdown("---")

    # Execution Config - Alpaca Only
    st.sidebar.caption("Execution Mode")
    st.sidebar.write("**Alpaca Trading**")
    
    if settings.ALPACA_API_KEY:
        if not isinstance(st.session_state.engine, AlpacaExecutionEngine):
            try:
                st.session_state.engine = AlpacaExecutionEngine()
                mode = "Paper" if settings.ALPACA_PAPER else "Live"
                st.sidebar.success(f"✅ Connected: Alpaca ({mode})")
            except Exception as e:
                st.sidebar.error(f"❌ Alpaca Error: {e}")
        else:
            mode = "Paper" if settings.ALPACA_PAPER else "Live"
            st.sidebar.info(f"📊 Mode: {mode}")
            st.sidebar.caption("Change mode in Settings")
    else:
        st.sidebar.error("❌ Alpaca API keys not configured")
        st.sidebar.caption("Add keys in Settings to enable trading")

    
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
                    # Store in session state to persist across reruns
                    st.session_state.current_stock = stock
                    st.session_state.current_symbol = symbol
                except Exception as e:
                    st.error(f"Error: {e}")
                    st.session_state.current_stock = None
        
        # Display analysis if stock data exists in session state
        if hasattr(st.session_state, 'current_stock') and st.session_state.current_stock:
            stock = st.session_state.current_stock
            
            # Display Current Info
            col1, col2 = st.columns(2)
            col1.metric("Current Price", f"${stock.current_price:.2f}")
            col2.metric("Company", stock.company_name or "N/A")
            
            # Charts
            plot_stock_data(stock)
            
            # AI Insight
            st.subheader("🤖 AI Analyst Insight")
            if st.button("Generate Insight", key=f"insight_{st.session_state.current_symbol}"):
                with st.spinner(f"Consulting {st.session_state.ai_persona}..."):
                    insight = st.session_state.ai_analyst.analyze_stock(stock, persona=st.session_state.ai_persona)
                    st.session_state.current_insight = insight
            
            # Display insight if it exists
            if hasattr(st.session_state, 'current_insight') and st.session_state.current_insight:
                st.info(st.session_state.current_insight)

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
    
    # AI Strategy Selection
    st.subheader("🧠 AI Investment Strategy")
    ai_persona = st.selectbox(
        "Select Investment Persona",
        ["General", "Warren Buffett", "Peter Lynch", "Benjamin Graham", "Joel Greenblatt", "Philip Fisher", "John Templeton"],
        index=0,
        help="Choose the AI investment strategy for the autonomous agent"
    )
    st.session_state.ai_persona = ai_persona
    
    st.markdown("---")
    
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
        # Max stocks slider
        max_stocks = st.slider("Max Stocks to Analyze", min_value=5, max_value=50, value=10, step=5,
                               help="How many stocks should the agent analyze per run?")
    
    # Run Button
    if st.button("🚀 Run Agent Cycle Now", type="primary", use_container_width=True):
        with st.status("Agent Running...", expanded=True) as status:
            st.write("🔍 Scanning Market & Watchlist...")
            watchlist_symbols = [item.symbol for item in st.session_state.watchlist]
            
            st.session_state.portfolio_manager.run_cycle(
                persona=st.session_state.ai_persona,
                watchlist=watchlist_symbols,
                max_stocks=max_stocks
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
    
    # Alpaca Mode Toggle
    st.subheader("📊 Alpaca Trading Mode")
    st.info("**Paper Mode**: Trade with simulated money on Alpaca's paper trading environment\n\n**Live Mode**: Trade with real money (requires funded Alpaca account)")
    
    alpaca_mode = st.radio(
        "Select Mode",
        ["Paper Trading", "Live Trading"],
        index=0 if settings.ALPACA_PAPER else 1,
        help="Paper mode uses paper-api.alpaca.markets, Live mode uses api.alpaca.markets"
    )
    
    new_paper_mode = (alpaca_mode == "Paper Trading")
    if new_paper_mode != settings.ALPACA_PAPER:
        settings.ALPACA_PAPER = new_paper_mode
        # Reinitialize engine with new mode
        if settings.ALPACA_API_KEY:
            try:
                st.session_state.engine = AlpacaExecutionEngine()
                st.success(f"✅ Switched to {alpaca_mode}")
                st.rerun()
            except Exception as e:
                st.error(f"Error switching mode: {e}")

            
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
    st.header("📊 Backtesting")
    
    # Help Text
    with st.expander("ℹ️ What is Backtesting?"):
        st.markdown("""
        **Backtesting** allows you to test trading strategies against historical data to see how they would have performed.
        
        **How it works:**
        1. Select a stock symbol and a trading strategy
        2. The system fetches historical price data (typically last 100-200 days)
        3. The strategy is simulated on past data (as if you traded in the past)
        4. You see the results: profit/loss, number of trades, win rate, etc.
        
        **Available Strategies (Technical/Rule-Based):**
        - **SMA Crossover**: Buys when short-term average crosses above long-term, sells when it crosses below
        - **RSI Mean Reversion**: Buys when RSI is oversold (<30), sells when overbought (>70)
        
        **Why only technical strategies?**
        AI personas (Buffett, Lynch, etc.) require real-time LLM API calls and can't be easily backtested on historical data. 
        Technical strategies are rule-based and deterministic, making them perfect for backtesting.
        
        **Why backtest?**
        - Validate strategy performance before risking real money
        - Understand historical returns and drawdowns
        - Compare different strategies on the same stock
        
        ⚠️ **Important**: Past performance does not guarantee future results!
        """)
    
    col1, col2 = st.columns(2)
    symbol = col1.text_input("Symbol", "AAPL", key="bt_sym").upper()
    strategy_name = col2.selectbox("Strategy", ["SMA Crossover", "RSI Mean Reversion"])
    
    if st.button("Run Backtest"):
        with st.spinner("Running backtest..."):
            try:
                # Fetch Data
                stock = st.session_state.service.get_stock_analysis(symbol)
                
                # Display date range
                if stock.history and len(stock.history) > 0:
                    start_date = stock.history[0].timestamp
                    end_date = stock.history[-1].timestamp
                    st.info(f"📅 Testing period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')} ({len(stock.history)} days)")
                
                # Select Strategy
                if strategy_name == "SMA Crossover":
                    strategy = SMACrossoverStrategy()
                else:
                    strategy = RSIMeanReversionStrategy()
                
                # Run Backtest
                backtester = Backtester(strategy)
                
                # Capture stdout to show logs
                import io
                from contextlib import redirect_stdout
                
                f = io.StringIO()
                with redirect_stdout(f):
                    backtester.run(stock)
                
                output = f.getvalue()
                st.text_area("Backtest Logs", output, height=300)
                
                # Show final stats
                final_val = backtester.engine.portfolio.total_value
                initial_val = 10000  # Default starting capital
                pnl = final_val - initial_val
                pnl_pct = (pnl / initial_val) * 100
                
                col1, col2, col3 = st.columns(3)
                col1.metric("Final Value", f"${final_val:,.2f}")
                col2.metric("P&L", f"${pnl:,.2f}", f"{pnl_pct:+.2f}%")
                col3.metric("Strategy", strategy_name)
                
            except Exception as e:
                st.error(f"Backtest failed: {e}")

if __name__ == "__main__":
    main()
