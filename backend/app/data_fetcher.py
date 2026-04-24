"""
TradingXtra Phase 1 — Data Fetcher (v2: Caching + Staleness + Timeout)

3-level data resolution:
  1. In-memory cache  (instant, TTL = 15 min)
  2. Database          (fast, persistent)
  3. yfinance fetch    (slow, on-demand with 30s timeout)

All yfinance calls are timeout-wrapped. Startup preloads all symbols
in a background thread so API requests never wait for yfinance.
"""

import logging
import time
import threading
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout

import yfinance as yf
import pandas as pd
from sqlalchemy.orm import Session

from app.database import SessionLocal, OHLCVData, FetchTracker

logger = logging.getLogger(__name__)


# ── Stock Universe ───────────────────────────────────────────────────
NSE_STOCKS: Dict[str, Dict] = {
    "RELIANCE":   {"name": "Reliance Industries",      "sector": "Energy"},
    "TCS":        {"name": "Tata Consultancy Services", "sector": "IT"},
    "HDFCBANK":   {"name": "HDFC Bank",                 "sector": "Banking"},
    "INFY":       {"name": "Infosys",                   "sector": "IT"},
    "ICICIBANK":  {"name": "ICICI Bank",                "sector": "Banking"},
    "HINDUNILVR": {"name": "Hindustan Unilever",        "sector": "FMCG"},
    "SBIN":       {"name": "State Bank of India",       "sector": "PSU Banks"},
    "BHARTIARTL": {"name": "Bharti Airtel",             "sector": "Telecom"},
    "KOTAKBANK":  {"name": "Kotak Mahindra Bank",       "sector": "Banking"},
    "LT":         {"name": "Larsen & Toubro",           "sector": "Infrastructure"},
    "HCLTECH":    {"name": "HCL Technologies",          "sector": "IT"},
    "AXISBANK":   {"name": "Axis Bank",                 "sector": "Banking"},
    "TATAMOTOR":  {"name": "Tata Motors",               "sector": "Auto"},
    "SUNPHARMA":  {"name": "Sun Pharma",                "sector": "Pharma"},
    "WIPRO":      {"name": "Wipro",                     "sector": "IT"},
    "MARUTI":     {"name": "Maruti Suzuki",             "sector": "Auto"},
    "TATASTEEL":  {"name": "Tata Steel",                "sector": "Metals"},
    "NTPC":       {"name": "NTPC",                      "sector": "Energy"},
    "POWERGRID":  {"name": "Power Grid Corp",           "sector": "Energy"},
    "HINDALCO":   {"name": "Hindalco",                  "sector": "Metals"},
    "JSWSTEEL":   {"name": "JSW Steel",                 "sector": "Metals"},
    "ADANIENT":   {"name": "Adani Enterprises",         "sector": "Conglomerate"},
    "COALINDIA":  {"name": "Coal India",                "sector": "Mining"},
    "ONGC":       {"name": "ONGC",                      "sector": "Energy"},
    "BPCL":       {"name": "BPCL",                      "sector": "Energy"},
    "CIPLA":      {"name": "Cipla",                     "sector": "Pharma"},
    "DRREDDY":    {"name": "Dr. Reddy's",               "sector": "Pharma"},
    "DIVISLAB":   {"name": "Divi's Labs",               "sector": "Pharma"},
    "HEROMOTOCO": {"name": "Hero MotoCorp",             "sector": "Auto"},
    "BAJFINANCE": {"name": "Bajaj Finance",             "sector": "NBFC"},
    "M&M":        {"name": "Mahindra & Mahindra",       "sector": "Auto"},
    "TECHM":      {"name": "Tech Mahindra",             "sector": "IT"},
    "HAL":        {"name": "Hindustan Aeronautics",     "sector": "Defence"},
    "BEL":        {"name": "Bharat Electronics",        "sector": "Defence"},
    "VEDL":       {"name": "Vedanta",                   "sector": "Metals"},
}

MARKET_TICKERS: Dict[str, str] = {
    "NIFTY50":  "^NSEI",
    "INDIAVIX": "^INDIAVIX",
}


# ── In-Memory Cache ─────────────────────────────────────────────────
# Structure: {symbol: {"data": [rows...], "loaded_at": datetime}}
_data_cache: Dict[str, Dict] = {}
_CACHE_TTL = 900  # 15 minutes in seconds
_cache_lock = threading.Lock()

# Thread pool for timeout-wrapped yfinance calls
_fetch_pool = ThreadPoolExecutor(max_workers=4)
_FETCH_TIMEOUT = 30  # seconds per symbol

# Preload status (for /api/status endpoint)
_preload_complete = False
_preload_progress = {"done": 0, "total": 0, "errors": 0}


# ── Ticker Resolution ───────────────────────────────────────────────

def _to_yf_ticker(symbol: str) -> str:
    """Convert plain NSE symbol → yfinance ticker."""
    if symbol in MARKET_TICKERS:
        return MARKET_TICKERS[symbol]
    clean = symbol.replace(".NS", "")
    return f"{clean}.NS"


# ── Cache Management ────────────────────────────────────────────────

def _get_cached(symbol: str) -> Optional[List[Dict]]:
    """Return cached data if fresh and has enough rows, else None."""
    with _cache_lock:
        if symbol not in _data_cache:
            return None
        entry = _data_cache[symbol]
        age = (datetime.now() - entry["loaded_at"]).total_seconds()
        if age > _CACHE_TTL:
            return None  # Stale
        return entry["data"]


def _set_cache(symbol: str, data: List[Dict]):
    """Store data in memory cache with current timestamp."""
    with _cache_lock:
        _data_cache[symbol] = {"data": data, "loaded_at": datetime.now()}


def _invalidate(symbol: str):
    """Remove symbol from memory cache (forces DB re-read)."""
    with _cache_lock:
        _data_cache.pop(symbol, None)


# ── Freshness Tracking (DB-backed, survives restarts) ────────────────

def _is_fetch_fresh(symbol: str, max_age_minutes: int = 15) -> bool:
    """Check if yfinance was called for this symbol within max_age_minutes."""
    db = SessionLocal()
    try:
        tracker = (
            db.query(FetchTracker)
            .filter(FetchTracker.symbol == symbol)
            .first()
        )
        if not tracker or not tracker.last_fetched_at:
            return False
        age = (datetime.now() - tracker.last_fetched_at).total_seconds()
        return age < max_age_minutes * 60
    finally:
        db.close()


def _record_fetch(symbol: str, rows: int):
    """Record that we fetched data for this symbol right now."""
    db = SessionLocal()
    try:
        tracker = (
            db.query(FetchTracker)
            .filter(FetchTracker.symbol == symbol)
            .first()
        )
        if tracker:
            tracker.last_fetched_at = datetime.now()
            tracker.rows_fetched = rows
        else:
            db.add(FetchTracker(
                symbol=symbol,
                last_fetched_at=datetime.now(),
                rows_fetched=rows,
            ))
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"[{symbol}] Tracker update failed: {e}")
    finally:
        db.close()


# ── yfinance Fetch (timeout-wrapped) ────────────────────────────────

def _yfinance_download(yf_ticker: str, period: str) -> pd.DataFrame:
    """Raw yfinance call (runs inside thread pool)."""
    ticker = yf.Ticker(yf_ticker)
    return ticker.history(period=period, interval="1d")


def fetch_and_store(
    symbol: str,
    period: str = "120d",
    timeout: int = _FETCH_TIMEOUT,
) -> int:
    """
    Fetch OHLCV from yfinance with timeout, upsert to DB, update tracker.
    Returns number of rows upserted, or 0 on failure.
    """
    yf_ticker = _to_yf_ticker(symbol)
    start = time.time()

    try:
        # Submit to thread pool with timeout
        future = _fetch_pool.submit(_yfinance_download, yf_ticker, period)
        df = future.result(timeout=timeout)

        elapsed = time.time() - start

        if df.empty:
            logger.warning(f"[{symbol}] yfinance empty response ({elapsed:.1f}s)")
            return 0

        logger.info(f"[{symbol}] yfinance → {len(df)} rows in {elapsed:.1f}s")

        # Store to DB
        db = SessionLocal()
        upserted = 0
        try:
            for ts, row in df.iterrows():
                timestamp = ts.to_pydatetime().replace(tzinfo=None)

                existing = (
                    db.query(OHLCVData)
                    .filter(
                        OHLCVData.symbol == symbol,
                        OHLCVData.timestamp == timestamp,
                    )
                    .first()
                )

                if existing:
                    existing.open = float(row["Open"])
                    existing.high = float(row["High"])
                    existing.low = float(row["Low"])
                    existing.close = float(row["Close"])
                    existing.volume = float(row["Volume"])
                else:
                    db.add(OHLCVData(
                        symbol=symbol,
                        timestamp=timestamp,
                        open=float(row["Open"]),
                        high=float(row["High"]),
                        low=float(row["Low"]),
                        close=float(row["Close"]),
                        volume=float(row["Volume"]),
                    ))
                upserted += 1

            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"[{symbol}] DB write failed: {e}")
            raise
        finally:
            db.close()

        # Update tracker + invalidate stale cache
        _record_fetch(symbol, upserted)
        _invalidate(symbol)

        return upserted

    except FuturesTimeout:
        logger.warning(
            f"[{symbol}] TIMEOUT after {timeout}s — using cached/DB data"
        )
        return 0
    except Exception as e:
        logger.error(f"[{symbol}] Fetch failed: {e}")
        return 0


# ── Read from DB ─────────────────────────────────────────────────────

def get_stock_data(symbol: str, days: int = 120) -> List[Dict]:
    """Read OHLCV from database, sorted oldest → newest."""
    db = SessionLocal()
    try:
        cutoff = datetime.now() - timedelta(days=days)
        rows = (
            db.query(OHLCVData)
            .filter(OHLCVData.symbol == symbol, OHLCVData.timestamp >= cutoff)
            .order_by(OHLCVData.timestamp.asc())
            .all()
        )
        return [
            {
                "timestamp": r.timestamp,
                "open": r.open,
                "high": r.high,
                "low": r.low,
                "close": r.close,
                "volume": r.volume,
            }
            for r in rows
        ]
    finally:
        db.close()


# ── Smart Data Loader (main entry point) ─────────────────────────────

def ensure_data(symbol: str, min_rows: int = 20, allow_stale: bool = False) -> List[Dict]:
    """
    3-level data resolution with cache-hit/miss logging:
      1. In-memory cache  → instant (< 1ms)
      2. Database read    → fast   (< 10ms)
      3. yfinance fetch   → slow   (5–30s, timeout-protected)
    """
    # ── Level 1: Memory cache ────────────────────────────────────
    cached = _get_cached(symbol)
    if cached and len(cached) >= min_rows:
        logger.debug(f"[{symbol}] CACHE HIT ({len(cached)} rows, memory)")
        return cached

    # ── Level 2: Database ────────────────────────────────────────
    data = get_stock_data(symbol, days=120)

    if len(data) >= min_rows and (_is_fetch_fresh(symbol) or allow_stale):
        logger.debug(f"[{symbol}] DB HIT ({len(data)} rows, fresh/stale allowed)")
        _set_cache(symbol, data)
        return data

    # ── Level 3: yfinance (last resort) ──────────────────────────
    if len(data) < min_rows:
        logger.info(
            f"[{symbol}] CACHE MISS — {len(data)} rows in DB, "
            f"fetching 120d from yfinance..."
        )
        fetch_and_store(symbol, period="120d")
    elif not _is_fetch_fresh(symbol) and not allow_stale:
        logger.info(
            f"[{symbol}] DATA STALE — refreshing from yfinance..."
        )
        fetch_and_store(symbol, period="5d")

    data = get_stock_data(symbol, days=120)
    _set_cache(symbol, data)
    return data


# ── Startup Preloader ────────────────────────────────────────────────

def preload_all_stocks():
    """
    Preload all stocks into DB + memory cache on startup.
    Checks freshness first — only fetches stale/missing data.
    Called in a background thread so the server accepts requests immediately.
    """
    global _preload_complete, _preload_progress

    all_symbols = list(MARKET_TICKERS.keys()) + list(NSE_STOCKS.keys())
    _preload_progress = {"done": 0, "total": len(all_symbols), "errors": 0}

    logger.info("=" * 55)
    logger.info(f"  PRELOADING {len(all_symbols)} symbols...")
    logger.info("=" * 55)

    for i, symbol in enumerate(all_symbols, 1):
        try:
            if _is_fetch_fresh(symbol, max_age_minutes=60):
                # Already fresh in DB — just load into memory cache
                data = get_stock_data(symbol, days=120)
                _set_cache(symbol, data)
                logger.info(f"  [{i}/{len(all_symbols)}] {symbol:12s} FRESH ({len(data)} rows)")
            else:
                # Stale or missing — fetch from yfinance
                count = fetch_and_store(symbol, period="120d")
                data = get_stock_data(symbol, days=120)
                _set_cache(symbol, data)
                logger.info(f"  [{i}/{len(all_symbols)}] {symbol:12s} FETCHED ({count} rows)")
                time.sleep(0.5)  # Rate-limit yfinance

        except Exception as e:
            logger.error(f"  [{i}/{len(all_symbols)}] {symbol} FAILED: {e}")
            _preload_progress["errors"] += 1

        _preload_progress["done"] = i

    _preload_complete = True
    logger.info("=" * 55)
    logger.info(
        f"  PRELOAD COMPLETE — {_preload_progress['done']} symbols, "
        f"{_preload_progress['errors']} errors"
    )
    logger.info("=" * 55)


# ── Scheduled Refresh ────────────────────────────────────────────────

def refresh_all_stocks():
    """
    Refresh last 5 days for all tracked symbols.
    Called by APScheduler every 15 minutes.
    Updates both DB and memory cache.
    """
    logger.info("Scheduled refresh starting...")
    errors = 0

    for name in MARKET_TICKERS:
        try:
            fetch_and_store(name, period="5d")
            # Reload into cache
            data = get_stock_data(name, days=120)
            _set_cache(name, data)
        except Exception as e:
            logger.error(f"  [{name}] refresh error: {e}")
            errors += 1
        time.sleep(0.3)

    for symbol in NSE_STOCKS:
        try:
            fetch_and_store(symbol, period="5d")
            data = get_stock_data(symbol, days=120)
            _set_cache(symbol, data)
        except Exception as e:
            logger.error(f"  [{symbol}] refresh error: {e}")
            errors += 1
        time.sleep(0.3)

    if errors:
        logger.warning(f"Refresh done with {errors} errors")
    else:
        logger.info("Refresh complete — all stocks updated + cached")


# ── Legacy compat ────────────────────────────────────────────────────
backfill_all_stocks = preload_all_stocks  # Alias


def get_preload_status() -> Dict:
    """Returns preload progress for /api/status endpoint."""
    return {
        "complete": _preload_complete,
        "progress": _preload_progress,
        "cache_size": len(_data_cache),
    }
