"""
Dynamic Stock Screener — Scans 200+ NSE stocks for trending candidates.

Instead of a fixed 34-stock list, this screener:
1. Maintains a broad universe of ~200 NSE stocks (NIFTY 200 + popular mid-caps)
2. Batch-downloads price/volume data via yfinance
3. Filters for "trending" stocks: momentum spikes, volume anomalies, breakouts
4. Returns dynamic candidates for the Decision Engine to evaluate

Cached for 30 minutes to avoid excessive yfinance calls.
"""

import logging
import threading
import time
from datetime import datetime
from typing import Dict, List, Optional

import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)

# ── Cache ────────────────────────────────────────────────────────────────────
_screen_cache: Dict = {}
_screen_lock = threading.Lock()
_SCREEN_CACHE_TTL = 1800  # 30 minutes

# ── Full NSE Scanning Universe (~200 stocks) ─────────────────────────────────
FULL_UNIVERSE: Dict[str, Dict] = {
    # ── NIFTY 50 Core ────────────────────────────────────────────────────────
    "RELIANCE":    {"name": "Reliance Industries",      "sector": "Energy"},
    "TCS":         {"name": "Tata Consultancy Services", "sector": "IT"},
    "HDFCBANK":    {"name": "HDFC Bank",                "sector": "Banking"},
    "INFY":        {"name": "Infosys",                  "sector": "IT"},
    "ICICIBANK":   {"name": "ICICI Bank",               "sector": "Banking"},
    "HINDUNILVR":  {"name": "Hindustan Unilever",       "sector": "FMCG"},
    "SBIN":        {"name": "State Bank of India",      "sector": "PSU Banks"},
    "BHARTIARTL":  {"name": "Bharti Airtel",            "sector": "Telecom"},
    "KOTAKBANK":   {"name": "Kotak Mahindra Bank",      "sector": "Banking"},
    "LT":          {"name": "Larsen & Toubro",          "sector": "Infrastructure"},
    "ITC":         {"name": "ITC",                      "sector": "FMCG"},
    "AXISBANK":    {"name": "Axis Bank",                "sector": "Banking"},
    "SUNPHARMA":   {"name": "Sun Pharma",               "sector": "Pharma"},
    "BAJFINANCE":  {"name": "Bajaj Finance",            "sector": "NBFC"},
    "MARUTI":      {"name": "Maruti Suzuki",            "sector": "Auto"},
    "TITAN":       {"name": "Titan Company",            "sector": "Consumer Durables"},
    "HCLTECH":     {"name": "HCL Technologies",         "sector": "IT"},
    "TATAMOTORS":  {"name": "Tata Motors",              "sector": "Auto"},
    "WIPRO":       {"name": "Wipro",                    "sector": "IT"},
    "NTPC":        {"name": "NTPC",                     "sector": "Energy"},
    "ONGC":        {"name": "ONGC",                     "sector": "Energy"},
    "POWERGRID":   {"name": "Power Grid Corp",          "sector": "Energy"},
    "COALINDIA":   {"name": "Coal India",               "sector": "Mining"},
    "ADANIENT":    {"name": "Adani Enterprises",        "sector": "Conglomerate"},
    "ADANIPORTS":  {"name": "Adani Ports",              "sector": "Infrastructure"},
    "ULTRACEMCO":  {"name": "UltraTech Cement",         "sector": "Cement"},
    "ASIANPAINT":  {"name": "Asian Paints",             "sector": "Consumer Durables"},
    "NESTLEIND":   {"name": "Nestle India",             "sector": "FMCG"},
    "JSWSTEEL":    {"name": "JSW Steel",                "sector": "Metals"},
    "TATASTEEL":   {"name": "Tata Steel",               "sector": "Metals"},
    "M&M":         {"name": "Mahindra & Mahindra",      "sector": "Auto"},
    "BAJAJFINSV":  {"name": "Bajaj Finserv",            "sector": "NBFC"},
    "BAJAJ-AUTO":  {"name": "Bajaj Auto",               "sector": "Auto"},
    "INDUSINDBK":  {"name": "IndusInd Bank",            "sector": "Banking"},
    "DRREDDY":     {"name": "Dr. Reddy's",              "sector": "Pharma"},
    "CIPLA":       {"name": "Cipla",                    "sector": "Pharma"},
    "DIVISLAB":    {"name": "Divi's Labs",              "sector": "Pharma"},
    "BRITANNIA":   {"name": "Britannia Industries",     "sector": "FMCG"},
    "TECHM":       {"name": "Tech Mahindra",            "sector": "IT"},
    "HEROMOTOCO":  {"name": "Hero MotoCorp",            "sector": "Auto"},
    "BPCL":        {"name": "BPCL",                     "sector": "Energy"},
    "EICHERMOT":   {"name": "Eicher Motors",            "sector": "Auto"},
    "APOLLOHOSP":  {"name": "Apollo Hospitals",         "sector": "Healthcare"},
    "GRASIM":      {"name": "Grasim Industries",        "sector": "Cement"},
    "TATACONSUM":  {"name": "Tata Consumer Products",   "sector": "FMCG"},
    "HINDALCO":    {"name": "Hindalco Industries",      "sector": "Metals"},
    "SBILIFE":     {"name": "SBI Life Insurance",       "sector": "Insurance"},
    "HDFCLIFE":    {"name": "HDFC Life Insurance",      "sector": "Insurance"},

    # ── NIFTY Next 50 & Mid-Cap Stars ────────────────────────────────────────
    "HAL":         {"name": "Hindustan Aeronautics",    "sector": "Defence"},
    "BEL":         {"name": "Bharat Electronics",       "sector": "Defence"},
    "BHEL":        {"name": "Bharat Heavy Electricals", "sector": "Capital Goods"},
    "COCHINSHIP":  {"name": "Cochin Shipyard",          "sector": "Defence"},
    "DLF":         {"name": "DLF",                      "sector": "Real Estate"},
    "GODREJPROP":  {"name": "Godrej Properties",        "sector": "Real Estate"},
    "OBEROIRLTY":  {"name": "Oberoi Realty",            "sector": "Real Estate"},
    "PRESTIGE":    {"name": "Prestige Estates",         "sector": "Real Estate"},
    "PHOENIXLTD":  {"name": "Phoenix Mills",            "sector": "Real Estate"},
    "BRIGADE":     {"name": "Brigade Enterprises",      "sector": "Real Estate"},
    "ZOMATO":      {"name": "Zomato",                   "sector": "Consumer Tech"},
    "TRENT":       {"name": "Trent",                    "sector": "Retail"},
    "DMART":       {"name": "Avenue Supermarts",        "sector": "Retail"},
    "ADANIGREEN":  {"name": "Adani Green Energy",       "sector": "Renewable Energy"},
    "ADANIPOWER":  {"name": "Adani Power",              "sector": "Energy"},
    "TATAPOWER":   {"name": "Tata Power",               "sector": "Energy"},
    "NHPC":        {"name": "NHPC",                     "sector": "Energy"},
    "SJVN":        {"name": "SJVN",                     "sector": "Energy"},
    "IRFC":        {"name": "Indian Railway Finance",   "sector": "Infrastructure"},
    "RECLTD":      {"name": "REC Limited",              "sector": "Infrastructure"},
    "PFC":         {"name": "Power Finance Corp",       "sector": "Infrastructure"},
    "VEDL":        {"name": "Vedanta",                  "sector": "Metals"},
    "HINDZINC":    {"name": "Hindustan Zinc",           "sector": "Metals"},
    "NATIONALUM":  {"name": "National Aluminium",       "sector": "Metals"},
    "SAIL":        {"name": "Steel Authority",          "sector": "Metals"},
    "NMDC":        {"name": "NMDC",                     "sector": "Metals"},
    "JINDALSTEL":  {"name": "Jindal Steel & Power",     "sector": "Metals"},
    "ABB":         {"name": "ABB India",                "sector": "Capital Goods"},
    "SIEMENS":     {"name": "Siemens",                  "sector": "Capital Goods"},
    "HAVELLS":     {"name": "Havells India",            "sector": "Capital Goods"},
    "CUMMINSIND":  {"name": "Cummins India",            "sector": "Capital Goods"},
    "LTIM":        {"name": "LTIMindtree",              "sector": "IT"},
    "MPHASIS":     {"name": "Mphasis",                  "sector": "IT"},
    "COFORGE":     {"name": "Coforge",                  "sector": "IT"},
    "PERSISTENT":  {"name": "Persistent Systems",       "sector": "IT"},
    "TATAELXSI":   {"name": "Tata Elxsi",               "sector": "IT"},
    "VBL":         {"name": "Varun Beverages",          "sector": "FMCG"},
    "COLPAL":      {"name": "Colgate-Palmolive",        "sector": "FMCG"},
    "DABUR":       {"name": "Dabur India",              "sector": "FMCG"},
    "MARICO":      {"name": "Marico",                   "sector": "FMCG"},
    "GODREJCP":    {"name": "Godrej Consumer Products", "sector": "FMCG"},
    "LUPIN":       {"name": "Lupin",                    "sector": "Pharma"},
    "AUROPHARMA":  {"name": "Aurobindo Pharma",         "sector": "Pharma"},
    "BIOCON":      {"name": "Biocon",                   "sector": "Pharma"},
    "TORNTPHARM":  {"name": "Torrent Pharmaceuticals",  "sector": "Pharma"},
    "ALKEM":       {"name": "Alkem Laboratories",       "sector": "Pharma"},
    "ZYDUSLIFE":   {"name": "Zydus Lifesciences",       "sector": "Pharma"},
    "IPCALAB":     {"name": "IPCA Laboratories",        "sector": "Pharma"},
    "GLENMARK":    {"name": "Glenmark Pharma",          "sector": "Pharma"},
    "PNB":         {"name": "Punjab National Bank",     "sector": "PSU Banks"},
    "BANKBARODA":  {"name": "Bank of Baroda",           "sector": "PSU Banks"},
    "CANBK":       {"name": "Canara Bank",              "sector": "PSU Banks"},
    "IOB":         {"name": "Indian Overseas Bank",     "sector": "PSU Banks"},
    "INDIANB":     {"name": "Indian Bank",              "sector": "PSU Banks"},
    "FEDERALBNK":  {"name": "Federal Bank",             "sector": "Banking"},
    "IDFCFIRSTB":  {"name": "IDFC First Bank",          "sector": "Banking"},
    "BANDHANBNK":  {"name": "Bandhan Bank",             "sector": "Banking"},
    "AUBANK":      {"name": "AU Small Finance Bank",    "sector": "Banking"},
    "IOC":         {"name": "Indian Oil Corporation",   "sector": "Energy"},
    "GAIL":        {"name": "GAIL India",               "sector": "Energy"},
    "ICICIPRULI":  {"name": "ICICI Pru Life Insurance", "sector": "Insurance"},
    "CHOLAFIN":    {"name": "Cholamandalam Finance",    "sector": "NBFC"},
    "MUTHOOTFIN":  {"name": "Muthoot Finance",          "sector": "NBFC"},
    "MANAPPURAM":  {"name": "Manappuram Finance",       "sector": "NBFC"},
    "LICHSGFIN":   {"name": "LIC Housing Finance",      "sector": "NBFC"},
    "SHRIRAMFIN":  {"name": "Shriram Finance",          "sector": "NBFC"},
    "TVSMOTOR":    {"name": "TVS Motor",                "sector": "Auto"},
    "ASHOKLEY":    {"name": "Ashok Leyland",            "sector": "Auto"},
    "MOTHERSON":   {"name": "Motherson Sumi",           "sector": "Auto"},
    "BHARATFORG":  {"name": "Bharat Forge",             "sector": "Auto"},
    "MRF":         {"name": "MRF",                      "sector": "Auto"},
    "APOLLOTYRE":  {"name": "Apollo Tyres",             "sector": "Auto"},
    "BALKRISIND":  {"name": "Balkrishna Industries",    "sector": "Auto"},
    "POLYCAB":     {"name": "Polycab India",            "sector": "Capital Goods"},
    "KEI":         {"name": "KEI Industries",           "sector": "Capital Goods"},
    "DIXON":       {"name": "Dixon Technologies",       "sector": "Electronics"},
    "KAYNES":      {"name": "Kaynes Technology",        "sector": "Electronics"},
    "VOLTAS":      {"name": "Voltas",                   "sector": "Consumer Durables"},
    "CROMPTON":    {"name": "Crompton Greaves CE",      "sector": "Consumer Durables"},
    "BATAINDIA":   {"name": "Bata India",               "sector": "Consumer Durables"},
    "PAGEIND":     {"name": "Page Industries",          "sector": "Consumer Durables"},
    "PIDILITIND":  {"name": "Pidilite Industries",      "sector": "Chemicals"},
    "SRF":         {"name": "SRF",                      "sector": "Chemicals"},
    "PIIND":       {"name": "PI Industries",            "sector": "Chemicals"},
    "DEEPAKNTR":   {"name": "Deepak Nitrite",           "sector": "Chemicals"},
    "NAVINFLUOR":  {"name": "Navin Fluorine",           "sector": "Chemicals"},
    "ATUL":        {"name": "Atul",                     "sector": "Chemicals"},
    "CLEAN":       {"name": "Clean Science",            "sector": "Chemicals"},
    "UPL":         {"name": "UPL",                      "sector": "Agrochemicals"},
    "SHREECEM":    {"name": "Shree Cement",             "sector": "Cement"},
    "AMBUJACEM":   {"name": "Ambuja Cements",           "sector": "Cement"},
    "ACC":         {"name": "ACC",                      "sector": "Cement"},
    "RAMCOCEM":    {"name": "Ramco Cements",            "sector": "Cement"},
    "DALBHARAT":   {"name": "Dalmia Bharat",            "sector": "Cement"},
    "JKCEMENT":    {"name": "JK Cement",                "sector": "Cement"},
    "INDIGO":      {"name": "InterGlobe Aviation",      "sector": "Aviation"},
    "CONCOR":      {"name": "Container Corp",           "sector": "Logistics"},
    "DELHIVERY":   {"name": "Delhivery",                "sector": "Logistics"},
    "MAXHEALTH":   {"name": "Max Healthcare",           "sector": "Healthcare"},
    "FORTIS":      {"name": "Fortis Healthcare",        "sector": "Healthcare"},
    "LALPATHLAB":  {"name": "Dr Lal PathLabs",          "sector": "Healthcare"},
    "METROPOLIS":  {"name": "Metropolis Healthcare",    "sector": "Healthcare"},
    "JIOFIN":      {"name": "Jio Financial Services",   "sector": "NBFC"},
    "LICI":        {"name": "LIC of India",             "sector": "Insurance"},
    "NAUKRI":      {"name": "Info Edge (Naukri)",       "sector": "Consumer Tech"},
    "PAYTM":       {"name": "One97 Communications",     "sector": "Consumer Tech"},
    "YESBANK":     {"name": "Yes Bank",                 "sector": "Banking"},
    "IDEA":        {"name": "Vodafone Idea",            "sector": "Telecom"},
    "IRCTC":       {"name": "IRCTC",                    "sector": "Consumer Tech"},
    "RVNL":        {"name": "Rail Vikas Nigam",         "sector": "Infrastructure"},
    "SUZLON":      {"name": "Suzlon Energy",            "sector": "Renewable Energy"},
    "TATACOMM":    {"name": "Tata Communications",      "sector": "Telecom"},
    "INDUSTOWER":  {"name": "Indus Towers",             "sector": "Telecom"},
    "BOSCHLTD":    {"name": "Bosch",                    "sector": "Auto"},
    "SUNTV":       {"name": "Sun TV Network",           "sector": "Media"},
    "ZEEL":        {"name": "Zee Entertainment",        "sector": "Media"},
    "PVR":         {"name": "PVR INOX",                 "sector": "Media"},
    "EXIDEIND":    {"name": "Exide Industries",         "sector": "Auto"},
    "AMARARAJA":   {"name": "Amara Raja Energy",        "sector": "Auto"},
    "CHAMBAL":     {"name": "Chambal Fertilisers",      "sector": "Agrochemicals"},
    "COROMANDEL":  {"name": "Coromandel International", "sector": "Agrochemicals"},
    "INDHOTEL":    {"name": "Indian Hotels (Taj)",      "sector": "Hospitality"},
    "STARHEALTH":  {"name": "Star Health Insurance",    "sector": "Insurance"},
    "NYKAA":       {"name": "FSN E-Commerce (Nykaa)",   "sector": "Consumer Tech"},
    "SOLARINDS":   {"name": "Solar Industries",         "sector": "Defence"},
    "DATAPATTNS":  {"name": "Data Patterns",            "sector": "Defence"},
    "MAZAGON":     {"name": "Mazagon Dock",             "sector": "Defence"},
    "GRSE":        {"name": "Garden Reach Shipbuilders", "sector": "Defence"},
    # ── Additions ────────────────────────────────────────────────────────────────
    "WAAREEENER":  {"name": "Waaree Energies",          "sector": "Renewable Energy"},
    "KPITTECH":    {"name": "KPIT Technologies",        "sector": "IT"},
    "AMBER":       {"name": "Amber Enterprises",        "sector": "Electronics"},
    "SONACOMS":    {"name": "Sona BLW Precision",       "sector": "Auto"},
    "MANKIND":     {"name": "Mankind Pharma",           "sector": "Pharma"},
    "POLICYBZR":   {"name": "PB Fintech",               "sector": "Consumer Tech"},
    "ANGELONE":    {"name": "Angel One",                "sector": "Consumer Tech"},
    "CDSL":        {"name": "CDSL",                     "sector": "Consumer Tech"},
    "LODHA":       {"name": "Macrotech Developers",     "sector": "Real Estate"},
    "JSWENERGY":   {"name": "JSW Energy",               "sector": "Renewable Energy"},
}


def _yf_symbol(nse_symbol: str) -> str:
    """Convert NSE symbol to Yahoo Finance format."""
    special = {
        "M&M":        "M%26M.NS",
        "BAJAJ-AUTO": "BAJAJ-AUTO.NS",
    }
    return special.get(nse_symbol, f"{nse_symbol}.NS")


def _yf_to_nse(yf_sym: str) -> str:
    """Reverse map Yahoo Finance ticker back to NSE symbol."""
    if yf_sym == "M%26M.NS":
        return "M&M"
    return yf_sym.replace(".NS", "")


class StockScreener:
    """
    Two-pass stock screener:
      Pass 1 — Quick batch scan of 200+ stocks (momentum + volume metrics)
      Pass 2 — Return top trending candidates for full Decision Engine evaluation
    """

    def __init__(self):
        self.universe = FULL_UNIVERSE

    def scan_trending(self, top_n: int = 80) -> List[Dict]:
        """
        Scan the full universe and return trending stock candidates.
        Results are cached for 30 minutes.

        Returns list of dicts with full stock data ready for decision engine:
        {symbol, name, sector, current_price, price_history, volume_history, ...}
        """
        # Check cache
        with _screen_lock:
            if _screen_cache.get("data") and _screen_cache.get("ts"):
                age = (datetime.now() - _screen_cache["ts"]).total_seconds()
                if age < _SCREEN_CACHE_TTL:
                    logger.info(
                        f"Screener CACHE HIT — {len(_screen_cache['data'])} "
                        f"trending stocks ({age:.0f}s old)"
                    )
                    return _screen_cache["data"]

        logger.info(f"Screening {len(self.universe)} stocks for trending candidates...")
        start = time.time()

        # ── Batch download all stocks ────────────────────────────────────
        symbols = list(self.universe.keys())
        yf_symbols = [_yf_symbol(s) for s in symbols]

        try:
            raw = yf.download(
                yf_symbols,
                period="30d",
                auto_adjust=True,
                progress=False,
                threads=True,
            )
        except Exception as e:
            logger.error(f"Screener batch download failed: {e}")
            return []

        if raw.empty:
            logger.error("Screener got empty data from yfinance")
            return []

        # ── Score each stock ─────────────────────────────────────────────
        scored = []
        for symbol in symbols:
            yf_sym = _yf_symbol(symbol)
            try:
                # Extract close and volume series
                if isinstance(raw.columns, pd.MultiIndex):
                    close_col = ("Close", yf_sym)
                    vol_col = ("Volume", yf_sym)
                    if close_col not in raw.columns:
                        continue
                    closes = raw[close_col].dropna()
                    volumes = raw[vol_col].dropna()
                else:
                    closes = raw["Close"].dropna()
                    volumes = raw["Volume"].dropna()

                if len(closes) < 10:
                    continue

                # Last 20 sessions
                closes = closes.tail(20)
                volumes = volumes.tail(20)

                close_list = closes.round(2).tolist()
                vol_list = volumes.tolist()

                # ── Screening Metrics ────────────────────────────────────
                current = float(close_list[-1])

                # 5-day return
                if len(close_list) >= 6:
                    ret_5d = ((close_list[-1] - close_list[-6]) / close_list[-6]) * 100
                else:
                    ret_5d = 0.0

                # 10-day return
                if len(close_list) >= 11:
                    ret_10d = ((close_list[-1] - close_list[-11]) / close_list[-11]) * 100
                else:
                    ret_10d = ret_5d

                # Volume ratio: peak of last 3 days vs prior baseline
                if len(vol_list) >= 10:
                    recent_peak = max(vol_list[-3:])
                    baseline = vol_list[:-3]
                    baseline_avg = sum(baseline) / len(baseline) if baseline else 1
                    vol_ratio = recent_peak / baseline_avg if baseline_avg > 0 else 0
                else:
                    vol_ratio = 0.0

                # Near 20-day high? (within 3%)
                high_20d = max(close_list)
                near_high = current >= high_20d * 0.97

                # ── Trending Score ───────────────────────────────────────
                # Higher score = more likely to be trending / worth analyzing
                trend_score = 0.0

                # Momentum component (absolute value — catches both bulls & bears)
                trend_score += min(abs(ret_5d) * 3, 30)   # max 30 pts
                trend_score += min(abs(ret_10d) * 2, 20)  # max 20 pts

                # Volume surge component
                if vol_ratio >= 2.0:
                    trend_score += 25
                elif vol_ratio >= 1.5:
                    trend_score += 15
                elif vol_ratio >= 1.2:
                    trend_score += 5

                # Breakout component
                if near_high:
                    trend_score += 15

                # Gap detection (today vs yesterday)
                if len(close_list) >= 2:
                    gap_pct = abs(close_list[-1] - close_list[-2]) / close_list[-2] * 100
                    if gap_pct >= 2:
                        trend_score += 10

                scored.append({
                    "symbol": symbol,
                    "name": self.universe[symbol]["name"],
                    "sector": self.universe[symbol]["sector"],
                    "current_price": round(current, 2),
                    "price_history": [float(c) for c in close_list],
                    "volume_history": [int(v) for v in vol_list],
                    "delivery_percent": 45,  # placeholder
                    "fii_net": 0,
                    "dii_net": 0,
                    "trend_score": round(trend_score, 1),
                    "ret_5d": round(ret_5d, 2),
                    "vol_ratio": round(vol_ratio, 2),
                })

            except Exception as e:
                logger.debug(f"Screener skip {symbol}: {e}")
                continue

        # ── Sort by trend score and take top N ───────────────────────────
        scored.sort(key=lambda x: x["trend_score"], reverse=True)
        trending = scored[:top_n]

        elapsed = time.time() - start
        logger.info(
            f"Screener found {len(trending)} trending stocks from "
            f"{len(scored)}/{len(symbols)} scanned in {elapsed:.1f}s"
        )
        if trending:
            top5 = [f"{s['symbol']}({s['trend_score']})" for s in trending[:5]]
            logger.info(f"  Top 5: {', '.join(top5)}")

        # Update cache
        with _screen_lock:
            _screen_cache["data"] = trending
            _screen_cache["ts"] = datetime.now()

        return trending

    def get_stock_info(self, symbol: str) -> Optional[Dict]:
        """Look up sector/name info for any stock in the universe."""
        return self.universe.get(symbol)

    def invalidate_cache(self):
        """Force re-scan on next call."""
        with _screen_lock:
            _screen_cache.clear()
        logger.info("Screener cache invalidated")
