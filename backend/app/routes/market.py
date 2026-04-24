"""Market status endpoint"""

from fastapi import APIRouter
from app.services.decision_engine import DecisionEngine
from app.models.schemas import MarketStatusResponse

router = APIRouter()
engine = DecisionEngine()

@router.get("/market-status", response_model=MarketStatusResponse)
async def get_market_status():
    """Get current market status including NIFTY, VIX, and top sector"""
    return engine.get_market_status()
