"""
In-memory cache for market data.
Prevents hammering Yahoo Finance on every API call.
Cache TTL: 15 minutes (market data is ~15 min delayed anyway).
"""

import time
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

_cache: dict = {}
_TTL = 5 * 60  # 5 minutes — market changes fast


def get(key: str) -> Optional[Any]:
    entry = _cache.get(key)
    if entry and (time.time() - entry["ts"]) < _TTL:
        logger.info(f"Cache HIT: {key} (age {int(time.time()-entry['ts'])}s)")
        return entry["data"]
    return None


def set(key: str, data: Any):
    _cache[key] = {"data": data, "ts": time.time()}
    logger.info(f"Cache SET: {key}")


def invalidate(key: str = None):
    """Invalidate one key or entire cache"""
    if key:
        _cache.pop(key, None)
    else:
        _cache.clear()
    logger.info(f"Cache INVALIDATED: {key or 'ALL'}")


def age(key: str) -> Optional[int]:
    """Return cache age in seconds, or None if not cached"""
    entry = _cache.get(key)
    if entry:
        return int(time.time() - entry["ts"])
    return None
