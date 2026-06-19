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
    fresh: bool = Query(
        False,
        description="If true, bypass cache and force fresh evaluation",
    ),
):
    """Evaluate a single stock. Uses cache when available (<5ms)."""
    try:
        from app.services.evaluation_cache import get_cached_result, store_result

        # Check cache first (unless fresh=True)
        if not fresh:
            cached = get_cached_result(symbol)
            if cached:
                logger.info(f"[{symbol}] Serving cached result")
                if record and cached.get("decision") == "ACCEPT":
                    from app.services.trade_monitor import create_trade
                    cached["trade_recorded"] = create_trade(cached)
                return cached

        # Cache miss — live evaluation
        result = evaluate(symbol)

        if result.get("decision") == "NO_DATA":
            raise HTTPException(
                status_code=404,
                detail=result.get(
                    "rejection_reason",
                    f"No data available for {symbol}",
                ),
            )

        # Store to cache for future requests
        store_result(symbol, result)

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
    response_model=None,
    summary="Scan all stocks in the universe",
    description=(
        "Returns pre-computed evaluation results for all tracked stocks.\n"
        "Results are computed in background (batch + incremental refresh)\n"
        "and served from cache in <50ms.\n\n"
        "Use `?lite=true` for a smaller payload (mobile-friendly).\n"
        "If cache is empty (first startup), triggers a background batch\n"
        "and returns partial/empty results."
    ),
)
async def scan_all(
    lite: bool = Query(
        False,
        description="If true, return lightweight results (no agents/features/reasoning)",
    ),
):
    """Serve pre-computed scan results from cache. <50ms response."""
    from app.services.evaluation_cache import get_cached_scan, get_all_db_results

    # Tier 1: Memory cache (< 1ms)
    cached = get_cached_scan()
    if cached:
        if lite:
            cached = _make_lite(cached)
        return cached

    # Tier 2: Rebuild from DB (accept up to 4 hours old)
    db_results = get_all_db_results(max_age_min=240)
    if db_results and len(db_results) > 5:
        accepted = sum(1 for r in db_results if r.get("decision") == "ACCEPT")
        rejected = len(db_results) - accepted

        def sort_key(r):
            priority = {"ACCEPT": 0, "REJECT": 1, "ERROR": 2, "NO_DATA": 3}
            return (priority.get(r.get("decision", "ERROR"), 9), -(r.get("ev", 0) or 0))

        db_results.sort(key=sort_key)

        result = {
            "results": db_results,
            "accepted": accepted,
            "rejected": rejected,
            "total": len(db_results),
        }
        if lite:
            result = _make_lite(result)
        return result

    # Tier 3: Nothing cached — trigger background batch, return empty
    import threading
    from app.services.batch_evaluator import full_batch, get_batch_status

    status = get_batch_status()
    if not status["running"]:
        thread = threading.Thread(target=full_batch, daemon=True, name="scan-batch")
        thread.start()

    return {
        "results": [],
        "accepted": 0,
        "rejected": 0,
        "total": 0,
        "_loading": True,
        "_message": "First scan in progress. Refresh in 30-60 seconds.",
    }


def _make_lite(scan_data: Dict) -> Dict:
    """Strip heavy fields from scan results for mobile bandwidth savings."""
    lite_results = []
    for r in scan_data.get("results", []):
        lite_results.append({
            "symbol": r.get("symbol"),
            "name": r.get("name"),
            "sector": r.get("sector"),
            "score": r.get("score"),
            "probability": r.get("probability"),
            "ev": r.get("ev"),
            "entry": r.get("entry"),
            "stop_loss": r.get("stop_loss"),
            "target": r.get("target"),
            "atr": r.get("atr"),
            "reward_risk": r.get("reward_risk"),
            "decision": r.get("decision"),
            "rejection_reason": r.get("rejection_reason"),
            "regime": r.get("regime"),
            "market_bias": r.get("market_bias"),
            # Omit: agents, features, reasoning (saves ~60% payload)
        })
    return {
        "results": lite_results,
        "accepted": scan_data.get("accepted", 0),
        "rejected": scan_data.get("rejected", 0),
        "total": scan_data.get("total", 0),
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
