# TradingXtra Phase 1 — Backend

EV-based stock evaluation engine using real NSE market data.

**Pipeline:** OHLCV → Feature Engine → Weighted Score → P(win) → EV → Accept/Reject

---

## Prerequisites

- Python 3.10+
- PostgreSQL 14+ (or SQLite for quick testing)

---

## Setup

### 1. Install dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Database setup

**Option A: PostgreSQL (recommended)**

```bash
# Create the database
psql -U postgres -c "CREATE DATABASE tradingxtra;"

# The .env file already has:
# DATABASE_URL=postgresql://postgres:postgres@localhost:5432/tradingxtra
```

**Option B: SQLite (quick testing, no install needed)**

Edit `.env` and comment/uncomment:

```env
# DATABASE_URL=postgresql://postgres:postgres@localhost:5432/tradingxtra
DATABASE_URL=sqlite:///./tradingxtra.db
```

### 3. Run the server

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Tables are created automatically on startup.

### 4. Initial data load

Trigger the backfill to fetch 120 days of OHLCV data for all 35 stocks:

```bash
curl -X POST http://localhost:8000/api/backfill
```

This runs in the background (~2-3 minutes). Check server logs for progress.

Alternatively, the system **auto-fetches** data on first API call per symbol, so you can skip this step and query directly.

---

## API Endpoints

### `GET /api/decision?symbol=RELIANCE`

Evaluate a single stock.

```bash
curl "http://localhost:8000/api/decision?symbol=RELIANCE"
```

**Response:**

```json
{
  "symbol": "RELIANCE",
  "name": "Reliance Industries",
  "sector": "Energy",
  "score": 0.6234,
  "probability": 0.6741,
  "ev": 18.45,
  "entry": 1285.50,
  "stop_loss": 1251.30,
  "target": 1331.10,
  "atr": 22.80,
  "reward_risk": 1.33,
  "decision": "ACCEPT",
  "rejection_reason": null,
  "features": {
    "PS": 0.7124,
    "MA": 0.5832,
    "SS": 0.5000,
    "VC": 0.6891,
    "LS": 1.0000,
    "SE": 0.5000,
    "MR": 0.0823
  },
  "data_points": 83
}
```

### `GET /api/scan`

Evaluate all 35 stocks. Returns results sorted by EV (accepted first).

```bash
curl "http://localhost:8000/api/scan"
```

### `GET /api/universe`

List all available stock symbols.

```bash
curl "http://localhost:8000/api/universe"
```

### `POST /api/backfill`

Trigger background data backfill for all stocks.

### `GET /api/db-stats`

Show database row counts per symbol.

### `GET /docs`

Interactive Swagger UI documentation.

---

## Architecture

```
Request → FastAPI
            ↓
       data_fetcher.py     ← yfinance → PostgreSQL
            ↓
       feature_engine.py   ← 7 features normalized to [0,1]
            ↓
       decision_engine.py  ← WScore → P(win) → EV → Accept/Reject
            ↓
         Response JSON
```

### Feature Definitions

| Feature | Name | Source | Phase 1 |
|---------|------|--------|---------|
| PS | PatternStrength | Momentum Z + ATR-norm + RSI | ✅ Real |
| MA | MarketAlignment | Stock vs NIFTY50 | ✅ Real |
| SS | SectorStrength | Sector vs market | ⏳ Neutral (0.5) |
| VC | VolumeConfirmation | Volume Z-score | ✅ Real |
| LS | LiquidityScore | Daily turnover | ✅ Real |
| SE | SentimentScore | News pipeline | ⏳ Neutral (0.5) |
| MR | ManipulationRisk | Spike + volume pattern | ✅ Real (simplified) |

### Decision Rules

- **WScore** = Weighted sum of 7 features
- **P(win)** = Logistic sigmoid: `1 / (1 + exp(-10 × (WScore - 0.55)))`
- **Entry** = Last close
- **SL** = Entry - 1.5 × ATR
- **Target** = Entry + 2.0 × ATR
- **EV** = `P(win) × Reward - (1-P(win)) × Risk`
- **REJECT** if: EV ≤ 0, P(win) < 55%, R:R < 1.3, or ATR < ₹0.50

---

## File Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              ← FastAPI app + lifespan + routes
│   ├── config.py             ← Settings from .env
│   ├── database.py           ← PostgreSQL connection + ORM model
│   ├── data_fetcher.py       ← yfinance fetch + stock universe
│   ├── feature_engine.py     ← 7 normalized features
│   ├── decision_engine.py    ← WScore → P(win) → EV → decision
│   ├── routes/
│   │   ├── decision.py       ← Phase 1 API endpoints
│   │   ├── picks.py          ← Legacy endpoints
│   │   ├── market.py
│   │   ├── health.py
│   │   └── twitter.py
│   ├── services/             ← Legacy services (kept for compat)
│   ├── models/
│   └── utils/
│       └── indicators.py     ← TA utilities (SMA, EMA, RSI, ATR)
├── requirements.txt
├── .env
└── README.md
```
