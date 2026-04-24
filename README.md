# 🚀 TradingXtra – Intelligent Quantitative Trading Terminal

**TradingXtra** is a high-fidelity, institutional-grade quantitative trading terminal. It bridges the gap between algorithmic rigor and discretionary trading by combining real-time market data ingestion, automated expected value (EV) calculations, and Google Gemini-powered multimodal AI to deliver a "Decision-First" market command center.

Designed to eliminate emotion from trading, the system automatically evaluates setups, manages portfolio risk exposure, and tracks performance metrics (MFE/MAE) with zero manual data entry.

---

## 🛠️ Tech Stack & Tools Used

### Backend Engine (Quantitative & AI Services)
* **Framework:** FastAPI (Python 3.10+)
* **Data Ingestion:** `yfinance` (Real-time OHLCV equities & indices)
* **Intelligence Layer:** Google Gemini 2.5 Flash/Pro (Multimodal AI, Text & Image)
* **Alternative Data:** `youtube-transcript-api` (Automated extraction of stock mentions from analyst videos), RSS feeds (Global/Domestic Market Drivers)
* **Database:** SQLite + SQLAlchemy (Trade Journaling & Portfolio State)
* **Architecture:** Multi-Agent System (Sector Analysis, Regime Detection, Decision Engine)

### Frontend Terminal (User Interface)
* **Framework:** Next.js 14 (React, App Router)
* **Styling:** Tailwind CSS (Custom Dark Mode "Terminal" Aesthetic, Glassmorphism, Micro-interactions)
* **Visualizations:** Chart.js (`react-chartjs-2`) for Equity Curves
* **State Management:** React Hooks + Server-Side API Fetching (`fetch`)
* **Icons:** Standard Emojis + Lucide-React 

---

## 🧠 Core Architecture & Data Flow

TradingXtra operates on a strict, unidirectional data pipeline ensuring that all insights presented to the user are backed by mathematical evaluation or contextual AI parsing.

1. **Market State Ingestion:** The backend continuously monitors `INDIAVIX`, `NIFTY50`, and `INR=X` (USD/INR) to determine the current Market Regime (Trending, Volatile, Sideways).
2. **Signal Generation / Intelligence:**
   * **Quantitative:** Mathematical models calculate ATR (Average True Range) and historical probability for specific setups.
   * **Alternative:** The `market_brief` service parses YouTube video transcripts via API and intercepts RSS feeds to extract "Smart Money" sentiment and macroeconomic alerts.
3. **The Decision Engine:** Before a trade is recommended, it passes through the Decision Engine. The engine calculates the **Expected Value (EV)** and **Risk/Reward ratio**. If a trade fails the mathematical threshold, it is explicitly *Rejected* with a visible reason.
4. **Terminal Delivery:** The Next.js frontend fetches these processed endpoints (`/scan`, `/market-brief`, `/portfolio`) and renders them asynchronously in a prioritized hierarchy: *Market State → Actionable Opportunities → Risk Context.*

---

## 🔄 User Flow (The "Decision-First" Experience)

TradingXtra is designed to mimic the workflow of a professional hedge fund desk:

1. **Dashboard (Command Center):** The user lands on the dashboard. Instantly, they are presented with a dominant "Market State" read (e.g., BULLISH DAY, 85% Confidence). 
2. **Risk Assessment:** The user checks the "Macro Indicators" (VIX, USD/INR) and expands the interactive **Market Alerts Modal** to read global/domestic catalysts before making any decisions.
3. **Trade Selection:** The user reviews the mathematically verified "Accepted Picks". They immediately see *why* the trade was chosen (Probability, Target, Stop Loss).
4. **Chart Analysis (Multimodal):** If the user finds an external setup, they navigate to `/analyze`, upload a screenshot of the chart, and the Gemini Vision AI instantly returns the pattern, setup strength, and a market prediction.
5. **Execution & Journaling:** Once a trade is executed, it is logged into the `/portfolio`. The system tracks active exposure across sectors and dynamically updates Unrealized PnL.
6. **Performance Review:** The user visits `/performance` to view their automated Equity Curve, Profit Factor, Win Rate, and advanced execution metrics like MFE (Maximum Favorable Excursion) and MAE (Maximum Adverse Excursion).

---

## 📈 Key Performance Metrics Tracked

The system shifts the focus from simple "Win/Loss" to advanced probabilistic metrics:

| Metric | Description | Impact |
|--------|-------------|--------|
| **Expected Value (EV)** | The statistical value of a trade over 100 iterations. | Prevents taking low-probability, high-risk trades. |
| **Capital Utilization** | Percentage of total portfolio actively deployed. | Ensures the user is never over-leveraged during volatile regimes. |
| **MFE / MAE** | Maximum Favorable/Adverse Excursion. | Tracks how much heat a trade took before working, or how much profit was left on the table. |
| **Calibration Score** | Predicted Probability vs. Actual Win Rate. | Validates whether the AI/Quant models are actually accurate over time. |

---

## 🚦 Getting Started

### 1. Clone & Setup Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
```

**Environment Variables (`backend/.env`):**
```env
GEMINI_API_KEY="your_google_gemini_api_key"
```

**Run Backend Service:**
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Setup Frontend Terminal
```bash
cd frontend
npm install
npm run dev
```

The terminal will be live at `http://localhost:3000`.

---
*Disclaimer: TradingXtra is a mathematical and AI-driven analysis tool. It is not financial advice. All trades carry inherent risk.*
