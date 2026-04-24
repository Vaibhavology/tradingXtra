"""
FINAL DECISION ENGINE — Live Data Edition
Fetches real NSE data via Yahoo Finance, then applies all momentum gates.

Decision Flow:
  Live Data → Momentum Gate → Volume Gate → Sector Gate →
  Manipulation Filter → Twitter Confirmation → Risk Rules → Rank → Top 10
"""

import logging
from typing import Dict, List
from datetime import datetime

from app.config import settings
from app.services.market_data import MarketDataService
from app.services.momentum import MomentumService
from app.services.volume import VolumeService
from app.services.sector import SectorService
from app.services.twitter_scout import TwitterScout
from app.services.manipulation import ManipulationFilter
from app.services.risk_rules import RiskRules
from app.services import data_cache

logger = logging.getLogger(__name__)


class DecisionEngine:

    def __init__(self):
        self.market_data   = MarketDataService()
        self.momentum_svc  = MomentumService()
        self.volume_svc    = VolumeService()
        self.sector_svc    = SectorService()
        self.twitter_scout = TwitterScout()
        self.manipulation  = ManipulationFilter()
        self.risk_rules    = RiskRules()

    # ── public API ────────────────────────────────────────────────────────────

    def get_market_status(self) -> Dict:
        cached = data_cache.get("market_status")
        if cached:
            return cached

        raw = self.market_data.fetch_market_status()
        result = {
            "nifty":           f"{'+' if raw['nifty']['change'] >= 0 else ''}{raw['nifty']['change']}%",
            "nifty_value":     raw["nifty"]["value"],
            "bank_nifty":      f"{'+' if raw['bank_nifty']['change'] >= 0 else ''}{raw['bank_nifty']['change']}%",
            "bank_nifty_value": raw["bank_nifty"]["value"],
            "vix":             raw["india_vix"],
            "vix_change":      raw["vix_change"],
            "top_sector":      "Fetching…",
            "fii_flow":        "+₹0Cr (live feed pending)",
            "dii_flow":        "+₹0Cr (live feed pending)",
            "market_open":     self._is_market_open(),
            "timestamp":       datetime.now().isoformat(),
        }
        data_cache.set("market_status", result)
        return result

    def get_today_picks(self) -> Dict:
        cached = data_cache.get("today_picks")
        if cached:
            return cached

        result = self._run_pipeline()
        data_cache.set("today_picks", result)
        return result

    def get_debug_output(self) -> Dict:
        """Full evaluation trace — internal use only, not exposed to frontend"""
        stocks        = self.market_data.fetch_all_stocks()
        mkt           = self.market_data.fetch_market_status()
        sector_returns = self.market_data.fetch_sector_returns(mkt["nifty_return_7d"])
        evaluations   = [self._evaluate(s, mkt, sector_returns) for s in stocks]
        rejected      = [e for e in evaluations if not e["passed_all_gates"]]
        selected      = [e["symbol"] for e in evaluations if e["passed_all_gates"]]
        return {
            "timestamp":       datetime.now().isoformat(),
            "all_evaluations": evaluations,
            "rejected":        [{"symbol": e["symbol"], "reason": e["rejection_reason"]} for e in rejected],
            "selected":        selected,
        }

    # ── pipeline ──────────────────────────────────────────────────────────────

    def _run_pipeline(self) -> Dict:
        logger.info("Decision Engine: fetching live data…")

        # 1. Fetch live data
        stocks         = self.market_data.fetch_all_stocks()
        mkt            = self.market_data.fetch_market_status()
        sector_returns = self.market_data.fetch_sector_returns(mkt["nifty_return_7d"])
        twitter_raw    = self.market_data.fetch_twitter_signals()

        logger.info(f"Fetched {len(stocks)} stocks")

        # 2. Evaluate every stock through all gates
        evaluations = [self._evaluate(s, mkt, sector_returns) for s in stocks]

        # 3. Gate counts for transparency
        passed_momentum = sum(1 for e in evaluations if e["passed_momentum_gate"])
        passed_volume   = sum(1 for e in evaluations if e["passed_volume_gate"])
        passed_sector   = sum(1 for e in evaluations if e["passed_sector_gate"])

        # 4. Keep only stocks that passed ALL gates
        passed = [e for e in evaluations if e["passed_all_gates"]]
        passed.sort(key=lambda x: x["final_score"], reverse=True)

        # 5. Sector diversification: max 3 per sector
        top_10 = self._apply_sector_limit(passed, max_per_sector=3, limit=10)

        # 6. Build final output
        picks = [self._build_pick(e) for e in top_10]

        # Update top_sector in market status
        top_sector = top_10[0]["sector"] if top_10 else "N/A"

        return {
            "date":                  datetime.now().strftime("%Y-%m-%d"),
            "market_regime":         "bullish" if mkt["nifty"]["change"] >= 0 else "bearish",
            "top_sector":            top_sector,
            "picks":                 picks,
            "total_candidates":      len(stocks),
            "passed_momentum_gate":  passed_momentum,
            "passed_volume_gate":    passed_volume,
            "passed_sector_gate":    passed_sector,
            "final_count":           len(picks),
        }

    def _evaluate(self, stock: Dict, mkt: Dict, sector_returns: Dict) -> Dict:
        symbol  = stock["symbol"]
        sector  = stock["sector"]
        prices  = stock["price_history"]
        volumes = stock["volume_history"]

        sector_return  = sector_returns.get(sector, mkt["nifty_return_7d"])
        nifty_return   = mkt["nifty_return_7d"]
        stock_return   = ((prices[-1] - prices[0]) / prices[0] * 100) if len(prices) >= 2 else 0

        # ── Gates ────────────────────────────────────────────────────────────
        mom_r  = self.momentum_svc.calculate_momentum(prices)
        vol_r  = self.volume_svc.calculate_volume_metrics(volumes)
        sec_r  = self.sector_svc.analyze_sector(sector_return, nifty_return, stock_return)

        # ── Twitter ──────────────────────────────────────────────────────────
        tw_sig  = self.twitter_scout.get_signal(symbol)
        tw_eval = self.twitter_scout.evaluate_signal(symbol, mom_r["passed"], vol_r["passed"])

        # ── Manipulation ─────────────────────────────────────────────────────
        manip_r = self.manipulation.check(
            mom_r["move_pct"],
            vol_r["volume_multiple"],
            mom_r["is_trending"],
            tw_sig["is_trending"],
            stock.get("delivery_percent", 40),
        )

        # ── Risk rules ───────────────────────────────────────────────────────
        risk_r = self.risk_rules.apply_rules(mom_r, vol_r, sec_r, manip_r, tw_eval)

        # ── Scores ───────────────────────────────────────────────────────────
        mom_score  = self.momentum_svc.get_momentum_score(mom_r["move_pct"])
        vol_score  = self.volume_svc.get_volume_score(vol_r["volume_multiple"])
        sec_score  = self.sector_svc.get_sector_score(sec_r["sector_vs_nifty"])
        tw_score   = self.twitter_scout.get_twitter_score(tw_sig)
        flow_score = self._flow_score(stock)
        tech_score = 65.0 if mom_r["is_trending"] else 40.0

        final = (
            mom_score  * settings.WEIGHT_MOMENTUM  +
            vol_score  * settings.WEIGHT_VOLUME    +
            sec_score  * settings.WEIGHT_SECTOR    +
            tech_score * settings.WEIGHT_TECHNICAL +
            flow_score * settings.WEIGHT_FLOW      +
            tw_score   * settings.WEIGHT_TWITTER
        )
        final = min(100, final + tw_eval.get("confidence_boost", 0))
        final = max(0,   final - self.manipulation.get_manipulation_score(manip_r))

        return {
            "symbol":                 symbol,
            "name":                   stock["name"],
            "sector":                 sector,
            "current_price":          stock["current_price"],
            "price_history":          prices,
            "price_move_pct":         mom_r["move_pct"],
            "volume_multiple":        vol_r["volume_multiple"],
            "sector_vs_nifty":        sec_r["sector_vs_nifty"],
            "delivery_pct":           stock.get("delivery_percent", 0),
            "passed_momentum_gate":   mom_r["passed"],
            "passed_volume_gate":     vol_r["passed"],
            "passed_sector_gate":     sec_r["passed"],
            "passed_manipulation_check": manip_r["passed"],
            "passed_all_gates":       risk_r["passed"],
            "momentum_score":         round(mom_score, 1),
            "volume_score":           round(vol_score, 1),
            "sector_score":           round(sec_score, 1),
            "technical_score":        round(tech_score, 1),
            "flow_score":             round(flow_score, 1),
            "twitter_score":          round(tw_score, 1),
            "final_score":            round(final, 1),
            "twitter_status":         tw_eval.get("twitter_status", "not_trending"),
            "twitter_boost":          tw_eval.get("confidence_boost", 0),
            "twitter_theme":          tw_eval.get("theme"),
            "rejection_reason":       risk_r["primary_rejection"]["reason"] if risk_r["primary_rejection"] else None,
            "warnings":               [r["reason"] for r in risk_r["rejections"]] +
                                      ([tw_eval["warning"]] if tw_eval.get("warning") else []),
        }

    def _build_pick(self, e: Dict) -> Dict:
        levels  = self.risk_rules.calculate_entry_sl_targets(
            e["current_price"], e["price_history"],
            "LONG" if e["price_move_pct"] >= 0 else "SHORT",
        )
        reasons = self._reasons(e)
        return {
            "symbol":          e["symbol"],
            "name":            e["name"],
            "sector":          e["sector"],
            "direction":       "LONG" if e["price_move_pct"] >= 0 else "SHORT",
            "momentum_score":  e["momentum_score"],
            "volume_multiple": e["volume_multiple"],
            "sector_strength": e["sector_vs_nifty"],
            "entry":           levels["entry"],
            "sl":              levels["sl"],
            "targets":         levels["targets"],
            "expected_move":   levels["expected_move"],
            "confidence":      round(e["final_score"] / 100, 3),
            "reasons":         reasons,
            "twitter_status":  e["twitter_status"],
            "warnings":        e["warnings"],
        }

    # ── helpers ───────────────────────────────────────────────────────────────

    def _flow_score(self, stock: Dict) -> float:
        fii = stock.get("fii_net", 0)
        dii = stock.get("dii_net", 0)
        delivery = stock.get("delivery_percent", 40)
        return (25 if fii > 0 else 0) + (25 if dii > 0 else 0) + min(50, delivery)

    def _apply_sector_limit(self, ranked: List[Dict], max_per_sector: int, limit: int) -> List[Dict]:
        counts: Dict[str, int] = {}
        result = []
        for stock in ranked:
            sec = stock["sector"]
            counts[sec] = counts.get(sec, 0) + 1
            if counts[sec] <= max_per_sector:
                result.append(stock)
            if len(result) >= limit:
                break
        return result

    def _reasons(self, e: Dict) -> List[str]:
        reasons = []
        price = e["current_price"]
        move = e["price_move_pct"]
        vol = e["volume_multiple"]
        sector_vs = e["sector_vs_nifty"]
        sector = e["sector"]
        prices = e.get("price_history", [])

        # 1. Momentum detail
        if abs(move) >= 6:
            reasons.append(f"Strong momentum: {'+'  if move > 0 else ''}{move:.1f}% move with aggressive buying")
        elif abs(move) >= 4:
            reasons.append(f"Solid momentum: {'+'  if move > 0 else ''}{move:.1f}% move in recent sessions")
        else:
            reasons.append(f"Emerging momentum: {'+'  if move > 0 else ''}{move:.1f}% building up")

        # 2. Volume confirmation
        if vol >= 3.0:
            reasons.append(f"Exceptional volume: {vol:.1f}× average — institutional interest likely")
        elif vol >= 2.0:
            reasons.append(f"Strong volume surge: {vol:.1f}× above 20-day average")
        elif vol >= 1.5:
            reasons.append(f"Volume expanding: {vol:.1f}× average — confirms conviction")

        # 3. Sector strength
        if sector_vs >= 3.0:
            reasons.append(f"{sector} sector leading market by +{sector_vs:.1f}% — strong tailwind")
        elif sector_vs >= 1.0:
            reasons.append(f"{sector} outperforming NIFTY by {sector_vs:.1f}% — sector rotation favourable")
        elif sector_vs >= 0:
            reasons.append(f"{sector} sector in line with market")

        # 4. Price level context
        if len(prices) >= 15:
            recent_high = max(prices[-15:])
            recent_low = min(prices[-15:])
            price_range = recent_high - recent_low
            if price_range > 0:
                position = (price - recent_low) / price_range
                if position > 0.9:
                    reasons.append(f"Trading near 15-session high (₹{recent_high:.0f}) — breakout territory")
                elif position < 0.2:
                    reasons.append(f"Near 15-session low — potential reversal zone (support ₹{recent_low:.0f})")
                elif position > 0.6:
                    reasons.append(f"Above midpoint of recent range — upward bias")

        # 5. Trend
        if len(prices) >= 10:
            sma10 = sum(prices[-10:]) / 10
            if price > sma10 * 1.01:
                reasons.append("Price above 10-day SMA — short-term trend is bullish")
            elif price < sma10 * 0.99:
                reasons.append("Price below 10-day SMA — caution, countertrend trade")

        # 6. Twitter/social
        if e.get("twitter_status") == "confirmed" and e.get("twitter_theme"):
            reasons.append(f"Social buzz: {e['twitter_theme']}")

        return reasons[:5]

    def _is_market_open(self) -> bool:
        now = datetime.now()
        # IST: Mon–Fri, 09:15–15:30
        if now.weekday() >= 5:
            return False
        h, m = now.hour, now.minute
        return (h == 9 and m >= 15) or (10 <= h <= 14) or (h == 15 and m <= 30)
