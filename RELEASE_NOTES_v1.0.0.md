# AI Day Trading Bot - v1.0.0 Stable Release

## 🎉 Overview
This is the first stable release of the AI Day Trading Bot - a fully autonomous, multi-LLM powered institutional-grade trading system with professional UI and comprehensive risk management.

## ✨ Key Features

### 🤖 Multi-LLM AI Brain
- **Ensemble AI Analysis**: Combines insights from Gemini, OpenAI, and Claude
- **Investment Personas**: Warren Buffett, Peter Lynch, Benjamin Graham strategies
- **Sentiment Analysis**: Real-time news sentiment integration via Alpha Vantage

### 📊 Autonomous Agent System
- **Smart Market Scanner**: Automatically scans top gainers/losers and index constituents
- **Scheduled Execution**: Runs automatically at 09:25 AM and 02:00 PM (market times)
- **Concurrency Control**: Prevents conflicts between manual and scheduled runs
- **Intelligent Stock Selection**: Prioritizes user watchlist, trending stocks, and major indices

### 💼 Trading Execution
- **Dual Engine Support**: Paper trading and Alpaca (live/paper) integration
- **Risk Management**: Max position limits, stop-loss, position sizing
- **Kill Switch**: Emergency trading disable functionality
- **Real-time Portfolio Tracking**: Live P&L, positions, and account metrics

### 📈 Market Data & Analysis
- **Multi-Provider Failover**: Alpha Vantage → Yahoo Finance
- **Technical Indicators**: SMA, RSI, MACD, Bollinger Bands, ATR
- **Fundamental Analysis**: P/E, EPS, Market Cap, Book Value
- **Redis Caching**: 5-minute cache for performance optimization

### 🎨 Professional UI
- **Schwab-Inspired Design**: Clean, institutional-grade interface
- **Dashboard**: Portfolio summary, active positions, market news
- **Market Analysis**: Deep dive into individual stocks with AI insights
- **Agent Command Center**: Monitor autonomous agent activity and next run time
- **Backtesting**: Test strategies against historical data
- **Settings**: Risk parameters and watchlist management

### 🔒 Safety & Reliability
- **Paper Trading Default**: Safe testing environment
- **API Key Validation**: Graceful degradation when keys are missing
- **Error Handling**: Comprehensive try-catch blocks throughout
- **Logging**: Detailed logging for debugging and monitoring

## 🛠 Technical Stack
- **Frontend**: Streamlit with custom CSS
- **AI/LLM**: Google Gemini, OpenAI GPT, Anthropic Claude
- **Data Providers**: Alpha Vantage, Yahoo Finance
- **Trading API**: Alpaca Markets
- **Caching**: Redis (optional, falls back to in-memory)
- **Scheduling**: Python `schedule` library with threading

## 📋 Installation & Setup

### Prerequisites
- Python 3.9+
- API Keys (optional but recommended):
  - Alpha Vantage (for news/sentiment)
  - Gemini API (for AI analysis)
  - OpenAI API (for AI analysis)
  - Alpaca API (for live/paper trading)

### Quick Start
```bash
# Clone the repository
git clone https://github.com/pvineethsoman/AI-DayTrading-AntiGravityVersion.git
cd AI-DayTrading-AntiGravityVersion

# Install dependencies
pip install -r requirements.txt

# Set up environment variables (copy .env.example to .env and fill in your keys)
cp .env.example .env

# Run the app
streamlit run src/app.py
```

## 🔧 Configuration

### Environment Variables (.env)
```
ALPHA_VANTAGE_API_KEY=your_key_here
GEMINI_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
ALPACA_API_KEY=your_key_here
ALPACA_SECRET_KEY=your_key_here
ALPACA_PAPER=True
TRADING_ENABLED=True
```

### Risk Settings (configurable in Settings page)
- Max Open Positions: 5
- Max Position Size: $10,000
- Stop Loss %: 5%
- Take Profit %: 15%

## 🐛 Known Issues & Limitations
- Redis is optional; app falls back to in-memory cache if unavailable
- Alpha Vantage free tier has rate limits (5 calls/min, 500 calls/day)
- Backtesting uses simplified execution model
- News sentiment requires Alpha Vantage API key

## 🚀 What's Next (Future Enhancements)
- Advanced backtesting with slippage and commission modeling
- Portfolio optimization algorithms
- Options trading support
- Multi-timeframe analysis
- Mobile-responsive UI
- Real-time WebSocket data feeds
- Advanced charting with TradingView integration

## 📝 Release Notes

### v1.0.0 (2025-11-21)
- ✅ Initial stable release
- ✅ Multi-LLM AI ensemble analysis
- ✅ Autonomous agent with scheduling
- ✅ Professional UI with Schwab-inspired design
- ✅ Dual execution engine (Paper + Alpaca)
- ✅ Comprehensive risk management
- ✅ Market scanner with smart stock selection
- ✅ Backtesting engine
- ✅ Redis caching with fallback
- ✅ Full error handling and graceful degradation

## 🙏 Acknowledgments
Built with the assistance of Google Deepmind's Antigravity AI coding assistant.

## 📄 License
MIT License - See LICENSE file for details

## 🤝 Contributing
Contributions are welcome! Please open an issue or submit a pull request.

## 📧 Support
For issues or questions, please open a GitHub issue.

---

**⚠️ Disclaimer**: This software is for educational and research purposes only. Trading involves substantial risk of loss. Past performance is not indicative of future results. Always do your own research and consult with a financial advisor before making investment decisions.
