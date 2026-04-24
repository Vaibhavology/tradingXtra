"""
TradingXtra Phase 3 — Trade, Performance & Backtest Routes

Endpoints:
    GET  /api/trades              → list all trades
    GET  /api/trades/open         → list open trades
    POST /api/trades/monitor      → trigger trade monitor
    GET  /api/performance         → aggregate metrics
    GET  /api/performance/regime  → breakdown by regime
    POST /api/backtest            → run backtest
"""

import logging
import threading
from typing import Optional, List

from fastapi import APIRouter, Query

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Trade Endpoints ──────────────────────────────────────────────────

@router.get(
    "/trades",
    summary="List all trades",
    description="Returns recent trades ordered by timestamp descending.",
    tags=["Phase 3 — Trades"],
)
async def list_trades(
    limit: int = Query(50, ge=1, le=500, description="Max trades to return"),
    status: str = Query(None, description="Filter: OPEN or CLOSED"),
):
    from app.services.trade_monitor import get_all_trades
    trades = get_all_trades(limit=limit)
    if status:
        trades = [t for t in trades if t["status"] == status.upper()]
    return {"trades": trades, "count": len(trades)}


@router.get(
    "/trades/open",
    summary="List open trades",
    tags=["Phase 3 — Trades"],
)
async def list_open_trades():
    from app.services.trade_monitor import get_open_trades
    trades = get_open_trades()
    return {"trades": trades, "count": len(trades)}


@router.post(
    "/trades/monitor",
    summary="Run trade monitor",
    description="Checks all open trades against current prices, closes any that hit target or SL.",
    tags=["Phase 3 — Trades"],
)
async def run_monitor():
    from app.services.trade_monitor import check_open_trades
    return check_open_trades()


# ── Performance Endpoints ────────────────────────────────────────────

@router.get(
    "/performance",
    summary="Aggregate performance metrics",
    description=(
        "Computes: win rate, profit factor, max drawdown, "
        "average win/loss, MFE/MAE, and calibration analysis."
    ),
    tags=["Phase 3 — Performance"],
)
async def performance_metrics():
    from app.services.performance import compute_metrics
    return compute_metrics()


@router.get(
    "/performance/regime",
    summary="Performance by regime",
    description="Breaks down win rate and PnL by the market regime at entry time.",
    tags=["Phase 3 — Performance"],
)
async def performance_by_regime():
    from app.services.performance import compute_by_regime
    return compute_by_regime()


@router.post(
    "/performance/calibrate",
    summary="Auto-calibrate Engine",
    description="Adjusts agent weights based on historical trade outcomes to maximize Profit Factor.",
    tags=["Phase 3 — Performance"],
)
async def calibrate_engine():
    from app.services.calibration import run_auto_calibration
    return run_auto_calibration()


# ── Backtest Endpoint ────────────────────────────────────────────────

@router.post(
    "/backtest",
    summary="Run backtest",
    description=(
        "Simulates decisions through historical data using the existing engine.\n"
        "Returns win rate, profit factor, and per-symbol breakdown.\n\n"
        "⚠️ This can take 30-60 seconds for the full universe."
    ),
    tags=["Phase 3 — Backtest"],
)
async def run_backtest(
    symbols: str = Query(
        None,
        description="Comma-separated symbols (e.g., RELIANCE,TCS,HAL). Omit for all.",
    ),
    lookback_days: int = Query(60, ge=30, le=180, description="Days of history"),
):
    from app.services.backtest import run_backtest as _run

    sym_list = None
    if symbols:
        sym_list = [s.strip().upper() for s in symbols.split(",")]

    return _run(symbols=sym_list, lookback_days=lookback_days)
