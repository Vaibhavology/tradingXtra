<p align="center">
  <img src="https://img.shields.io/badge/status-live-brightgreen?style=for-the-badge" alt="Status" />
  <img src="https://img.shields.io/badge/python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/Next.js-15-black?style=for-the-badge&logo=next.js&logoColor=white" alt="Next.js" />
  <img src="https://img.shields.io/badge/FastAPI-0.100+-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Gemini_AI-2.5_Flash-4285F4?style=for-the-badge&logo=google&logoColor=white" alt="Gemini" />
</p>

# TradingXtra — AI-Powered Quantitative Trading Terminal

**TradingXtra** is a production-grade, institutional-style quantitative trading terminal built for the Indian stock market. It combines real-time market data, a multi-agent decision engine, and Google Gemini-powered AI to deliver a **"Decision-First" command center** — where every trade recommendation is backed by math, not emotion.

> **Live:** [tradingxtra.vercel.app](https://tradingxtra.vercel.app)

---

## What Makes It Different

Most trading dashboards show you charts. TradingXtra tells you **what to do and why**.

- Every stock pick passes through a **7-factor weighted scoring model** with probability gates
- Trades are only shown if they have **positive Expected Value (EV)** — the same framework used by quant funds
- A multi-agent system evaluates **pattern strength, sector momentum, volume confirmation, liquidity, manipulation risk, news sentiment, and market regime** independently
- The system auto-generates a **paper trading portfolio**, tracks every position in real-time, and builds performance analytics with no manual data entry

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Next.js)                       │
│  Dashboard → Analyzer → Portfolio → Performance → Trade Journal │
│         SessionStorage Cache · Skeleton Loading · SEO           │
└────────────────────────┬────────────────────────────────────────┘
                         │ REST API
┌────────────────────────▼────────────────────────────────────────┐
│                      BACKEND (FastAPI)                          │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              MULTI-AGENT DECISION ENGINE                 │   │
│  │                                                          │   │
│  │  ┌─────────┐ ┌─────────┐ ┌──────────┐ ┌─────────────┐  │   │
│  │  │ Pattern │ │ Sector  │ │Liquidity │ │Manipulation │  │   │
│  │  │  Agent  │ │  Agent  │ │  Agent   │ │   Agent     │  │   │
│  │  └────┬────┘ └────┬────┘ └────┬─────┘ └──────┬──────┘  │   │
│  │       └───────────┼──────────┼───────────────┘          │   │
│  │                   ▼          ▼                           │   │
│  │          ┌─────────────────────────┐                    │   │
│  │          │    Feature Engine       │                    │   │
│  │          │  PS·MA·SS·VC·LS·SE·MR   │                    │   │
│  │          └───────────┬─────────────┘                    │   │
│  │                      ▼                                  │   │
│  │          ┌─────────────────────────┐                    │   │
│  │          │   Regime Detector       │                    │   │
│  │          │ Trending·Sideways·Vol.  │                    │   │
│  │          └───────────┬─────────────┘                    │   │
│  │                      ▼                                  │   │
│  │    WScore → P(win) → EV → R:R → ACCEPT / REJECT        │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Services: Portfolio · Performance · Market Brief · News · AI   │
│  Data: yfinance · RSS · YouTube Transcripts · Gemini Vision     │
│  Storage: Supabase PostgreSQL · In-Memory Cache (5min TTL)      │
└─────────────────────────────────────────────────────────────────┘
```

---

## Features

### 🎯 Decision Engine
- **7-Factor Weighted Score**: Pattern Strength (PS), Market Alignment (MA), Sector Strength (SS), Volume Confirmation (VC), Liquidity Score (LS), Sentiment (SE), Manipulation Risk (MR)
- **Regime-Adaptive Weights**: Weights auto-adjust based on whether the market is trending, sideways, or volatile
- **Sigmoid Probability Model**: `P(win) = 1 / (1 + exp(-K × (WScore - θ)))` converts raw scores into calibrated probabilities
- **Hard Rejection Gates**: Negative EV, low P(win), poor R:R, or illiquid stocks are automatically filtered out with visible reasons

### 🤖 Multi-Agent System
| Agent | Purpose | Output |
|-------|---------|--------|
| **Pattern Agent** | Detects breakout, trend, reversal, consolidation patterns | Pattern type + score (0–1) |
| **Sector Agent** | Measures relative sector strength vs NIFTY 50 | Sector momentum score |
| **Liquidity Agent** | Evaluates average volume, spread, and turnover | Liquidity score (0–1) |
| **Manipulation Agent** | Detects pump-dump patterns, volume anomalies, price spikes | Risk score (0–1) |
| **Regime Detector** | Classifies market as Trending / Sideways / Volatile using ADX + VIX | Regime label + confidence |

### 📊 Dashboard
- **Market State Hero**: Real-time bias (Bullish/Bearish/Neutral), confidence %, and market behavior
- **Stock Pick Cards**: Each card shows stock-specific reasons ("Why this trade") and risks extracted from actual agent analysis — not generic text
- **Risk Context Panel**: VIX, weak sectors, market alerts
- **Invest Smart**: YouTube video intelligence — auto-fetches latest market analysis, extracts strategy insights, stock mentions, and sentiment via Gemini AI
- **Skeleton Loading**: Full-layout skeleton with gradient-sweep shimmer animations that mirror the exact dashboard shape
- **Persistent Cache**: `sessionStorage` + React Context caching — switching tabs and returning shows data instantly

### 📈 Stock Analyzer
- Search any NSE stock by name or symbol
- AI-powered strengths/weaknesses analysis
- Real-time order book flow visualization
- Investment verdict with risk assessment
- Market cap, P/E ratio, and earnings date

### 💼 Portfolio & Performance
- **Paper Trading Portfolio**: Auto-generated positions from accepted picks
- **Real-Time P&L**: Unrealized gains/losses tracked at 30-second intervals
- **Sector Exposure**: Visual breakdown of portfolio concentration
- **Equity Curve**: Interactive chart with drawdown tracking
- **Advanced Metrics**: Win rate, profit factor, MFE/MAE, calibration scores
- **Trade Journal**: Complete log of every trade with entry/exit, P&L, regime at entry

### 🔍 Chart Analyzer
- Upload any stock chart screenshot
- Gemini Vision AI identifies patterns, support/resistance, and trend direction
- Returns actionable analysis with confidence levels

---

## Tech Stack

### Backend
| Technology | Purpose |
|-----------|---------|
| **FastAPI** | Async REST API framework |
| **Python 3.10+** | Core language |
| **yfinance** | Real-time OHLCV data for 35 NSE stocks + indices |
| **Google Gemini 2.5 Flash** | Multimodal AI (chart analysis, video intelligence) |
| **Supabase PostgreSQL** | Trade journaling, portfolio state, performance data |
| **SQLAlchemy** | ORM for database operations |
| **youtube-transcript-api** | Extract stock mentions from analyst videos |
| **RSS Feeds** | Global/domestic market news ingestion |

### Frontend
| Technology | Purpose |
|-----------|---------|
| **Next.js 15** | React framework with App Router |
| **Tailwind CSS** | Custom dark terminal aesthetic |
| **Chart.js** | Equity curves and performance charts |
| **Lucide React** | Professional icon system |
| **React Context + sessionStorage** | Persistent dashboard caching |

### Infrastructure
| Service | Purpose |
|---------|---------|
| **Vercel** | Frontend hosting (auto-deploy from GitHub) |
| **Render** | Backend API hosting |
| **Supabase** | Managed PostgreSQL database |
| **Google Search Console** | SEO monitoring with canonical URLs + structured sitemap |

---

## The Decision Pipeline

Every stock goes through this pipeline before appearing on the dashboard:

```
Raw Price Data (yfinance)
    │
    ├── Pattern Agent → PS score
    ├── Sector Agent → SS score  
    ├── Liquidity Agent → LS score
    ├── Manipulation Agent → MR score
    ├── News Service → SE score (capped at 0.7)
    ├── Feature Engine → MA, VC scores
    │
    ▼
Regime Detection (ADX + VIX)
    │
    ▼
Regime-Adjusted Weights (re-normalized)
    │
    ▼
WScore = Σ(weight_i × feature_i)
    │
    ▼
P(win) = sigmoid(K × (WScore - θ))
    │
    ▼
ATR-Based Entry / SL / Target (regime-adjusted multipliers)
    │
    ▼
EV = P(win) × Reward - (1 - P(win)) × Risk
    │
    ▼
Rejection Gates:
  ✗ EV ≤ 0         → REJECT
  ✗ P(win) < 55%   → REJECT  
  ✗ R:R < 1.3      → REJECT
  ✗ ATR < ₹0.50    → REJECT
    │
    ▼
ACCEPT → Dashboard Pick Card (with stock-specific reasoning)
```

---

## Key Metrics Tracked

| Metric | What It Measures | Why It Matters |
|--------|-----------------|----------------|
| **Expected Value (EV)** | Statistical value of a trade over 100 iterations | Prevents taking negative-edge trades |
| **P(win)** | Calibrated win probability from sigmoid model | Rejects low-conviction setups |
| **Risk:Reward** | Target distance / Stop loss distance | Ensures asymmetric payoff structure |
| **MFE / MAE** | Max profit reached / Max loss endured per trade | Reveals execution quality and stop placement |
| **Calibration** | Predicted probability vs actual win rate | Validates model accuracy over time |
| **Profit Factor** | Gross profits / Gross losses | Overall system profitability |
| **Capital Utilization** | % of portfolio deployed | Prevents over-leverage in volatile regimes |

---

## Getting Started

### 1. Clone & Setup Backend
```bash
git clone https://github.com/Vaibhavology/tradingXtra.git
cd tradingXtra/backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**Environment Variables (`backend/.env`):**
```env
GEMINI_API_KEY=your_google_gemini_api_key
```

**Run Backend:**
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Setup Frontend
```bash
cd frontend
npm install
npm run dev
```

The terminal will be live at `http://localhost:3000`.

---

## Project Structure

```
Trading_xtra/
├── backend/
│   ├── app/
│   │   ├── agents/               # Multi-agent system
│   │   │   ├── pattern_agent.py      # Chart pattern detection
│   │   │   ├── sector_agent.py       # Relative sector strength
│   │   │   ├── liquidity_agent.py    # Volume & spread analysis
│   │   │   ├── manipulation_agent.py # Anomaly detection
│   │   │   └── regime_detector.py    # Market regime classification
│   │   ├── services/             # Core business logic
│   │   │   ├── portfolio.py          # Position management
│   │   │   ├── performance.py        # Metrics & equity curve
│   │   │   ├── market_brief.py       # News + YouTube intelligence
│   │   │   ├── chart_analyzer.py     # Gemini Vision AI
│   │   │   ├── news_service.py       # RSS sentiment parsing
│   │   │   ├── trade_monitor.py      # SL/Target hit detection
│   │   │   └── calibration.py        # Model accuracy tracking
│   │   ├── decision_engine.py    # The core EV pipeline
│   │   ├── feature_engine.py     # Technical feature computation
│   │   ├── data_fetcher.py       # yfinance data layer + cache
│   │   └── main.py               # FastAPI app + routes
│   └── requirements.txt
├── frontend/
│   ├── app/                      # Next.js App Router pages
│   │   ├── page.tsx                  # Dashboard (command center)
│   │   ├── analyze/                  # Stock analyzer
│   │   ├── portfolio/                # Live positions
│   │   ├── performance/              # System metrics
│   │   ├── trades/                   # Trade journal
│   │   ├── intelligence/             # Market intelligence
│   │   ├── about/                    # About page
│   │   ├── sitemap.ts                # SEO sitemap
│   │   └── robots.ts                 # Crawler rules
│   ├── components/               # Reusable UI components
│   │   ├── PickCard.tsx              # Stock pick with real reasoning
│   │   ├── ChartAnalyzerCard.tsx     # AI chart upload
│   │   ├── OrderBookCard.tsx         # Live order book
│   │   ├── PortfolioCard.tsx         # Portfolio summary
│   │   └── PerformanceCard.tsx       # Performance snapshot
│   └── lib/
│       ├── api.ts                    # API client + types
│       └── dashboard-cache.tsx       # Persistent cache provider
└── README.md
```

---

## SEO & Indexing

- Canonical URLs on every page (prevents Google "duplicate content" warnings)
- Structured sitemap at `/sitemap.xml`
- Per-page metadata with unique titles and descriptions
- Open Graph + Twitter Card tags for social sharing
- Dynamic trade pages are `noindex` to prevent crawl bloat
- Trailing slash enforcement via `next.config.ts`

---

## Author

**Vaibhav S** — Full-Stack Developer & Quantitative Systems Architect

- [Portfolio](https://vaibhavology.vercel.app)
- [GitHub](https://github.com/vaibhavology)
- [LinkedIn](https://linkedin.com/in/vaibhavology)

---

<p align="center">
  <sub>⚠️ <strong>Disclaimer:</strong> TradingXtra is a mathematical and AI-driven analysis tool built for educational and research purposes. It is not financial advice. All trades carry inherent risk. Past performance does not guarantee future results.</sub>
</p>
