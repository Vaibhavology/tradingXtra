"""
TradingXtra Phase 4 — Portfolio Routes

Endpoints:
    GET /api/portfolio           → Full portfolio state
    GET /api/portfolio/positions → Open positions with current P&L
    GET /api/portfolio/exposure  → Exposure breakdown (total + sector)
"""

import logging
from fastapi import APIRouter

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "/portfolio",
    summary="Full portfolio state",
    description=(
        "Returns capital, positions, exposure, sector breakdown, "
        "and key metrics for the active portfolio."
    ),
    tags=["Phase 4 — Portfolio"],
)
async def portfolio_state():
    from app.services.portfolio import get_portfolio_state
    return get_portfolio_state()


@router.get(
    "/portfolio/positions",
    summary="Open positions",
    description="Returns all open positions with current market prices and unrealized P&L.",
    tags=["Phase 4 — Portfolio"],
)
async def portfolio_positions():
    from app.services.portfolio import get_open_positions
    positions = get_open_positions()
    total_unrealized = sum(p["unrealized_pnl"] for p in positions)
    return {
        "positions": positions,
        "count": len(positions),
        "total_unrealized_pnl": round(total_unrealized, 2),
    }


@router.get(
    "/portfolio/exposure",
    summary="Exposure breakdown",
    description=(
        "Returns total portfolio exposure and per-sector breakdown "
        "with limit status indicators."
    ),
    tags=["Phase 4 — Portfolio"],
)
async def portfolio_exposure():
    from app.services.portfolio import compute_exposure
    return compute_exposure()
