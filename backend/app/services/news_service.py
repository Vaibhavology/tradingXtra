"""
TradingXtra Phase 2 — News Service

Fetches market news from Google News RSS, classifies by category/impact,
and extracts simple sentiment. Results cached for 30 minutes.
"""

import re
import time
import hashlib
import logging
import threading
from typing import List, Dict

logger = logging.getLogger(__name__)

try:
    import feedparser
    HAS_FEEDPARSER = True
except ImportError:
    HAS_FEEDPARSER = False
    logger.warning("feedparser not installed. Run: pip install feedparser")

FEEDS = [
    "https://news.google.com/rss/search?q=indian+stock+market+today&hl=en-IN&gl=IN&ceid=IN:en",
    "https://news.google.com/rss/search?q=NSE+nifty+sensex&hl=en-IN&gl=IN&ceid=IN:en",
    "https://news.google.com/rss/search?q=RBI+SEBI+FII+market&hl=en-IN&gl=IN&ceid=IN:en",
]

_news_cache: Dict = {"items": [], "fetched_at": 0}
_NEWS_TTL = 1800
_lock = threading.Lock()

IMPACT_KW = {
    "rate hike": 0.85, "rate cut": 0.85, "rbi": 0.75, "fed": 0.80,
    "recession": 0.85, "crash": 0.90, "crisis": 0.85,
    "block deal": 0.75, "results": 0.65, "earnings": 0.65,
    "fii": 0.60, "crude oil": 0.55, "inflation": 0.60, "gdp": 0.60,
    "budget": 0.70, "ipo": 0.50, "upgrade": 0.40, "downgrade": 0.45,
}
POS = {"rally","surge","gains","bullish","positive","upgrade","strong","growth","record high","soars","jumps","rises","buying","recovery"}
NEG = {"crash","fall","drop","bearish","negative","downgrade","weak","decline","slump","sell-off","warning","fear","plunge","tumbles","panic"}

CAT_KW = {
    "RISK": ["crash","crisis","warning","ban","fraud","scam","panic"],
    "GLOBAL": ["us market","global","fed","crude","dollar","china","europe","wall street"],
    "INDIA": ["rbi","india","sebi","budget","gdp","modi","finance minister"],
}

STOCK_KW = {
    "RELIANCE": ["reliance","jio","ril"], "TCS": ["tcs","tata consultancy"],
    "INFY": ["infosys"], "HDFCBANK": ["hdfc bank","hdfc"], "ICICIBANK": ["icici"],
    "SBIN": ["sbi","state bank"], "TATASTEEL": ["tata steel"],
    "ADANIENT": ["adani"], "BAJFINANCE": ["bajaj finance"], "LT": ["larsen","l&t"],
    "BHARTIARTL": ["airtel","bharti"], "SUNPHARMA": ["sun pharma"],
    "MARUTI": ["maruti"], "HAL": ["hal","hindustan aeronautics"],
    "COALINDIA": ["coal india"], "ONGC": ["ongc"],
}

def _classify(title):
    t = title.lower()
    for cat, kws in CAT_KW.items():
        if any(k in t for k in kws): return cat
    for sym, kws in STOCK_KW.items():
        if any(k in t for k in kws): return "STOCK"
    return "SECTOR"

def _impact(title):
    t = title.lower()
    return round(max(0.20, max((v for k,v in IMPACT_KW.items() if k in t), default=0.20)), 2)

def _sentiment(title):
    t = title.lower()
    p = sum(1 for w in POS if w in t)
    n = sum(1 for w in NEG if w in t)
    if p+n == 0: return 0.50
    return round(0.50 + (p-n)/(p+n) * 0.35, 3)

def _symbols(title):
    t = title.lower()
    return [s for s,kws in STOCK_KW.items() if any(k in t for k in kws)]

def fetch_news(force=False):
    if not HAS_FEEDPARSER: return []
    with _lock:
        if not force and time.time() - _news_cache["fetched_at"] < _NEWS_TTL:
            return _news_cache["items"]
    items, seen = [], set()
    for url in FEEDS:
        try:
            for e in feedparser.parse(url).entries[:15]:
                title = e.get("title","").strip()
                h = hashlib.md5(title.lower().encode()).hexdigest()[:12]
                if not title or h in seen: continue
                seen.add(h)
                items.append({"title":title,"link":e.get("link",""),"published":e.get("published",""),
                    "category":_classify(title),"impact_score":_impact(title),
                    "sentiment":_sentiment(title),"symbols":_symbols(title)})
        except Exception as ex: logger.error(f"RSS error: {ex}")
    items.sort(key=lambda x: x["impact_score"], reverse=True)
    with _lock: _news_cache["items"]=items; _news_cache["fetched_at"]=time.time()
    logger.info(f"News: {len(items)} items from {len(FEEDS)} feeds")
    return items

def get_stock_news(symbol):
    return [n for n in fetch_news() if symbol in n.get("symbols",[])]

def get_market_sentiment():
    items = fetch_news()
    if not items: return {"overall":0.5,"by_category":{},"item_count":0}
    tw, ws = 0.0, 0.0
    cats = {}
    for i in items:
        w,s = i["impact_score"],i["sentiment"]
        ws += s*w; tw += w
        cats.setdefault(i["category"],[]).append(s)
    return {"overall":round(ws/tw,3) if tw>0 else 0.5,
            "by_category":{c:round(sum(v)/len(v),3) for c,v in cats.items()},
            "item_count":len(items)}


def get_symbol_sentiment(symbol: str) -> float:
    """
    Get sentiment score for a specific symbol from news.

    Returns ∈ [0, 0.7], default 0.5 (neutral).
    Capped at 0.7 to prevent news from dominating the score.

    Used by decision_engine to set the SE feature.
    """
    stock_news = get_stock_news(symbol.upper())

    if not stock_news:
        # Also check broader market sentiment as fallback
        mkt = get_market_sentiment()
        mkt_overall = mkt.get("overall", 0.5)
        # Dampen market-level sentiment (less relevant than stock-specific)
        dampened = 0.5 + (mkt_overall - 0.5) * 0.3
        return round(min(dampened, 0.7), 4)

    # Impact-weighted sentiment for this stock
    total_weight = 0.0
    weighted_sent = 0.0
    for item in stock_news:
        w = item["impact_score"]
        weighted_sent += item["sentiment"] * w
        total_weight += w

    if total_weight == 0:
        return 0.5

    raw = weighted_sent / total_weight
    # Cap at 0.7 — news should influence but never dominate
    return round(min(max(raw, 0.0), 0.7), 4)

