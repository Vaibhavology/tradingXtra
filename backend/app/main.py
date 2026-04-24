"""
TradingXtra Phase 1 — Momentum Decision Engine

FastAPI entry point with:
  - Background data preloading on startup
  - 15-minute scheduled refresh via APScheduler
  - Phase 1 decision routes + legacy backward compat
"""

import logging
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings

# ── Logging ──────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("tradingxtra")

# Quiet noisy libraries
logging.getLogger("yfinance").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("apscheduler").setLevel(logging.WARNING)

_scheduler = None


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

    # 2. Start background data preload (non-blocking)
    try:
        from app.data_fetcher import preload_all_stocks
        preload_thread = threading.Thread(
            target=preload_all_stocks,
            daemon=True,
            name="data-preloader",
        )
        preload_thread.start()
        logger.info("✓ Data preloading started in background")
    except Exception as e:
        logger.warning(f"✗ Preload failed to start: {e}")

    # 3. Start scheduler for periodic refresh + trade monitor
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from app.data_fetcher import refresh_all_stocks
        from app.services.trade_monitor import check_open_trades

        _scheduler = BackgroundScheduler()
        _scheduler.add_job(
            refresh_all_stocks,
            "interval",
            minutes=15,
            id="ohlcv_refresh",
            max_instances=1,
        )
        _scheduler.add_job(
            check_open_trades,
            "interval",
            minutes=5,
            id="trade_monitor",
            max_instances=1,
        )
        _scheduler.start()
        logger.info("✓ Scheduler started (15-min data + 5-min trade monitor)")
    except ImportError:
        logger.warning("✗ APScheduler not installed — auto-refresh disabled")
    except Exception as e:
        logger.warning(f"✗ Scheduler failed: {e}")

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
        "database": {
            "total_rows": total_rows,
            "symbols_tracked": symbol_count,
        },
    }


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
