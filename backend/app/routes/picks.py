"""Today's Top 10 Picks endpoint - THE CORE OUTPUT"""

from fastapi import APIRouter
from app.services.decision_engine import DecisionEngine
from app.models.schemas import TodayPicksResponse

router = APIRouter()
engine = DecisionEngine()

@router.get("/today-picks", response_model=TodayPicksResponse)
async def get_today_picks():
    """
    Get Today's Top 10 Momentum Stocks.
    
    This is the FINAL output from the Decision Engine.
    All stocks have passed:
    - Momentum Gate (≥4-6% move in 5-10 sessions)
    - Volume Gate (≥1.5x 20-day average)
    - Sector Gate (sector outperforming NIFTY)
    - Manipulation Filter
    - Risk Rules
    
    Frontend receives ONLY final decisions.
    """
    return engine.get_today_picks()

@router.get("/picks-debug")
async def get_picks_debug():
    """Debug endpoint showing full decision process (not for production)"""
    return engine.get_debug_output()

@router.get("/picks-refresh")
async def refresh_picks():
    """Force-invalidate cache and re-run the pipeline"""
    from app.services import data_cache
    data_cache.invalidate()
    return engine.get_today_picks()
