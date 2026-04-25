"""
TradingXtra — Market Brief v2

Structured daily market intelligence combining:
  - Regime detection (NIFTY50 + VIX)
  - Google RSS news (Global + India)
  - YouTube Invest Smart (The Wealth Magnet)
  - Scored bias + sector strength + risk alerts

Cached 15 min. All output is structured and capped.
"""

import os
import re
import time
import hashlib
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

try:
    import feedparser
    HAS_FEEDPARSER = True
except ImportError:
    HAS_FEEDPARSER = False
    logger.warning("feedparser not installed — RSS disabled")

# ── Constants ────────────────────────────────────────────────────────

_cache: Dict[str, Any] = {"data": None, "ts": 0}
_CACHE_TTL = 900  # 15 minutes
_lock = threading.Lock()

# Google News RSS queries
GLOBAL_FEEDS = [
    "https://news.google.com/rss/search?q=global+stock+market+today&hl=en-IN&gl=IN&ceid=IN:en",
    "https://news.google.com/rss/search?q=US+market+oil+inflation&hl=en-IN&gl=IN&ceid=IN:en",
]
INDIA_FEEDS = [
    "https://news.google.com/rss/search?q=nifty+sensex+news+today&hl=en-IN&gl=IN&ceid=IN:en",
    "https://news.google.com/rss/search?q=RBI+FII+DII+flows&hl=en-IN&gl=IN&ceid=IN:en",
]

# YouTube Invest Smart
YOUTUBE_CHANNEL_ID = os.getenv("YOUTUBE_CHANNEL_ID", "UCFlpGKkFc9KW6aWbDdx3oVQ")
YOUTUBE_HANDLE = os.getenv("YOUTUBE_HANDLE", "@TheWealthMagnet")
YOUTUBE_RSS = f"https://www.youtube.com/feeds/videos.xml?channel_id={YOUTUBE_CHANNEL_ID}"

# Impact keywords → score
IMPACT_KW = {
    "rate hike": 0.85, "rate cut": 0.85, "rbi": 0.75, "fed": 0.80,
    "recession": 0.85, "crash": 0.90, "crisis": 0.85, "war": 0.80,
    "block deal": 0.70, "results": 0.60, "earnings": 0.65,
    "fii": 0.65, "dii": 0.60, "crude oil": 0.60, "crude": 0.55,
    "inflation": 0.65, "gdp": 0.60, "budget": 0.70,
    "tariff": 0.70, "sanctions": 0.65,
}

POS_KW = {"rally","surge","gains","bullish","positive","upgrade","strong","growth",
           "record high","soars","jumps","rises","buying","recovery","rebound","breakout"}
NEG_KW = {"crash","fall","drop","bearish","negative","downgrade","weak","decline",
           "slump","sell-off","warning","fear","plunge","tumbles","panic","risk","loss"}

# Stock extraction patterns
from app.data_fetcher import NSE_STOCKS
STOCK_PATTERNS = {}
for sym, info in NSE_STOCKS.items():
    patterns = [sym.lower()]
    name = info.get("name", "")
    if name:
        patterns.append(name.lower())
        # Add first word of name if long enough
        first = name.split()[0].lower()
        if len(first) >= 4:
            patterns.append(first)
    STOCK_PATTERNS[sym] = patterns

# Extra aliases
_ALIASES = {
    "RELIANCE": ["ril", "jio", "reliance"],
    "TCS": ["tcs", "tata consultancy"],
    "INFY": ["infosys", "infy"],
    "HDFCBANK": ["hdfc bank", "hdfc"],
    "ICICIBANK": ["icici bank", "icici"],
    "SBIN": ["sbi", "state bank"],
    "TATASTEEL": ["tata steel"],
    "ADANIENT": ["adani enterprises", "adani"],
    "BAJFINANCE": ["bajaj finance"],
    "BHARTIARTL": ["airtel", "bharti airtel"],
    "HAL": ["hindustan aeronautics", "hal"],
    "LT": ["larsen", "l&t"],
    "MARUTI": ["maruti suzuki"],
    "COALINDIA": ["coal india"],
    "SUNPHARMA": ["sun pharma"],
    "KOTAKBANK": ["kotak mahindra"],
    "NTPC": ["ntpc"],
    "WIPRO": ["wipro"],
    "HCLTECH": ["hcl tech"],
    "TECHM": ["tech mahindra"],
}
for sym, aliases in _ALIASES.items():
    if sym in STOCK_PATTERNS:
        STOCK_PATTERNS[sym] = list(set(STOCK_PATTERNS[sym] + aliases))


# ── Helpers ──────────────────────────────────────────────────────────

def _sentiment_score(text: str) -> float:
    """Keyword-based sentiment ∈ [0, 1]. 0.5 = neutral."""
    t = text.lower()
    p = sum(1 for w in POS_KW if w in t)
    n = sum(1 for w in NEG_KW if w in t)
    if p + n == 0:
        return 0.50
    return round(0.50 + (p - n) / (p + n) * 0.40, 3)


def _impact_score(text: str) -> float:
    """Impact score from keyword matching."""
    t = text.lower()
    return round(max(0.20, max((v for k, v in IMPACT_KW.items() if k in t), default=0.20)), 2)


def _classify(text: str) -> str:
    """Classify into GLOBAL / INDIA / RISK / SECTOR."""
    t = text.lower()
    risk_kw = ["crash", "crisis", "warning", "ban", "fraud", "panic", "collapse", "fear"]
    global_kw = ["us market", "global", "fed", "crude", "dollar", "china", "europe",
                 "wall street", "nasdaq", "s&p", "dow", "oil price", "tariff"]
    india_kw = ["rbi", "india", "sebi", "budget", "gdp", "nifty", "sensex",
                "fii", "dii", "modi", "finance minister", "rupee"]

    if any(k in t for k in risk_kw):
        return "RISK"
    if any(k in t for k in global_kw):
        return "GLOBAL"
    if any(k in t for k in india_kw):
        return "INDIA"
    return "SECTOR"


def _extract_stocks(text: str) -> List[str]:
    """Extract stock symbols from text using pattern matching."""
    t = text.lower()
    found = []
    for sym, patterns in STOCK_PATTERNS.items():
        if any(p in t for p in patterns):
            found.append(sym)
    return found[:5]


# ── News Fetching ────────────────────────────────────────────────────

def _fetch_rss_items(feeds: List[str], max_per_feed: int = 10) -> List[Dict]:
    """Fetch and deduplicate RSS items."""
    if not HAS_FEEDPARSER:
        return []
    items = []
    seen = set()
    for url in feeds:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:max_per_feed]:
                title = entry.get("title", "").strip()
                if not title:
                    continue
                h = hashlib.md5(title.lower().encode()).hexdigest()[:12]
                if h in seen:
                    continue
                seen.add(h)
                items.append({
                    "title": title,
                    "link": entry.get("link", ""),
                    "published": entry.get("published", ""),
                    "category": _classify(title),
                    "impact": _impact_score(title),
                    "sentiment": _sentiment_score(title),
                    "symbols": _extract_stocks(title),
                })
        except Exception as e:
            logger.warning(f"RSS fetch error: {e}")
    items.sort(key=lambda x: x["impact"], reverse=True)
    return items


# ── YouTube Invest Smart ────────────────────────────────────────────

_yt_cache: Dict[str, Any] = {"data": None, "ts": 0}
_YT_CACHE_TTL = 1800  # 30 minutes


def _fetch_latest_video() -> Optional[Dict]:
    """Fetch latest video info from YouTube channel.

    Strategy:
      1. Try RSS feed (fast, structured)
      2. Fallback: scrape channel page HTML for video ID + title
    """
    # ── Strategy 1: RSS feed ──
    if HAS_FEEDPARSER:
        try:
            feed = feedparser.parse(YOUTUBE_RSS)
            if feed.entries:
                latest = feed.entries[0]
                logger.info(f"InvestSmart: got video from RSS: {latest.get('title', '?')[:50]}")
                return {
                    "title": latest.get("title", ""),
                    "published": latest.get("published", ""),
                    "link": latest.get("link", ""),
                }
        except Exception as e:
            logger.warning(f"InvestSmart RSS error: {e}")

    # ── Strategy 2: Scrape channel page ──
    try:
        import urllib.request
        channel_url = f"https://www.youtube.com/{YOUTUBE_HANDLE}/videos"
        req = urllib.request.Request(channel_url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        })
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="ignore")

        # Split by richItemRenderer — each section is one video card
        # The first section is always a YouTube UI element (empty), skip it
        parts = html.split('"richItemRenderer"')
        if len(parts) < 3:
            logger.info("InvestSmart: no richItemRenderer sections found")
            return None

        # Iterate through sections to find the first valid video
        for part in parts[1:]:
            vid_match = re.search(r'"videoId"\s*:\s*"([a-zA-Z0-9_-]{11})"', part)
            title_match = re.search(
                r'"title"\s*:\s*\{\s*"runs"\s*:\s*\[\s*\{\s*"text"\s*:\s*"([^"]+)"',
                part,
            )
            if vid_match and title_match:
                video_id = vid_match.group(1)
                # Decode unicode escapes in title
                title = title_match.group(1).encode().decode("unicode_escape", errors="ignore")
                link = f"https://www.youtube.com/watch?v={video_id}"
                logger.info(f"InvestSmart: scraped video: {title[:60]} ({video_id})")
                return {
                    "title": title,
                    "published": datetime.now().isoformat(),
                    "link": link,
                }

        logger.info("InvestSmart: no valid video found in page sections")
        return None
    except Exception as e:
        logger.warning(f"InvestSmart scrape error: {e}")
        return None


def get_latest_cached_invest_smart() -> Optional[Dict]:
    """Get the most recently analyzed video from the database.
    Returns None if no cached analysis exists — user must click Refresh.
    This prevents blocking the market-brief endpoint on first load."""
    from app.database import SessionLocal, InvestSmartCache
    db = SessionLocal()
    try:
        cached = db.query(InvestSmartCache).order_by(InvestSmartCache.analyzed_at.desc()).first()
        if cached:
            return cached.data
        
        # Don't auto-trigger Gemini on first load — too slow
        # User can click "Refresh Video" button to trigger analysis
        logger.info("InvestSmart DB is empty. User can click Refresh to fetch.")
        return None
    except Exception as e:
        logger.error(f"InvestSmart DB read error: {e}")
        return None
    finally:
        db.close()


def force_refresh_invest_smart() -> Optional[Dict]:
    """Fetch latest video from YouTube channel, check DB cache, then use Gemini to
    watch the video and extract full analysis only if it's a new video.
    """
    video_info = _fetch_latest_video()
    if not video_info:
        logger.info("InvestSmart: could not fetch any video")
        return None

    title = video_info["title"]
    published = video_info["published"]
    link = video_info["link"]

    from app.database import SessionLocal, InvestSmartCache

    db = SessionLocal()
    try:
        # Check if we already analyzed this video
        cached = db.query(InvestSmartCache).filter(InvestSmartCache.video_link == link).first()
        if cached:
            logger.info(f"InvestSmart: found cached analysis for {link}, returning it.")
            return cached.data

        logger.info(f"InvestSmart: new video detected, hitting Gemini for {link}")
        # ── Gemini Video Analysis (watches the actual video) ──
        gemini_result = _gemini_video_analyze(link)

        if gemini_result:
            result = {
                "title": title,
                "published": published,
                "link": link,
                "stocks": gemini_result.get("stocks", []),
                "takeaways": gemini_result.get("takeaways", []),
                "market_commentary": gemini_result.get("market_commentary", ""),
                "insights": gemini_result.get("insights", []),
                "source": "The Wealth Magnet",
            }
        else:
            # Fallback: just show the video info without stock extraction
            result = {
                "title": title,
                "published": published,
                "link": link,
                "stocks": [],
                "takeaways": [],
                "market_commentary": "",
                "insights": [title[:80]] if title else [],
                "source": "The Wealth Magnet",
            }

        # Only save to database if we actually got valid analysis (so we retry if API was missing)
        if result.get("stocks"):
            new_cache = InvestSmartCache(video_link=link, data=result)
            db.add(new_cache)
            db.commit()

        # Update the main brief cache so it reflects immediately
        with _lock:
            if _cache["data"]:
                _cache["data"]["invest_smart"] = result

        return result
    except Exception as e:
        logger.error(f"InvestSmart DB error: {e}")
        return None
    finally:
        db.close()


def _gemini_video_analyze(video_url: str) -> Optional[Dict]:
    """Pass the YouTube video URL and transcript to Gemini and let it watch + analyze."""
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        logger.info("InvestSmart: no GEMINI_API_KEY set")
        return None

    transcript_text = ""
    try:
        import urllib.parse
        
        # Extract video ID
        parsed = urllib.parse.urlparse(video_url)
        video_id = urllib.parse.parse_qs(parsed.query).get("v")
        if video_id:
            video_id = video_id[0]
        else:
            video_id = parsed.path.split("/")[-1]
            
        logger.info(f"InvestSmart: Fetching transcript for {video_id}...")
        
        # Try multiple API patterns — youtube-transcript-api changed its interface
        try:
            # New API (v1.0+): instance-based with .fetch() returning FetchedTranscript
            from youtube_transcript_api import YouTubeTranscriptApi
            ytt = YouTubeTranscriptApi()
            transcript = ytt.fetch(video_id, languages=['en', 'hi', 'en-IN'])
            # Try .snippets (newer) then direct iteration (older)
            if hasattr(transcript, 'snippets'):
                transcript_text = " ".join([t.text for t in transcript.snippets])
            else:
                transcript_text = " ".join([t.get('text', t.text if hasattr(t, 'text') else str(t)) for t in transcript])
        except (TypeError, AttributeError):
            # Older API (v0.6.x): class method based
            from youtube_transcript_api import YouTubeTranscriptApi
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['en', 'hi', 'en-IN'])
            transcript_text = " ".join([t['text'] for t in transcript_list])
        
        logger.info(f"InvestSmart: Fetched {len(transcript_text)} chars of transcript.")
    except Exception as e:
        logger.warning(f"InvestSmart: Could not fetch transcript: {e}")
        transcript_text = "[No transcript available. Use visual/audio analysis if possible or rely on title/metadata.]"

    try:
        from google import genai
        import json as _json

        client = genai.Client(api_key=api_key)

        stock_list = ", ".join(NSE_STOCKS.keys())

        prompt = f"""You are an expert stock market analyst. I am providing you with the TRANSCRIPT of a recent YouTube video about the Indian Stock Market.

VIDEO URL: {video_url}
TRANSCRIPT:
{transcript_text[:25000]}  # Limit to ~25k chars to fit safely in prompt limits

KNOWN NSE STOCKS (use these tickers when matched): {stock_list}

Return ONLY valid JSON (no markdown, no code blocks):
{{
  "stocks": [
    {{
      "symbol": "SBIN",
      "action": "BUY",
      "reason": "Strong chart, low PE, PSU bank darling",
      "confidence": 0.8
    }}
  ],
  "takeaways": [
    "Index is up but most stocks are showing fatigue"
  ],
  "market_commentary": "Despite the index being green, breadth is weak.",
  "insights": [
    "PSU banks outperforming private banks since 2020"
  ]
}}

STRICT RULES:
- ONLY include stocks that the speaker EXPLICITLY mentions in the transcript.
- DO NOT guess or infer stocks — if not mentioned, don't include them.
- For stocks mentioned but NOT in the KNOWN list, use the commonly used NSE ticker anyway.
- action: BUY (speaker is positive), WATCH (neutral/mentioned), AVOID (negative/failed setup/warned against)
- reason: 1 sentence summarizing what the speaker said about this stock
- confidence: 0.8 if speaker is very strong about it, 0.6 for casual mention, 0.4 for negative
- takeaways: 3-5 KEY takeaways from the entire video (what would a viewer remember)
- market_commentary: 2-3 sentence summary of the overall market view expressed
- insights: 2-3 actionable trading insights from the video
- If you CANNOT analyze the video, return: {{"stocks":[],"takeaways":[],"market_commentary":"","insights":[],"error":"Cannot access video"}}"""

        # Try multiple models in case one's quota is exhausted
        # Free tier quota is per-model, so different models may have quota
        MODELS = [
            "gemini-2.5-flash",         # Latest, best quality
            "gemini-2.5-flash-lite",    # Lighter variant
            "gemini-2.0-flash",         # Stable
            "gemini-2.0-flash-lite",    # Cheapest
            "gemini-3-flash-preview",   # Preview — separate quota pool
        ]
        response = None
        for model_name in MODELS:
            try:
                logger.info(f"InvestSmart: trying model {model_name}")
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                )
                logger.info(f"InvestSmart: success with {model_name}")
                break
            except Exception as model_err:
                err_str = str(model_err)
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                    logger.warning(f"InvestSmart: {model_name} rate limited, trying next...")
                    continue
                if "503" in err_str or "UNAVAILABLE" in err_str:
                    logger.warning(f"InvestSmart: {model_name} unavailable (503), trying next...")
                    continue
                if "404" in err_str or "NOT_FOUND" in err_str:
                    logger.warning(f"InvestSmart: {model_name} not found, trying next...")
                    continue
                raise model_err

        if response is None:
            logger.warning("InvestSmart: all Gemini models exhausted")
            return None

        raw = response.text.strip()
        # Clean markdown fencing if present
        if raw.startswith("```"):
            raw = re.sub(r"```\w*\n?", "", raw).strip()

        parsed = _json.loads(raw)

        # Check for error flag
        if parsed.get("error"):
            logger.warning(f"InvestSmart Gemini: {parsed['error']}")
            return None

        # Validate stocks — keep non-NSE stocks too (with a flag)
        valid_stocks = []
        for s in parsed.get("stocks", []):
            sym = s.get("symbol", "").upper()
            action = s.get("action", "WATCH")
            if action not in ("BUY", "WATCH", "AVOID"):
                action = "WATCH"
            valid_stocks.append({
                "symbol": sym,
                "action": action,
                "reason": str(s.get("reason", ""))[:120],
                "confidence": min(max(float(s.get("confidence", 0.6)), 0.0), 1.0),
                "in_universe": sym in NSE_STOCKS,
            })

        parsed["stocks"] = valid_stocks  # Allow all stocks
        parsed["takeaways"] = [str(t)[:150] for t in parsed.get("takeaways", [])][:5]
        parsed["market_commentary"] = str(parsed.get("market_commentary", ""))[:500]
        parsed["insights"] = [str(i)[:100] for i in parsed.get("insights", [])][:3]

        logger.info(f"InvestSmart Gemini: {len(valid_stocks)} stocks, "
                     f"{len(parsed['takeaways'])} takeaways extracted")
        return parsed

    except Exception as e:
        logger.warning(f"Gemini video analysis failed: {e}")
        return None


# ── Scoring Pipeline ────────────────────────────────────────────────

def _compute_scores(global_items: List[Dict], india_items: List[Dict]) -> Dict:
    """Compute global, india, volatility scores from news items."""

    def _avg_sentiment(items):
        if not items:
            return 0.5
        total_w, ws = 0.0, 0.0
        for i in items:
            w = i["impact"]
            ws += i["sentiment"] * w
            total_w += w
        return ws / total_w if total_w > 0 else 0.5

    global_sent = _avg_sentiment(global_items)
    india_sent = _avg_sentiment(india_items)

    # Normalize to [-1, 1]
    global_score = round((global_sent - 0.5) * 2, 3)
    india_score = round((india_sent - 0.5) * 2, 3)

    # Volatility: count risk items
    all_items = global_items + india_items
    risk_count = sum(1 for i in all_items if i["category"] == "RISK")
    volatility_score = round(min(1.0, risk_count / 5.0), 3)

    # Bias score = weighted blend
    sector_score = 0.0  # Neutral default
    bias_score = round(0.4 * global_score + 0.4 * india_score + 0.2 * sector_score, 3)

    return {
        "global_score": global_score,
        "india_score": india_score,
        "volatility_score": volatility_score,
        "bias_score": bias_score,
    }


def _score_to_bias(score: float) -> str:
    """Convert numerical bias to label."""
    if score > 0.15:
        return "Bullish"
    elif score < -0.15:
        return "Bearish"
    return "Neutral"


# ── Sector Strength ─────────────────────────────────────────────────

def _compute_sector_strength(items: List[Dict]) -> Dict[str, List[str]]:
    """Compute sector strength from news mention sentiment."""
    sector_sents: Dict[str, List[float]] = {}
    for item in items:
        for sym in item.get("symbols", []):
            sec = NSE_STOCKS.get(sym, {}).get("sector", "Other")
            sector_sents.setdefault(sec, []).append(item["sentiment"])

    strong, weak = [], []
    for sec, sents in sector_sents.items():
        avg = sum(sents) / len(sents)
        if avg > 0.55:
            strong.append(sec)
        elif avg < 0.45:
            weak.append(sec)

    return {"strong": strong[:3], "weak": weak[:3]}


# ── Main Generator ───────────────────────────────────────────────────

def generate_brief() -> Dict:
    """
    Generate a structured market brief.

    Returns cached result if within TTL.
    """
    with _lock:
        if _cache["data"] and time.time() - _cache["ts"] < _CACHE_TTL:
            return _cache["data"]

    logger.info("Market Brief: generating fresh...")

    # ── 1. Regime Detection ──────────────────────────────────────
    from app.agents.regime_detector import detect as detect_regime
    from app.data_fetcher import ensure_data

    nifty_full = ensure_data("NIFTY50", min_rows=20, allow_stale=True)
    market_data = nifty_full[-30:] if nifty_full else []
    
    vix_full = ensure_data("INDIAVIX", min_rows=10, allow_stale=True)
    vix_data = vix_full[-10:] if vix_full else []

    regime_result = detect_regime(
        market_ohlcv=market_data if len(market_data) >= 20 else None,
        vix_ohlcv=vix_data if vix_data else None,
    )
    regime = regime_result.get("regime", "unknown")
    behavior_map = {"trending": "Trending", "sideways": "Range-bound",
                    "volatile": "Volatile", "unknown": "Unknown"}
    behavior = behavior_map.get(regime, "Unknown")

    # VIX
    vix_level = vix_data[-1]["close"] if vix_data else None

    # NIFTY returns
    ret_5d, ret_1d = 0.0, 0.0
    if len(market_data) >= 6:
        closes = [r["close"] for r in market_data]
        ret_5d = (closes[-1] - closes[-6]) / closes[-6] * 100
        ret_1d = (closes[-1] - closes[-2]) / closes[-2] * 100 if len(closes) >= 2 else 0

    # USD/INR (timeout-wrapped to avoid blocking)
    import yfinance as yf
    from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
    def _fetch_usd_inr():
        ticker = yf.Ticker("INR=X")
        return ticker.history(period="5d")
    try:
        with ThreadPoolExecutor(max_workers=1) as pool:
            usd_inr_data = pool.submit(_fetch_usd_inr).result(timeout=10)
        if not usd_inr_data.empty:
            usd_inr_close = usd_inr_data["Close"].iloc[-1]
            usd_inr_1d_pct = ((usd_inr_close - usd_inr_data["Close"].iloc[-2]) / usd_inr_data["Close"].iloc[-2]) * 100 if len(usd_inr_data) >= 2 else 0
            usd_inr = {"price": float(usd_inr_close), "change_pct": float(usd_inr_1d_pct)}
        else:
            usd_inr = {"price": 83.5, "change_pct": 0.0}
    except (FuturesTimeout, Exception) as e:
        logger.warning(f"USD/INR fetch timed out or failed: {e}")
        usd_inr = {"price": 83.5, "change_pct": 0.0}

    # ── 2. News Fetch ────────────────────────────────────────────
    global_items = _fetch_rss_items(GLOBAL_FEEDS, max_per_feed=10)
    india_items = _fetch_rss_items(INDIA_FEEDS, max_per_feed=10)

    # ── 3. Score ─────────────────────────────────────────────────
    scores = _compute_scores(global_items, india_items)

    # Combine regime + news for final bias
    regime_bias = {"trending": 0.1, "volatile": -0.1, "sideways": 0.0}.get(regime, 0.0)
    nifty_bias = 0.1 if ret_5d > 1.5 else (-0.1 if ret_5d < -1.5 else 0.0)
    final_bias_score = scores["bias_score"] + regime_bias + nifty_bias
    bias = _score_to_bias(final_bias_score)

    # ── 4. Drivers (capped) ──────────────────────────────────────
    global_drivers = [
        i["title"] for i in global_items
        if i["category"] == "GLOBAL" and i["impact"] >= 0.40
    ][:3]
    india_drivers = [
        i["title"] for i in india_items
        if i["category"] == "INDIA" and i["impact"] >= 0.40
    ][:3]

    # Fallback if empty
    if not global_drivers:
        global_drivers = [i["title"] for i in global_items[:2]]
    if not india_drivers:
        india_drivers = [i["title"] for i in india_items[:2]]

    # ── 5. Risk Alerts ───────────────────────────────────────────
    all_items = global_items + india_items
    risk_alerts = [
        i["title"] for i in all_items
        if i["category"] == "RISK" and i["impact"] >= 0.50
    ][:3]
    if vix_level and vix_level > 20:
        risk_alerts.insert(0, f"India VIX elevated at {vix_level:.1f}")
    risk_alerts = risk_alerts[:3]

    # ── 6. Sector Strength ───────────────────────────────────────
    sector_strength = _compute_sector_strength(all_items)

    # ── 7. Guidance ──────────────────────────────────────────────
    guidance = _build_guidance(regime, bias, vix_level, scores)

    # ── 8. Invest Smart ──────────────────────────────────────────
    invest_smart = get_latest_cached_invest_smart()

    # ── 9. Assemble ──────────────────────────────────────────────
    result = {
        "bias": bias,
        "behavior": behavior,
        "nifty_return_5d": round(ret_5d, 2),
        "nifty_return_1d": round(ret_1d, 2),
        "vix": round(vix_level, 2) if vix_level else None,
        "usd_inr": usd_inr,
        "scores": scores,
        "regime": regime_result,
        "drivers": {
            "global": global_drivers,
            "india": india_drivers,
        },
        "sector_strength": sector_strength,
        "risk_alerts": risk_alerts,
        "guidance": guidance,
        "invest_smart": invest_smart,
        "timestamp": datetime.now().isoformat(),
    }

    with _lock:
        _cache["data"] = result
        _cache["ts"] = time.time()

    logger.info(f"Market Brief: bias={bias}, behavior={behavior}, "
                f"drivers={len(global_drivers)}G+{len(india_drivers)}I, "
                f"invest_smart={'yes' if invest_smart else 'no'}")
    return result


def _build_guidance(regime: str, bias: str, vix: Optional[float],
                    scores: Dict) -> List[str]:
    """Build actionable trading guidance (max 4 items)."""
    guidance = []

    if regime == "volatile":
        guidance.append("Use tight stop-losses — volatility elevated")
        guidance.append("Reduce position sizes to 50-75% of normal")
    elif regime == "trending":
        guidance.append("Favor momentum/breakout strategies")
        if bias == "Bullish":
            guidance.append("Look for pullback entries in uptrending stocks")
        elif bias == "Bearish":
            guidance.append("Wait for reversal signals — avoid catching knives")
    elif regime == "sideways":
        guidance.append("High false-breakout risk — avoid breakout trades")
        guidance.append("Consider mean-reversion strategies")

    if vix and vix > 22:
        guidance.append("VIX above 22 — hedge positions or stay defensive")

    if scores["volatility_score"] > 0.5:
        guidance.append("Multiple risk events — keep tight stops")

    if not guidance:
        guidance.append("Normal conditions — follow system signals")

    return guidance[:4]


# ── Invest Smart Stock List (for decision engine integration) ─────

def get_invest_smart_stocks() -> List[str]:
    """Return list of symbols currently BUY-suggested by Invest Smart.

    Only returns stocks that:
      1. Have BUY action (not WATCH or AVOID)
      2. Are in our NSE universe (in_universe=True)

    Used by decision_engine for light SE boost (+0.05).
    """
    brief = generate_brief()
    invest_smart = brief.get("invest_smart")
    if not invest_smart:
        return []
    return [
        s["symbol"] for s in invest_smart.get("stocks", [])
        if s.get("action") == "BUY" and s.get("in_universe", False)
    ]
