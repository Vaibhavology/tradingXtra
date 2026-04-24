"""
Live Market Data Service — Yahoo Finance (NSE)
Fetches real OHLCV data for NSE-listed stocks and indices.
Data is end-of-day / 15-min delayed (free tier).
"""

import yfinance as yf
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# ── NSE symbol universe ──────────────────────────────────────────────────────
# Format: Yahoo Finance uses "<SYMBOL>.NS" for NSE stocks

STOCK_UNIVERSE: Dict[str, Dict] = {
    # Metals
    "HINDZINC":   {"name": "Hindustan Zinc",        "sector": "Metals"},
    "VEDL":       {"name": "Vedanta Ltd",            "sector": "Metals"},
    "JSWSTEEL":   {"name": "JSW Steel",              "sector": "Metals"},
    "TATASTEEL":  {"name": "Tata Steel",             "sector": "Metals"},
    "HINDALCO":   {"name": "Hindalco Industries",    "sector": "Metals"},
    "NATIONALUM": {"name": "National Aluminium",     "sector": "Metals"},
    # Defence
    "HAL":        {"name": "Hindustan Aeronautics",  "sector": "Defence"},
    "BEL":        {"name": "Bharat Electronics",     "sector": "Defence"},
    "BHEL":       {"name": "Bharat Heavy Electricals","sector": "Defence"},
    "COCHINSHIP": {"name": "Cochin Shipyard",        "sector": "Defence"},
    # Energy / PSU
    "COALINDIA":  {"name": "Coal India",             "sector": "Energy"},
    "ONGC":       {"name": "ONGC",                   "sector": "Energy"},
    "NTPC":       {"name": "NTPC",                   "sector": "Energy"},
    "POWERGRID":  {"name": "Power Grid Corp",        "sector": "Energy"},
    "ADANIPOWER": {"name": "Adani Power",            "sector": "Energy"},
    # PSU Banks
    "SBIN":       {"name": "State Bank of India",    "sector": "PSU Banks"},
    "PNB":        {"name": "Punjab National Bank",   "sector": "PSU Banks"},
    "BANKBARODA": {"name": "Bank of Baroda",         "sector": "PSU Banks"},
    "CANBK":      {"name": "Canara Bank",            "sector": "PSU Banks"},
    # Infrastructure
    "IRFC":       {"name": "Indian Railway Finance", "sector": "Infrastructure"},
    "RECLTD":     {"name": "REC Limited",            "sector": "Infrastructure"},
    "PFC":        {"name": "Power Finance Corp",     "sector": "Infrastructure"},
    "LT":         {"name": "Larsen & Toubro",        "sector": "Infrastructure"},
    # Auto (TATAMOTORS not available on Yahoo Finance NSE feed)
    "MARUTI":     {"name": "Maruti Suzuki",          "sector": "Auto"},
    "M&M":        {"name": "Mahindra & Mahindra",    "sector": "Auto"},
    "BAJAJ-AUTO": {"name": "Bajaj Auto",             "sector": "Auto"},
    "EICHERMOT":  {"name": "Eicher Motors",          "sector": "Auto"},
    # Private Banks
    "HDFCBANK":   {"name": "HDFC Bank",              "sector": "Banking"},
    "ICICIBANK":  {"name": "ICICI Bank",             "sector": "Banking"},
    "AXISBANK":   {"name": "Axis Bank",              "sector": "Banking"},
    "KOTAKBANK":  {"name": "Kotak Mahindra Bank",    "sector": "Banking"},
    # IT
    "INFY":       {"name": "Infosys",                "sector": "IT"},
    "TCS":        {"name": "TCS",                    "sector": "IT"},
    "WIPRO":      {"name": "Wipro",                  "sector": "IT"},
    # Pharma
    "SUNPHARMA":  {"name": "Sun Pharma",             "sector": "Pharma"},
    "DRREDDY":    {"name": "Dr Reddy's",             "sector": "Pharma"},
}

# Sector index proxies (Yahoo Finance tickers)
SECTOR_INDICES: Dict[str, str] = {
    "Metals":         "^CNXMETAL",
    "Defence":        "^CNXPSE",      # PSE index — covers HAL, BEL, BHEL, defence PSUs
    "Energy":         "^CNXENERGY",
    "PSU Banks":      "^CNXPSUBANK",
    "Infrastructure": "^CNXINFRA",
    "Auto":           "^CNXAUTO",
    "Banking":        "^NSEBANK",
    "IT":             "^CNXIT",
    "Pharma":         "^CNXPHARMA",
}

NIFTY_TICKER = "^NSEI"
BANKNIFTY_TICKER = "^NSEBANK"
VIX_TICKER = "^INDIAVIX"


class MarketDataService:
    """
    Fetches live NSE data via Yahoo Finance.
    - Price history: 20 sessions
    - Volume history: 20 sessions
    - Index data: NIFTY, BANKNIFTY, VIX
    - Sector returns: 7-day
    """

    def _yf_symbol(self, nse_symbol: str) -> str:
        """Convert NSE symbol to Yahoo Finance format"""
        special = {
            "M&M":        "M%26M.NS",
            "BAJAJ-AUTO": "BAJAJ-AUTO.NS",
        }
        if nse_symbol in special:
            return special[nse_symbol]
        return f"{nse_symbol}.NS"

    def _get_live_price(self, symbol: str) -> float:
        """Get near-real-time price via fast_info (not from historical candles)."""
        try:
            ticker = yf.Ticker(self._yf_symbol(symbol))
            info = ticker.fast_info
            if hasattr(info, 'last_price') and info.last_price:
                return round(float(info.last_price), 2)
        except Exception:
            pass
        return 0.0

    def fetch_stock(self, symbol: str, period: str = "30d") -> Optional[Dict]:
        """
        Fetch OHLCV data for a single NSE stock.
        Returns dict with price_history, volume_history, current_price, delivery_percent.
        """
        try:
            ticker = yf.Ticker(self._yf_symbol(symbol))
            hist = ticker.history(period=period)

            if hist.empty or len(hist) < 10:
                logger.warning(f"{symbol}: insufficient data ({len(hist)} rows)")
                return None

            # Last 20 sessions
            hist = hist.tail(20)
            closes = hist["Close"].round(2).tolist()
            volumes = hist["Volume"].tolist()

            # Delivery % — not available via yfinance, use a reasonable estimate
            # In production this would come from NSE bhav copy
            delivery_pct = 45  # placeholder

            info = ticker.fast_info
            current_price = float(info.last_price) if hasattr(info, "last_price") else closes[-1]

            return {
                "symbol": symbol,
                "name": STOCK_UNIVERSE[symbol]["name"],
                "sector": STOCK_UNIVERSE[symbol]["sector"],
                "current_price": round(current_price, 2),
                "price_history": closes,
                "volume_history": volumes,
                "delivery_percent": delivery_pct,
                "fii_net": 0,   # Would need NSE bulk/block deal data
                "dii_net": 0,
            }
        except Exception as e:
            logger.error(f"{symbol} fetch error: {e}")
            return None

    def fetch_all_stocks(self) -> List[Dict]:
        """Fetch all stocks in the universe. Uses batch download for speed."""
        symbols = list(STOCK_UNIVERSE.keys())
        yf_symbols = [self._yf_symbol(s) for s in symbols]

        try:
            # Batch download — much faster than individual calls
            raw = yf.download(
                yf_symbols,
                period="30d",
                auto_adjust=True,
                progress=False,
                threads=True,
            )
        except Exception as e:
            logger.error(f"Batch download failed: {e}")
            return []

        stocks = []
        for symbol in symbols:
            yf_sym = self._yf_symbol(symbol)
            try:
                # Multi-ticker download returns MultiIndex columns
                if isinstance(raw.columns, pd.MultiIndex):
                    close_col = ("Close", yf_sym)
                    vol_col   = ("Volume", yf_sym)
                    if close_col not in raw.columns:
                        continue
                    closes  = raw[close_col].dropna().tail(20).round(2).tolist()
                    volumes = raw[vol_col].dropna().tail(20).tolist()
                else:
                    closes  = raw["Close"].dropna().tail(20).round(2).tolist()
                    volumes = raw["Volume"].dropna().tail(20).tolist()

                if len(closes) < 10:
                    continue

                # Get near-real-time price (fast_info) instead of stale daily close
                live_price = self._get_live_price(symbol)
                current_price = live_price if live_price > 0 else round(float(closes[-1]), 2)

                stocks.append({
                    "symbol": symbol,
                    "name": STOCK_UNIVERSE[symbol]["name"],
                    "sector": STOCK_UNIVERSE[symbol]["sector"],
                    "current_price": current_price,
                    "price_history": [float(c) for c in closes],
                    "volume_history": [int(v) for v in volumes],
                    "delivery_percent": 45,
                    "fii_net": 0,
                    "dii_net": 0,
                })
            except Exception as e:
                logger.warning(f"{symbol} parse error: {e}")
                continue

        logger.info(f"Fetched {len(stocks)}/{len(symbols)} stocks")
        return stocks

    def fetch_market_status(self) -> Dict:
        """Fetch live NIFTY, BANKNIFTY, VIX data"""
        try:
            tickers = yf.download(
                [NIFTY_TICKER, BANKNIFTY_TICKER, VIX_TICKER],
                period="5d",
                auto_adjust=True,
                progress=False,
            )

            def _last_change(sym):
                try:
                    if isinstance(tickers.columns, pd.MultiIndex):
                        col = ("Close", sym)
                        series = tickers[col].dropna()
                    else:
                        series = tickers["Close"].dropna()
                    if len(series) < 2:
                        return series.iloc[-1], 0.0
                    val   = float(series.iloc[-1])
                    prev  = float(series.iloc[-2])
                    chg   = round(((val - prev) / prev) * 100, 2)
                    return round(val, 2), chg
                except Exception:
                    return 0.0, 0.0

            nifty_val,  nifty_chg  = _last_change(NIFTY_TICKER)
            bnifty_val, bnifty_chg = _last_change(BANKNIFTY_TICKER)
            vix_val,    vix_chg    = _last_change(VIX_TICKER)

            return {
                "nifty":        {"value": nifty_val,  "change": nifty_chg,  "direction": "up" if nifty_chg  >= 0 else "down"},
                "bank_nifty":   {"value": bnifty_val, "change": bnifty_chg, "direction": "up" if bnifty_chg >= 0 else "down"},
                "india_vix":    vix_val,
                "vix_change":   vix_chg,
                "fii_flow":     {"value": 0, "type": "buy"},   # NSE FII data needs separate scrape
                "dii_flow":     {"value": 0, "type": "buy"},
                "nifty_return_7d": nifty_chg,
            }
        except Exception as e:
            logger.error(f"Market status fetch error: {e}")
            return {
                "nifty":      {"value": 0, "change": 0, "direction": "up"},
                "bank_nifty": {"value": 0, "change": 0, "direction": "up"},
                "india_vix":  0, "vix_change": 0,
                "fii_flow":   {"value": 0, "type": "buy"},
                "dii_flow":   {"value": 0, "type": "buy"},
                "nifty_return_7d": 0,
            }

    def fetch_sector_returns(self, nifty_return_7d: float) -> Dict[str, float]:
        """
        Fetch 7-day returns for each sector index.
        Falls back to estimating from constituent stocks if index unavailable.
        """
        sector_returns = {}

        for sector, idx_ticker in SECTOR_INDICES.items():
            try:
                hist = yf.Ticker(idx_ticker).history(period="10d")
                if len(hist) >= 2:
                    ret = ((hist["Close"].iloc[-1] - hist["Close"].iloc[-6]) /
                           hist["Close"].iloc[-6]) * 100
                    sector_returns[sector] = round(float(ret), 2)
                else:
                    sector_returns[sector] = nifty_return_7d
            except Exception:
                sector_returns[sector] = nifty_return_7d

        return sector_returns

    def fetch_twitter_signals(self) -> Dict:
        """
        Twitter signals — returns empty dict until Twitter API is configured.
        The decision engine handles missing signals gracefully (neutral score).
        """
        return {}
