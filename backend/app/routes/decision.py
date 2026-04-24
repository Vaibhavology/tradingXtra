"""
TradingXtra Phase 1 — Decision API Routes

Endpoints:
    GET  /api/decision?symbol=RELIANCE   → single stock evaluation
    GET  /api/scan                        → evaluate all stocks in universe
    GET  /api/universe                    → list available symbols
"""

import logging
from typing import Optional, Dict, List

from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel, Field

from app.decision_engine import evaluate

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Response Models ──────────────────────────────────────────────────

class DecisionResponse(BaseModel):
    """Response for a single stock evaluation."""
    symbol: str
    name: str = ""
    sector: str = ""
    score: float = Field(description="Weighted score [0, 1]")
    probability: float = Field(description="Calibrated P(win) [0, 1]")
    ev: float = Field(description="Expected Value in ₹ per share")
    entry: float = Field(description="Entry price (last close)")
    stop_loss: float = Field(description="Stop loss (entry - 1.5×ATR)")
    target: float = Field(description="Target price (entry + 2.0×ATR)")
    atr: float = Field(default=0.0, description="14-period ATR in ₹")
    reward_risk: float = Field(default=0.0, description="Reward:Risk ratio")
    decision: str = Field(description="ACCEPT | REJECT | NO_DATA")
    rejection_reason: Optional[str] = None
    features: Dict[str, float] = Field(
        default={},
        description="7 normalized features: PS, MA, SS, VC, LS, SE, MR",
    )
    # Phase 2 additions
    agents: Dict = Field(default={}, description="Agent outputs (pattern, sector, liquidity, manipulation, regime)")
    regime: str = Field(default="unknown", description="Market regime: trending | sideways | volatile")
    market_bias: str = Field(default="Neutral", description="Market bias: Bullish | Bearish | Neutral")
    reasoning: List[str] = Field(default=[], description="Human-readable reasoning for the decision")
    data_points: int = Field(default=0, description="OHLCV rows used")


class ScanResult(BaseModel):
    """Response for full universe scan."""
    results: List[Dict]
    accepted: int
    rejected: int
    total: int


class SymbolInfo(BaseModel):
    """Stock info for universe listing."""
    symbol: str
    name: str
    sector: str


# ── Endpoints ────────────────────────────────────────────────────────

@router.get(
    "/decision",
    response_model=DecisionResponse,
    summary="Evaluate a single stock",
    description=(
        "Runs the full Phase 1 pipeline: \n"
        "Data → Features → WScore → P(win) → EV → Accept/Reject.\n\n"
        "If the stock has no data in the database, it will be fetched "
        "from yfinance automatically (first call may take a few seconds)."
    ),
)
async def get_decision(
    symbol: str = Query(
        ...,
        description="NSE stock symbol (e.g., RELIANCE, TCS, INFY, TATASTEEL)",
        examples=["RELIANCE", "TCS", "TATASTEEL", "HAL"],
    ),
    record: bool = Query(
        False,
        description="If true, auto-record ACCEPT decisions to trade journal",
    ),
):
    """Evaluate a single stock through the decision pipeline."""
    try:
        result = evaluate(symbol)

        if result.get("decision") == "NO_DATA":
            raise HTTPException(
                status_code=404,
                detail=result.get(
                    "rejection_reason",
                    f"No data available for {symbol}",
                ),
            )

        # Phase 3: auto-record accepted trades
        if record and result.get("decision") == "ACCEPT":
            from app.services.trade_monitor import create_trade
            trade_info = create_trade(result)
            result["trade_recorded"] = trade_info

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Evaluation failed for {symbol}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Evaluation error for {symbol}: {str(e)}",
        )


@router.get(
    "/scan",
    response_model=ScanResult,
    summary="Scan all stocks in the universe",
    description=(
        "Evaluates every stock in the 35-stock NSE universe.\n"
        "Results are sorted: ACCEPTed stocks first (by EV descending), "
        "then REJECTed stocks.\n\n"
        "⚠️ First call with an empty database will trigger data fetch "
        "for all stocks — this may take 2-3 minutes."
    ),
)
async def scan_all():
    """Scan all stocks and return ranked results."""
    from app.data_fetcher import NSE_STOCKS

    results = []
    accepted = 0
    rejected = 0

    for symbol in NSE_STOCKS:
        try:
            result = evaluate(symbol)
            results.append(result)
            if result.get("decision") == "ACCEPT":
                accepted += 1
            else:
                rejected += 1
        except Exception as e:
            logger.error(f"Scan failed for {symbol}: {e}")
            results.append({
                "symbol": symbol,
                "name": NSE_STOCKS[symbol]["name"],
                "sector": NSE_STOCKS[symbol]["sector"],
                "score": 0.0,
                "probability": 0.0,
                "ev": 0.0,
                "entry": 0.0,
                "stop_loss": 0.0,
                "target": 0.0,
                "decision": "ERROR",
                "rejection_reason": str(e),
                "features": {},
                "data_points": 0,
            })
            rejected += 1

    # Sort: ACCEPT first (by EV desc), then REJECT, then ERROR
    def sort_key(r):
        priority = {"ACCEPT": 0, "REJECT": 1, "ERROR": 2, "NO_DATA": 3}
        return (priority.get(r.get("decision", "ERROR"), 9), -(r.get("ev", 0) or 0))

    results.sort(key=sort_key)

    return {
        "results": results,
        "accepted": accepted,
        "rejected": rejected,
        "total": len(results),
    }


@router.get(
    "/universe",
    response_model=List[SymbolInfo],
    summary="List all available stock symbols",
)
async def list_universe():
    """Return the list of all stocks in the trading universe."""
    from app.data_fetcher import NSE_STOCKS

    return [
        {"symbol": sym, "name": info["name"], "sector": info["sector"]}
        for sym, info in sorted(NSE_STOCKS.items())
    ]
