"""
Batch Evaluator — Parallel stock evaluation engine.

Runs evaluations in background threads so the API never blocks.
Three modes:
  1. full_batch()       — All stocks (night job / startup)
  2. incremental()      — Top movers + stale stocks (every 15 min)
  3. priority_refresh() — Hottest stocks only (every 5 min)

All results are persisted via evaluation_cache → DB + memory.
"""

import logging
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Dict, List, Optional

from app.decision_engine import evaluate
from app.services.evaluation_cache import (
    store_result,
    store_batch_results,
    get_stale_symbols,
    get_cached_result,
    invalidate,
)
from app.services.stock_screener import FULL_UNIVERSE

logger = logging.getLogger(__name__)

# ── Config ───────────────────────────────────────────────────────────
MAX_WORKERS = 8            # Parallel evaluation threads
EVAL_TIMEOUT = 30          # Seconds per stock evaluation
RATE_LIMIT_DELAY = 0.1     # Seconds between batch submissions

# Track batch status
_batch_status = {
    "running": False,
    "last_run": None,
    "last_duration": 0,
    "last_count": 0,
    "last_accepted": 0,
    "errors": 0,
}
_batch_lock = threading.Lock()


def get_batch_status() -> Dict:
    """Return current batch evaluator status."""
    with _batch_lock:
        return dict(_batch_status)


def _evaluate_safe(symbol: str) -> Optional[Dict]:
    """Evaluate a single stock with error handling and retry."""
    for attempt in range(2):  # 1 retry
        try:
            result = evaluate(symbol, allow_stale=True)
            return result
        except Exception as e:
            if attempt == 0:
                logger.warning(f"[{symbol}] Eval attempt 1 failed: {e}, retrying...")
                time.sleep(1)
            else:
                logger.error(f"[{symbol}] Eval failed after retry: {e}")
                return {
                    "symbol": symbol,
                    "name": FULL_UNIVERSE.get(symbol, {}).get("name", symbol),
                    "sector": FULL_UNIVERSE.get(symbol, {}).get("sector", "Unknown"),
                    "score": 0, "probability": 0, "ev": 0,
                    "entry": 0, "stop_loss": 0, "target": 0,
                    "atr": 0, "reward_risk": 0,
                    "decision": "ERROR",
                    "rejection_reason": str(e),
                    "features": {}, "agents": {},
                    "regime": "unknown", "reasoning": [],
                    "data_points": 0,
                }
    return None


# ── Full Batch (Night Job / Startup) ────────────────────────────────

def full_batch():
    """
    Evaluate ALL stocks in the universe.
    Called at 3:00 AM or on startup.
    Uses parallel ThreadPoolExecutor for speed.
    """
    with _batch_lock:
        if _batch_status["running"]:
            logger.warning("Batch already running — skipping")
            return
        _batch_status["running"] = True

    symbols = list(FULL_UNIVERSE.keys())
    logger.info(f"{'='*55}")
    logger.info(f"  FULL BATCH: Evaluating {len(symbols)} stocks...")
    logger.info(f"{'='*55}")

    start = time.time()
    results = []
    accepted = 0
    errors = 0

    try:
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
            future_to_sym = {}
            for sym in symbols:
                future = pool.submit(_evaluate_safe, sym)
                future_to_sym[future] = sym
                time.sleep(RATE_LIMIT_DELAY)

            for i, future in enumerate(as_completed(future_to_sym), 1):
                sym = future_to_sym[future]
                try:
                    result = future.result(timeout=EVAL_TIMEOUT)
                    if result:
                        results.append(result)
                        store_result(sym, result)
                        if result.get("decision") == "ACCEPT":
                            accepted += 1
                    else:
                        errors += 1
                except Exception as e:
                    logger.error(f"[{sym}] Future error: {e}")
                    errors += 1

                # Progress log every 20 stocks
                if i % 20 == 0:
                    elapsed = time.time() - start
                    logger.info(
                        f"  Batch progress: {i}/{len(symbols)} "
                        f"({i/len(symbols)*100:.0f}%) in {elapsed:.1f}s"
                    )

        # Store all results in scan cache
        store_batch_results(results)

        elapsed = time.time() - start
        logger.info(f"{'='*55}")
        logger.info(
            f"  BATCH COMPLETE: {len(results)} evaluated, "
            f"{accepted} ACCEPTED, {errors} errors in {elapsed:.1f}s"
        )
        logger.info(f"{'='*55}")

    except Exception as e:
        logger.error(f"Batch evaluation crashed: {e}", exc_info=True)
    finally:
        with _batch_lock:
            _batch_status.update({
                "running": False,
                "last_run": datetime.now().isoformat(),
                "last_duration": round(time.time() - start, 1),
                "last_count": len(results),
                "last_accepted": accepted,
                "errors": errors,
            })


# ── Incremental Refresh (Every 15 min during market hours) ──────────

def incremental_refresh(max_stocks: int = 50):
    """
    Re-evaluate stocks that are stale (>30 min old) or high-priority.
    Called every 15 minutes during market hours.
    """
    with _batch_lock:
        if _batch_status["running"]:
            logger.info("Batch running — skipping incremental")
            return

    stale = get_stale_symbols(max_age_min=30)

    if not stale:
        logger.info("Incremental: all stocks fresh, nothing to do")
        return

    # Prioritize: sort stale stocks by how interesting they are
    prioritized = _prioritize_stocks(stale)[:max_stocks]

    logger.info(
        f"Incremental refresh: {len(prioritized)} stocks "
        f"(from {len(stale)} stale)"
    )

    start = time.time()
    results = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = {pool.submit(_evaluate_safe, s): s for s in prioritized}
        for future in as_completed(futures):
            sym = futures[future]
            try:
                result = future.result(timeout=EVAL_TIMEOUT)
                if result:
                    results.append(result)
                    store_result(sym, result)
            except Exception as e:
                logger.warning(f"[{sym}] Incremental eval error: {e}")

    # Rebuild scan cache with fresh + existing results
    _merge_into_scan_cache(results)

    elapsed = time.time() - start
    logger.info(
        f"Incremental done: {len(results)} refreshed in {elapsed:.1f}s"
    )


# ── Priority Refresh (Every 5 min — hottest stocks only) ────────────

def priority_refresh(max_stocks: int = 15):
    """
    Re-evaluate only the highest-priority stocks:
    - Open trades (MUST stay fresh for SL/target monitoring)
    - Recently accepted stocks
    - Stocks with high volume/momentum from last scan
    """
    with _batch_lock:
        if _batch_status["running"]:
            return

    hot_symbols = _get_hot_symbols(max_stocks)

    if not hot_symbols:
        return

    logger.info(f"Priority refresh: {len(hot_symbols)} hot stocks")

    start = time.time()

    with ThreadPoolExecutor(max_workers=min(MAX_WORKERS, len(hot_symbols))) as pool:
        futures = {pool.submit(_evaluate_safe, s): s for s in hot_symbols}
        for future in as_completed(futures):
            sym = futures[future]
            try:
                result = future.result(timeout=EVAL_TIMEOUT)
                if result:
                    store_result(sym, result)
            except Exception:
                pass

    logger.info(f"Priority refresh done in {time.time()-start:.1f}s")


# ── Helpers ──────────────────────────────────────────────────────────

def _prioritize_stocks(symbols: List[str]) -> List[str]:
    """Sort stocks by priority (open trades first, then by cached score)."""
    # Get open trade symbols
    try:
        from app.services.trade_monitor import get_open_trades
        open_syms = {t["symbol"] for t in get_open_trades()}
    except Exception:
        open_syms = set()

    def score(sym):
        # Open trades get highest priority
        if sym in open_syms:
            return 1000

        # Check last cached result for interest signals
        cached = get_cached_result(sym)
        if cached:
            s = 0
            if cached.get("decision") == "ACCEPT":
                s += 50
            s += abs(cached.get("ev", 0))
            s += cached.get("probability", 0) * 20
            return s
        return 0  # Unknown = lowest priority

    return sorted(symbols, key=score, reverse=True)


def _get_hot_symbols(max_n: int = 15) -> List[str]:
    """Get the hottest stocks that need priority refresh."""
    hot = set()

    # 1. Open trades — always refresh
    try:
        from app.services.trade_monitor import get_open_trades
        for t in get_open_trades():
            hot.add(t["symbol"])
    except Exception:
        pass

    # 2. Recently accepted stocks from cache
    from app.services.evaluation_cache import get_all_db_results
    try:
        recent = get_all_db_results(max_age_min=60)
        for r in recent:
            if r.get("decision") == "ACCEPT":
                hot.add(r["symbol"])
    except Exception:
        pass

    return list(hot)[:max_n]


def _merge_into_scan_cache(new_results: List[Dict]):
    """Merge newly evaluated results into the existing scan cache."""
    from app.services.evaluation_cache import (
        get_all_db_results, store_batch_results as _store_batch,
    )

    # Get all current DB results (fresh + stale)
    all_results = get_all_db_results(max_age_min=60)

    # Replace stale entries with new ones
    result_map = {r["symbol"]: r for r in all_results if r.get("symbol")}
    for r in new_results:
        if r and r.get("symbol"):
            result_map[r["symbol"]] = r

    merged = list(result_map.values())
    _store_batch(merged)
