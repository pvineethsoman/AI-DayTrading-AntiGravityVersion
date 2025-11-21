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

def main():
    st.title("🤖 AI Day Trading Bot")
    
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
    
    page = st.sidebar.selectbox("Navigation", ["Dashboard", "Market Analysis", "Backtesting"])
    
    if page == "Dashboard":
        show_dashboard()
    elif page == "Market Analysis":
        show_analysis()
    elif page == "Backtesting":
        show_backtesting()

def show_dashboard():
    st.header("Portfolio Overview")
    
    portfolio = st.session_state.engine.portfolio
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Value", f"${portfolio.total_value:,.2f}")
    col2.metric("Cash Balance", f"${portfolio.cash:,.2f}")
    col3.metric("Active Positions", len(portfolio.positions))
    
    if portfolio.positions:
        st.subheader("Current Positions")
        data = []
        for sym, pos in portfolio.positions.items():
            data.append({
                "Symbol": sym,
                "Quantity": pos.quantity,
                "Avg Price": f"${pos.average_price:.2f}",
                "Current Price": f"${pos.current_price:.2f}",
                "Unrealized PnL": f"${pos.unrealized_pnl:.2f}"
            })
        st.dataframe(pd.DataFrame(data))
    else:
        st.info("No active positions. Go to Backtesting to simulate trades!")

def show_analysis():
    st.header("Market Analysis")
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
                if st.button("Generate Insight"):
                    with st.spinner("Consulting Gemini..."):
                        insight = st.session_state.ai_analyst.analyze_stock(stock)
                        st.info(insight)
                
            except Exception as e:
                st.error(f"Error: {e}")

def plot_stock_data(stock: Stock):
    df = pd.DataFrame([p.model_dump() for p in stock.history])
    df['timestamp'] = pd.to_datetime(df['timestamp'])
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
