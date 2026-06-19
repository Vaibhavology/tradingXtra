"""
TradingXtra Phase 1 — Momentum Decision Engine

FastAPI entry point with:
  - Background data preloading on startup
  - 15-minute scheduled refresh via APScheduler
  - Phase 1 decision routes + legacy backward compat
"""

import logging
import os
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings

# ── Logging ──────────────────────────────────────────────────────────
_log_level = logging.DEBUG if settings.DEBUG else logging.INFO
_log_format = (
    '{"time":"%(asctime)s","name":"%(name)s","level":"%(levelname)s","msg":"%(message)s"}'
    if settings.ENVIRONMENT == "production"
    else "%(asctime)s [%(name)s] %(levelname)s: %(message)s"
)
logging.basicConfig(
    level=_log_level,
    format=_log_format,
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("tradingxtra")

# Quiet noisy libraries
logging.getLogger("yfinance").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("apscheduler").setLevel(logging.WARNING)

_scheduler = None


# ── Daily Morning Refresh (Cron) ──────────────────────────────────────
def daily_morning_refresh():
    """
    Daily morning refresh scheduled for 6:30 AM IST.
    1. Refreshes OHLCV data for all stocks.
    2. Runs a full batch evaluation of all stocks.
    3. Regenerates the market brief and caches it.
    """
    import time
    logger.info("=" * 60)
    logger.info("  DAILY MORNING REFRESH STARTING...")
    logger.info("=" * 60)

    start_time = time.time()
    try:
        from app.data_fetcher import refresh_all_stocks
        logger.info("1/3: Refreshing OHLCV data...")
        refresh_all_stocks()

        from app.services.batch_evaluator import full_batch
        logger.info("2/3: Running full batch evaluation...")
        full_batch()

        from app.services.market_brief import generate_brief
        logger.info("3/3: Regenerating market brief...")
        generate_brief(force_refresh=True)

        duration = time.time() - start_time
        logger.info("=" * 60)
        logger.info(f"  DAILY MORNING REFRESH COMPLETE in {duration:.1f}s")
        logger.info("=" * 60)
    except Exception as e:
        logger.error(f"Daily morning refresh failed: {e}", exc_info=True)


# ── Lifespan (startup + shutdown) ────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    global _scheduler

    logger.info("=" * 60)
    logger.info("  TradingXtra Phase 3 — Starting...")
    logger.info("=" * 60)

    # 0. Load ML Calibrated Weights
    try:
        from app.services.calibration import load_calibrated_weights
        load_calibrated_weights()
    except Exception as e:
        logger.warning(f"Failed to load calibrated weights: {e}")

    # 1. Initialize database (creates tables including FetchTracker)
    try:
        from app.database import init_db
        init_db()
        logger.info("✓ Database initialized")
    except Exception as e:
        logger.error(f"✗ Database init failed: {e}")
        logger.error("  Set DATABASE_URL in .env (see README.md)")

    # 2. Start scheduler for trade monitor + daily morning refresh
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from app.services.trade_monitor import check_open_trades

        _scheduler = BackgroundScheduler()

        # Trade monitor (check SL/target hits)
        _scheduler.add_job(
            check_open_trades,
            "interval",
            minutes=5,
            id="trade_monitor",
            max_instances=1,
        )

        # Daily morning refresh at 6:30 AM IST (Asia/Kolkata timezone)
        from apscheduler.triggers.cron import CronTrigger
        from zoneinfo import ZoneInfo
        _scheduler.add_job(
            daily_morning_refresh,
            trigger=CronTrigger(hour=6, minute=30, timezone=ZoneInfo("Asia/Kolkata")),
            id="daily_morning_refresh",
            max_instances=1,
        )

        _scheduler.start()
        logger.info("✓ Scheduler started (trade monitor + daily morning refresh)")
    except ImportError:
        logger.warning("✗ APScheduler not installed — auto-refresh disabled")
    except Exception as e:
        logger.warning(f"✗ Scheduler failed: {e}")

    # 3. Immediately seed scan cache from DB (so /api/scan isn't empty)
    try:
        from app.services.evaluation_cache import get_all_db_results, store_batch_results
        db_results = get_all_db_results(max_age_min=None)  # Load all DB results
        if db_results:
            store_batch_results(db_results)
            logger.info(f"✓ Scan cache seeded from DB: {len(db_results)} results")
        else:
            logger.info("  No existing DB results to seed scan cache")
    except Exception as e:
        logger.warning(f"✗ Scan cache seed failed: {e}")

    logger.info("")
    logger.info("  Phase 4 Endpoints:")
    logger.info("    GET  /api/decision?symbol=RELIANCE&record=true")
    logger.info("    GET  /api/portfolio")
    logger.info("    GET  /api/portfolio/exposure")
    logger.info("    GET  /api/trades")
    logger.info("    GET  /api/performance")
    logger.info("    POST /api/backtest")
    logger.info("    GET  /docs  (Swagger UI)")
    logger.info("")

    yield

    # ── SHUTDOWN ──
    # Signal data fetcher threads to stop first
    try:
        from app.data_fetcher import shutdown_fetcher
        shutdown_fetcher()
    except Exception as e:
        logger.warning(f"Data fetcher shutdown error: {e}")

    if _scheduler:
        _scheduler.shutdown(wait=False)
    logger.info("TradingXtra shutting down")


# ── FastAPI App ──────────────────────────────────────────────────────
app = FastAPI(
    title="TradingXtra Phase 4 — Portfolio Decision Engine",
    description=(
        "EV-based stock evaluation with portfolio risk management.\n\n"
        "**Pipeline:** Data → Agents → Features → "
        "Regime-Adjusted WScore → P(win) → EV → Portfolio Gates → Accept/Reject\n\n"
        "Includes portfolio engine, exposure control, correlation filtering, and backtesting."
    ),
    version="5.0.0",
    lifespan=lifespan,
)

# Apply Rate Limiting Middleware (Security)
from app.middleware import RateLimitMiddleware
app.add_middleware(RateLimitMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Phase 1 Routes ──────────────────────────────────────────────────
from app.routes.decision import router as decision_router
app.include_router(decision_router, prefix="/api", tags=["Decisions"])

# ──────────────────────────────── Phase 2 Routes (market brief + news) ────────────────────────────────
from app.routes.market_brief import router as brief_router
app.include_router(brief_router, prefix="/api", tags=["Phase 2 — Market Intel"])

# ──────────────────────────────── Phase 3 Routes (trades + performance + backtest) ────────────────────────────────
from app.routes.trades import router as trades_router
app.include_router(trades_router, prefix="/api")

# ──────────────────────────────── Phase 4 Routes (portfolio) ────────────────────────────────
from app.routes.portfolio import router as portfolio_router
app.include_router(portfolio_router, prefix="/api")

# ──────────────────────────────── Phase 5 Routes (Chart Analyzer) ────────────────────────────────
from app.routes.chart_analyzer import router as chart_analyzer_router
app.include_router(chart_analyzer_router, prefix="/api", tags=["Analyzer"])

# ──────────────────────────────── WebSockets ────────────────────────────────
from app.routes.ws import router as ws_router
app.include_router(ws_router, prefix="/api")

# ──────────────────────────────── Phase 6 (Stock Analyzer) ──────────────────
@app.get("/api/analyze-stock/{symbol}", tags=["Phase 6 — Stock Analyzer"])
async def analyze_stock_endpoint(symbol: str):
    try:
        from app.services.stock_analyzer import StockAnalyzerService
        svc = StockAnalyzerService()
        return svc.analyze(symbol)
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error analyzing stock {symbol}: {e}")
        return {"error": str(e)}

# ── Legacy Routes ────────────────────────────────────────────────────
try:
    from app.routes import picks, market, health, twitter
    app.include_router(health.router, prefix="/api", tags=["Legacy"])
    app.include_router(market.router, prefix="/api", tags=["Legacy"])
    app.include_router(picks.router, prefix="/api", tags=["Legacy"])
    app.include_router(twitter.router, prefix="/api", tags=["Legacy"])
except ImportError:
    pass


# ── Admin & Status Endpoints ────────────────────────────────────────

@app.get("/api/status", tags=["Admin"])
async def system_status():
    """
    System health: preload progress, cache size, DB row count.
    """
    from app.data_fetcher import get_preload_status
    from app.database import SessionLocal, OHLCVData
    from sqlalchemy import func

    preload = get_preload_status()

    db = SessionLocal()
    try:
        total_rows = db.query(func.count(OHLCVData.id)).scalar()
        symbol_count = db.query(func.count(func.distinct(OHLCVData.symbol))).scalar()
    finally:
        db.close()

    return {
        "server": "running",
        "preload": preload,
        "batch_evaluator": _get_batch_status_safe(),
        "database": {
            "total_rows": total_rows,
            "symbols_tracked": symbol_count,
        },
    }


def _get_batch_status_safe():
    """Get batch evaluator status without crashing if not available."""
    try:
        from app.services.batch_evaluator import get_batch_status
        return get_batch_status()
    except Exception:
        return {"status": "unavailable"}


@app.post("/api/backfill", tags=["Admin"])
async def trigger_backfill():
    """Manually trigger full data preload in background."""
    from app.data_fetcher import preload_all_stocks

    thread = threading.Thread(
        target=preload_all_stocks,
        daemon=True,
        name="manual-backfill",
    )
    thread.start()

    return {
        "status": "backfill_started",
        "message": "Preloading all stocks in background. Check /api/status for progress.",
    }


@app.get("/api/db-stats", tags=["Admin"])
async def db_stats():
    """Detailed database statistics — rows per symbol with date range."""
    from app.database import SessionLocal, OHLCVData
    from sqlalchemy import func

    db = SessionLocal()
    try:
        total = db.query(func.count(OHLCVData.id)).scalar()
        symbols = (
            db.query(
                OHLCVData.symbol,
                func.count(OHLCVData.id),
                func.min(OHLCVData.timestamp),
                func.max(OHLCVData.timestamp),
            )
            .group_by(OHLCVData.symbol)
            .order_by(OHLCVData.symbol)
            .all()
        )

        return {
            "total_rows": total,
            "symbols": {
                s[0]: {
                    "rows": s[1],
                    "from": s[2].isoformat() if s[2] else None,
                    "to": s[3].isoformat() if s[3] else None,
                }
                for s in symbols
            },
        }
    finally:
        db.close()
