# Backend API Specification

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     FRONTEND (Next.js)                          │
│  - Consumes API-style JSON only                                 │
│  - No business logic                                            │
│  - Decision display only                                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     BACKEND API LAYER                           │
│  FastAPI / Node.js - Stateless, Async-ready                     │
├─────────────────────────────────────────────────────────────────┤
│  /api/market-status    │  /api/today-picks   │  /api/sectors    │
│  /api/chat             │  /api/chart-analysis │  /api/scanner   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                 FINAL DECISION ENGINE                           │
│  - Aggregates all agent outputs                                 │
│  - Applies hard risk rules                                      │
│  - Resolves conflicts                                           │
│  - Produces FINAL Top 10 only                                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   ADVISORY AGENTS (Non-authoritative)           │
├─────────────────────────────────────────────────────────────────┤
│  Technical Agent    │  Fundamental Agent  │  News/Budget Agent  │
│  FII/DII Agent      │  Sentiment Agent    │  Chart Vision Agent │
│  Cross-Platform Verification Agent                              │
└─────────────────────────────────────────────────────────────────┘
```

## API Endpoints

### GET /api/market-status

Returns current market indices and flow data.

```json
{
  "success": true,
  "data": {
    "nifty": { "value": 21892.75, "change": 0.42, "direction": "up" },
    "bankNifty": { "value": 46234.50, "change": -0.18, "direction": "down" },
    "indiaVix": { "value": 13.25, "change": -2.1 },
    "fiiFlow": { "value": 1245.32, "type": "buy" },
    "diiFlow": { "value": 892.15, "type": "buy" },
    "lastUpdated": "2024-01-15T10:30:00Z",
    "marketOpen": true
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### GET /api/today-picks

Returns FINAL decisions only (post Decision Engine).

```json
{
  "success": true,
  "data": [
    {
      "id": "1",
      "symbol": "RELIANCE",
      "name": "Reliance Industries",
      "direction": "LONG",
      "entryZone": { "low": 2420, "high": 2445 },
      "stopLoss": 2385,
      "target1": 2510,
      "target2": 2580,
      "expectedMove": 3.8,
      "confidence": 82,
      "pattern": {
        "name": "Bull Flag",
        "timeframe": "Daily",
        "confidence": 78,
        "keyLevels": {
          "support": [2400, 2350],
          "resistance": [2500, 2580]
        }
      },
      "reasoning": [
        "Strong accumulation near 200 DMA with rising volumes",
        "Sector rotation favoring energy; FII buying in cash segment"
      ],
      "crossCheck": {
        "status": "OK",
        "issues": [],
        "platformsChecked": 4
      },
      "riskReward": 2.1,
      "sector": "Energy"
    }
  ],
  "timestamp": "2024-01-15T09:15:00Z"
}
```

### GET /api/sectors

Returns sector analysis with top picks.

```json
{
  "success": true,
  "data": [
    {
      "name": "Banking & Financials",
      "direction": "bullish",
      "reason": "Credit growth momentum, NIM expansion, FII accumulation",
      "topPick": "ICICI Bank",
      "topPickSymbol": "ICICIBANK",
      "strength": 85
    }
  ],
  "timestamp": "2024-01-15T09:15:00Z"
}
```

### POST /api/chat

Chat with the research assistant.

Request:
```json
{
  "message": "Why is ICICIBANK selected?",
  "context": {
    "currentPicks": ["ICICIBANK", "RELIANCE"],
    "sessionId": "abc123"
  }
}
```

Response:
```json
{
  "success": true,
  "data": {
    "response": "ICICIBANK was selected based on...",
    "sources": ["technical", "fundamental", "flow"],
    "confidence": 84
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### POST /api/chart-analysis

Analyze uploaded chart image.

Request:
```json
{
  "image": "base64_encoded_image_data",
  "symbol": "RELIANCE",
  "timeframe": "Daily"
}
```

Response:
```json
{
  "success": true,
  "data": {
    "pattern": "Ascending Triangle",
    "timeframe": "Daily",
    "suggestedEntry": { "low": 1520, "high": 1545 },
    "suggestedSL": 1485,
    "suggestedTP": [1610, 1680],
    "confidence": 72,
    "notes": "Pattern shows higher lows with horizontal resistance...",
    "isAIAssisted": true
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### GET /api/scanner

Scan stocks based on filters.

Query Parameters:
- `direction`: "LONG" | "SHORT" | "all"
- `minConfidence`: number (0-100)
- `sector`: string
- `pattern`: string
- `page`: number
- `limit`: number

Response:
```json
{
  "success": true,
  "data": {
    "results": [...],
    "total": 45,
    "page": 1,
    "limit": 20
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## Decision Engine Rules (HARD - Cannot Be Overridden)

1. **Market Regime Conflict** → REJECT
   - If setup contradicts current market regime

2. **SL Risk Beyond Limits** → REJECT
   - If stop-loss exceeds user's max risk per trade

3. **Agent Disagreement** → REJECT
   - If ≥2 major agents strongly disagree

4. **Manipulation Flag** → REJECT or DOWNGRADE
   - Any governance or manipulation flag from cross-platform check

5. **Social Hype Override** → BLOCKED
   - Social sentiment cannot override fundamentals + risk

6. **Pattern Confidence Override** → BLOCKED
   - Pattern confidence cannot override SL discipline

## Cross-Platform Verification

The system compares signals across:
- Other screeners / research platforms
- Broker insights
- Analyst consensus summaries
- Social sentiment sources

Purpose: Detect contradictions, hidden risks, manipulation, pump-and-dump patterns.

Example Output:
```json
{
  "crossCheck": {
    "status": "WARNING",
    "issues": [
      "Unusual volume spike without news",
      "Conflicting analyst sentiment",
      "Negative governance flag on alternate platform"
    ],
    "platformsChecked": 4
  }
}
```

## Error Handling

All endpoints return consistent error format:

```json
{
  "success": false,
  "error": "Error message here",
  "code": "ERROR_CODE",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

Error Codes:
- `MARKET_CLOSED`: Market is closed
- `RATE_LIMITED`: Too many requests
- `INVALID_INPUT`: Invalid request parameters
- `AGENT_TIMEOUT`: Advisory agent timeout
- `DECISION_ENGINE_ERROR`: Decision engine failure
