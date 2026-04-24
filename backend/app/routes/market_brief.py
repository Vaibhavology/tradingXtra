"""
TradingXtra — Market Brief & News Routes

Endpoints:
    GET /api/market-brief  → structured market intelligence + invest smart
    GET /api/news          → filtered news feed
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Query

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "/market-brief",
    summary="Today's Market Brief",
    description=(
        "Generates a structured market briefing:\n"
        "- Market bias (Bullish/Bearish/Neutral)\n"
        "- Global & India drivers (max 3 each)\n"
        "- Sector strength (strong/weak)\n"
        "- Risk alerts (max 3)\n"
        "- Trading guidance\n"
        "- Invest Smart (YouTube stock suggestions)"
    ),
)
async def market_brief():
    """Generate today's market brief."""
    try:
        from app.services.market_brief import generate_brief
        return generate_brief()
    except Exception as e:
        logger.error(f"Market brief failed: {e}", exc_info=True)
        return {
            "bias": "Neutral",
            "behavior": "Unknown",
            "nifty_return_5d": 0.0,
            "nifty_return_1d": 0.0,
            "vix": None,
            "scores": {"global_score": 0, "india_score": 0, "volatility_score": 0, "bias_score": 0},
            "regime": {"regime": "unknown", "confidence": 0.0},
            "drivers": {"global": [], "india": []},
            "sector_strength": {"strong": [], "weak": []},
            "risk_alerts": [f"Brief generation error: {str(e)}"],
            "guidance": ["System error — use manual analysis"],
            "invest_smart": None,
            "timestamp": None,
        }


@router.post(
    "/invest-smart/refresh",
    summary="Refresh Invest Smart Video",
    description="Manually triggers a check for new YouTube video and hits Gemini if new.",
)
async def refresh_invest_smart():
    """Force refresh the Invest Smart analysis."""
    try:
        from app.services.market_brief import force_refresh_invest_smart
        result = force_refresh_invest_smart()
        if result:
            return {"status": "success", "data": result}
        else:
            return {"status": "error", "message": "Failed to fetch or analyze video."}
    except Exception as e:
        logger.error(f"Invest Smart refresh failed: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}


@router.get(
    "/news",
    summary="Market News Feed",
    description="Returns classified and scored market news from Google News RSS.",
)
async def get_news(
    limit: int = Query(20, ge=1, le=50, description="Max items to return"),
    category: str = Query(None, description="Filter: GLOBAL, INDIA, SECTOR, STOCK, RISK"),
    symbol: str = Query(None, description="Filter news by stock symbol"),
):
    """Get classified market news."""
    try:
        from app.services.news_service import fetch_news, get_stock_news

        if symbol:
            items = get_stock_news(symbol.upper())
        else:
            items = fetch_news()

        if category:
            items = [n for n in items if n["category"] == category.upper()]

        return {
            "items": items[:limit],
            "total": len(items),
            "filtered_by": {"category": category, "symbol": symbol},
        }
    except Exception as e:
        logger.error(f"News fetch failed: {e}", exc_info=True)
        return {"items": [], "total": 0, "error": str(e)}
