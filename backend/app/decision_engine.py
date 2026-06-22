"""
TradingXtra Phase 2.5 — Decision Engine (Precision Upgrade)

Pipeline:  Data → Agents → News → Regime → Features → Adjusted WScore → P(win) → EV → Accept/Reject

Phase 2.5 upgrades:
  - SE driven by news_service.get_symbol_sentiment() (capped at 0.7)
  - Regime affects risk parameters (SL/target multipliers, P(win) threshold)
  - Market bias integrated into MA scoring
  - VIX/risk alerts boost MR penalty
  - Sideways regime dampens breakout PS
  - Enhanced reasoning with sentiment, bias, and regime context
"""

import math
import logging
from typing import Dict, List, Optional, Tuple

from app.feature_engine import compute_features, calculate_atr
from app.data_fetcher import ensure_data, get_stock_data, NSE_STOCKS

# Agents
from app.agents import pattern_agent, sector_agent, liquidity_agent
from app.agents import manipulation_agent, regime_detector

# News
from app.services.news_service import get_symbol_sentiment

logger = logging.getLogger(__name__)


def _sanitize(obj):
    """Recursively replace NaN/Infinity float values with 0.0 so JSON serialization never fails."""
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize(v) for v in obj]
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return 0.0
    return obj


# ── Scoring Parameters ───────────────────────────────────────────────
BASE_WEIGHTS = {
    "PS": 0.22,   # Pattern Strength
    "MA": 0.18,   # Market Alignment
    "SS": 0.15,   # Sector Strength
    "VC": 0.15,   # Volume Confirmation
    "LS": 0.10,   # Liquidity Score
    "SE": 0.10,   # Sentiment Score
    "MR": 0.10,   # Manipulation Risk (inverted)
}

# Regime-aware weight multipliers (re-normalized after application)
REGIME_ADJUSTMENTS = {
    "trending":  {"PS": 1.15, "MA": 1.15, "MR": 0.90},
    "sideways":  {"PS": 0.80, "MA": 0.85, "SS": 1.20},
    "volatile":  {"PS": 0.75, "MR": 1.30, "LS": 1.10},
}

# Regime-specific risk parameters
REGIME_RISK_PARAMS = {
    "trending":  {"sl_mult": 1.5, "tgt_mult": 2.5, "p_win_boost": -0.02},
    "sideways":  {"sl_mult": 1.5, "tgt_mult": 2.0, "p_win_boost": 0.0},
    "volatile":  {"sl_mult": 1.2, "tgt_mult": 1.8, "p_win_boost": 0.05},
}
DEFAULT_RISK_PARAMS = {"sl_mult": 1.5, "tgt_mult": 2.0, "p_win_boost": 0.0}

K = 10.0
THETA = 0.55

MIN_P_WIN = 0.55
MIN_RR_RATIO = 1.3
MIN_ATR_ABS = 0.5
MIN_EV = 0.0

# Market bias adjustments for MA feature
BIAS_MA_BOOST = {"Bullish": 0.04, "Bearish": -0.04, "Neutral": 0.0}

# VIX threshold for MR penalty
VIX_HIGH_THRESHOLD = 20.0
VIX_MR_PENALTY = 0.08


# ── Core Functions ───────────────────────────────────────────────────

def _get_adjusted_weights(regime: str) -> Dict[str, float]:
    """Apply regime-specific weight multipliers, re-normalize to sum=1."""
    adjustments = REGIME_ADJUSTMENTS.get(regime, {})
    adjusted = {}
    for key, base_w in BASE_WEIGHTS.items():
        adjusted[key] = base_w * adjustments.get(key, 1.0)

    total = sum(adjusted.values())
    if total > 0:
        adjusted = {k: v / total for k, v in adjusted.items()}
    return adjusted


def weighted_score(features: Dict[str, float], weights: Dict[str, float]) -> float:
    """WScore = Σ (weight_i × feature_i), MR inverted."""
    wscore = (
        weights["PS"] * features["PS"]
        + weights["MA"] * features["MA"]
        + weights["SS"] * features["SS"]
        + weights["VC"] * features["VC"]
        + weights["LS"] * features["LS"]
        + weights["SE"] * features["SE"]
        + weights["MR"] * (1.0 - features["MR"])
    )
    return round(wscore, 4)


def probability_of_win(wscore: float) -> float:
    """P(win) = 1 / (1 + exp(-K × (WScore - θ)))"""
    z = K * (wscore - THETA)
    z_clamped = max(-20.0, min(20.0, z))
    return round(1.0 / (1.0 + math.exp(-z_clamped)), 4)


def compute_risk_reward(closes, highs, lows, sl_mult=1.5, tgt_mult=2.0) -> Dict:
    """ATR-based entry/SL/target with regime-adjustable multipliers."""
    entry = closes[-1]
    atr = calculate_atr(highs, lows, closes, period=14)
    risk_dist = sl_mult * atr
    reward_dist = tgt_mult * atr
    sl = entry - risk_dist
    target = entry + reward_dist
    risk = abs(entry - sl)
    reward = abs(target - entry)
    rr_ratio = reward / risk if risk > 0 else 0.0
    return {
        "entry": round(entry, 2), "stop_loss": round(sl, 2),
        "target": round(target, 2), "atr": round(atr, 2),
        "risk": round(risk, 2), "reward": round(reward, 2),
        "reward_risk": round(rr_ratio, 2),
    }


def _stock_adjusted_risk_params(
    regime_params: Dict,
    pattern_score: float,
    pattern_confidence: float,
    sector_score: float,
    PS: float,
    MR: float,
    VC: float,
) -> Dict:
    """
    Create per-stock SL/target multipliers by adjusting regime base values.

    This ensures each stock gets a unique R:R ratio instead of all stocks
    in the same regime sharing the same ratio (since ATR cancels out).

    Adjustments (additive to regime base multipliers):
      - Pattern confidence: strong pattern → wider target (+0.30 max)
      - Sector strength:    strong sector → wider target (+0.15 max)
      - Momentum (PS):      strong momentum → wider target (+0.20 max)
      - Manipulation risk:  high MR → wider SL (+0.15 max), tighter target
      - Volume confirm:     strong volume → wider target (+0.10 max)

    All results clamped to realistic bounds.
    """
    base_sl = regime_params["sl_mult"]
    base_tgt = regime_params["tgt_mult"]

    # ── Target adjustments (how far can price reasonably go?) ─────
    tgt_adj = 0.0

    # Strong pattern + high confidence → can set wider target
    if pattern_score >= 0.7 and pattern_confidence >= 0.65:
        tgt_adj += 0.30 * pattern_score  # up to +0.21
    elif pattern_score >= 0.5:
        tgt_adj += 0.15 * pattern_score  # up to +0.10
    elif pattern_score < 0.35:
        tgt_adj -= 0.10  # Weak pattern → pull in target

    # Sector tailwind → can ride further
    if sector_score >= 0.6:
        tgt_adj += 0.15 * (sector_score - 0.5)  # up to +0.075
    elif sector_score < 0.4:
        tgt_adj -= 0.08  # Sector headwind → conservative target

    # Momentum (PS) → strong momentum supports wider targets
    if PS >= 0.65:
        tgt_adj += 0.20 * (PS - 0.5)  # up to +0.10
    elif PS < 0.35:
        tgt_adj -= 0.10

    # Volume confirmation → more conviction in target
    if VC >= 0.65:
        tgt_adj += 0.10 * (VC - 0.5)  # up to +0.05

    # ── SL adjustments (how much room does the trade need?) ──────
    sl_adj = 0.0

    # High manipulation risk → need wider SL buffer
    if MR >= 0.5:
        sl_adj += 0.15 * MR  # up to +0.15 wider SL
        tgt_adj -= 0.05  # Also slightly reduce target ambition
    elif MR >= 0.3:
        sl_adj += 0.08 * MR  # up to +0.08

    # Low confidence pattern → slightly wider SL (more room for noise)
    if pattern_confidence < 0.5:
        sl_adj += 0.08

    # ── Apply + clamp ────────────────────────────────────────────
    final_sl = max(1.0, min(2.0, base_sl + sl_adj))
    final_tgt = max(1.5, min(3.5, base_tgt + tgt_adj))

    return {
        "sl_mult": round(final_sl, 3),
        "tgt_mult": round(final_tgt, 3),
        "p_win_boost": regime_params.get("p_win_boost", 0.0),
    }


def _build_trade_analysis(
    symbol: str,
    meta: Dict,
    decision: str,
    features: Dict[str, float],
    pattern_result: Dict,
    sector_result: Dict,
    liquidity_result: Dict,
    manipulation_result: Dict,
    regime: str,
    market_bias: str,
    SE: float,
    p_win: float,
    rr: Dict,
    ev: float,
    vix_level: Optional[float],
) -> Dict:
    """
    Build a structured trade analysis with:
      - description: 2-3 sentence trade thesis unique to this stock
      - pros: list of bullish factors
      - cons: list of risk factors
    """
    name = meta.get("name", symbol)
    sector = meta.get("sector", "Unknown")
    pattern_type = pattern_result.get("pattern", "none")
    pattern_score = pattern_result.get("pattern_score", 0)
    pattern_conf = pattern_result.get("confidence", 0)
    sector_score = sector_result.get("sector_strength", 0.5)
    liq_score = liquidity_result.get("liquidity_score", 0.5)
    manip_risk = manipulation_result.get("manipulation_risk", 0)

    # ── Build description ────────────────────────────────────────
    desc_parts = []

    # Lead with the pattern (what triggered the trade)
    pattern_label = pattern_type.replace("_", " ").title()
    if pattern_type not in ("none", "unknown") and pattern_score >= 0.4:
        strength_word = "strong" if pattern_score >= 0.7 else "moderate" if pattern_score >= 0.5 else "developing"
        desc_parts.append(
            f"{name} is showing a {strength_word} {pattern_label} pattern "
            f"with {pattern_conf:.0%} confidence."
        )
    else:
        desc_parts.append(
            f"{name} is being evaluated based on its technical and fundamental profile."
        )

    # Sector context
    if sector_score >= 0.6:
        desc_parts.append(
            f"The {sector} sector is showing relative strength, providing a tailwind."
        )
    elif sector_score < 0.4:
        desc_parts.append(
            f"The {sector} sector is currently weak, which may limit upside."
        )

    # Key metric summary
    desc_parts.append(
        f"At ₹{rr['entry']}, the trade offers a {rr['reward_risk']:.1f}x risk-reward "
        f"with a {p_win:.0%} probability of success and expected value of ₹{ev:.1f} per share."
    )

    description = " ".join(desc_parts)

    # ── Build pros ───────────────────────────────────────────────
    pros = []

    if pattern_type not in ("none", "unknown") and pattern_score >= 0.5:
        pros.append(f"{pattern_label} pattern detected (score: {pattern_score:.2f})")

    if sector_score >= 0.6:
        pros.append(f"{sector} sector outperforming (strength: {sector_score:.2f})")

    if features.get("VC", 0) >= 0.6:
        pros.append("Volume confirming the price move")

    if features.get("MA", 0) >= 0.6:
        pros.append("Aligned with broader market direction")

    if SE >= 0.55:
        pros.append(f"Positive news sentiment (score: {SE:.2f})")

    if liq_score >= 0.7:
        pros.append("High liquidity — tight spreads, easy execution")

    if manip_risk < 0.1:
        pros.append("Clean price action — no manipulation detected")

    if market_bias == "Bullish":
        pros.append("Bullish market bias supports long positions")

    if p_win >= 0.7:
        pros.append(f"High conviction: {p_win:.0%} win probability")
    elif p_win >= 0.6:
        pros.append(f"Moderate conviction with edge: P(win) = {p_win:.0%}")

    if rr["reward_risk"] >= 2.0:
        pros.append(f"Strong risk-reward ratio of {rr['reward_risk']:.1f}x")

    if ev > 5:
        pros.append(f"Significant expected value: ₹{ev:.1f} per share")

    if regime == "trending":
        pros.append("Trending regime favors momentum trades")

    # ── Build cons ───────────────────────────────────────────────
    cons = []

    if manip_risk >= 0.5:
        cons.append(f"High manipulation risk ({manip_risk:.2f}) — suspicious price action")
    elif manip_risk >= 0.3:
        cons.append(f"Moderate manipulation signals detected (risk: {manip_risk:.2f})")

    if liq_score < 0.4:
        cons.append(f"Low liquidity (score: {liq_score:.2f}) — slippage and exit risk")

    if features.get("VC", 1) < 0.35:
        cons.append("Weak volume — move lacks conviction from participants")

    if SE < 0.4:
        cons.append(f"Negative news sentiment (score: {SE:.2f})")
    elif SE < 0.5:
        cons.append("Mixed/neutral news sentiment — no catalyst support")

    if features.get("MA", 1) < 0.35:
        cons.append("Trading against the broader market trend")

    if sector_score < 0.4:
        cons.append(f"{sector} sector underperforming — headwind")

    if market_bias == "Bearish":
        cons.append("Bearish market bias increases downside risk")

    if regime == "volatile":
        cons.append("Volatile regime — wider stops needed, false signals more likely")
    elif regime == "sideways":
        cons.append("Sideways regime — higher risk of false breakouts")

    if vix_level and vix_level > VIX_HIGH_THRESHOLD:
        cons.append(f"Elevated VIX at {vix_level:.1f} — market uncertainty")

    if p_win < 0.6:
        cons.append(f"Lower conviction trade (P(win) = {p_win:.0%})")

    if rr["reward_risk"] < 1.5:
        cons.append(f"Modest risk-reward ratio ({rr['reward_risk']:.1f}x)")

    if pattern_type in ("none", "unknown") or pattern_score < 0.4:
        cons.append("No strong chart pattern identified")

    return {
        "description": description,
        "pros": pros[:6],  # Cap at 6 most relevant
        "cons": cons[:5],  # Cap at 5
    }


def calculate_ev(p_win, risk, reward) -> float:
    """EV = P(win) × Reward - (1 - P(win)) × Risk"""
    return round(p_win * reward - (1.0 - p_win) * risk, 2)


def should_reject(p_win, ev, rr_ratio, atr, p_win_threshold=None) -> Tuple[bool, Optional[str]]:
    """Hard rejection rules with adjustable P(win) threshold."""
    min_p = p_win_threshold if p_win_threshold is not None else MIN_P_WIN

    if ev <= MIN_EV:
        return True, f"Negative EV: ₹{ev}"

    if p_win < min_p:
        return True, f"P(win) = {p_win:.2%} < {min_p:.0%} threshold"

    if rr_ratio < MIN_RR_RATIO:
        return True, f"R:R ratio {rr_ratio:.1f} < {MIN_RR_RATIO} minimum"

    if atr < MIN_ATR_ABS:
        return True, f"ATR = ₹{atr:.2f} too low (illiquid or flat)"

    return False, None


# ── Main Entry Point ─────────────────────────────────────────────────

def evaluate(symbol: str, allow_stale: bool = False) -> Dict:
    """
    Full Phase 2.5 evaluation pipeline.

    Steps:
        1. Fetch data (cache → DB → yfinance)
        2. Run agents (pattern, sector, liquidity, manipulation)
        3. Detect regime + get VIX
        4. Get news sentiment (SE)
        5. Compute market bias
        6. Build features (agent-enhanced + context-adjusted)
        7. Regime-adjusted weights → WScore → P(win)
        8. Regime-adjusted risk → SL/target/EV
        9. Rejection rules
        10. Build reasoning + response
    """
    symbol = symbol.upper().strip()
    meta = NSE_STOCKS.get(symbol, {"name": symbol, "sector": "Unknown"})

    logger.info(f"[{symbol}] Starting evaluation...")

    # ── Step 1: Data ─────────────────────────────────────────────
    stock_data = ensure_data(symbol, allow_stale=allow_stale)

    if len(stock_data) < 20:
        logger.warning(f"[{symbol}] Insufficient data: {len(stock_data)} rows")
        return {
            "symbol": symbol, "name": meta.get("name", symbol),
            "sector": meta.get("sector", "Unknown"),
            "score": 0.0, "probability": 0.0, "ev": 0.0,
            "entry": 0.0, "stop_loss": 0.0, "target": 0.0,
            "atr": 0.0, "reward_risk": 0.0,
            "decision": "NO_DATA",
            "rejection_reason": f"Insufficient data: {len(stock_data)} rows",
            "features": {}, "agents": {}, "regime": "unknown",
            "reasoning": [], "data_points": len(stock_data),
        }

    market_data = get_stock_data("NIFTY50", days=120)
    vix_data = get_stock_data("INDIAVIX", days=30)

    # ── Step 2: Run Agents ───────────────────────────────────────
    pattern_result = pattern_agent.analyze(stock_data)
    sector_result = sector_agent.analyze(symbol, stock_data, market_data)
    liquidity_result = liquidity_agent.analyze(stock_data)
    manipulation_result = manipulation_agent.analyze(stock_data)

    # ── Step 3: Regime Detection ─────────────────────────────────
    regime_result = regime_detector.detect(
        market_ohlcv=market_data if len(market_data) >= 20 else None,
        vix_ohlcv=vix_data if vix_data else None,
    )
    regime = regime_result.get("regime", "unknown")

    # ── Step 4: News Sentiment → SE ──────────────────────────────
    try:
        se_raw = get_symbol_sentiment(symbol)
        SE = min(se_raw, 0.7)  # Hard cap — news cannot dominate
    except Exception as e:
        logger.warning(f"[{symbol}] Sentiment fetch failed: {e}")
        SE = 0.5  # Neutral fallback

    # ── Step 4b: Invest Smart boost (YouTube) ─────────────────────
    try:
        from app.services.market_brief import get_invest_smart_stocks
        if symbol in get_invest_smart_stocks():
            SE = min(SE + 0.05, 0.7)  # Light boost only, still capped
    except Exception:
        pass  # Non-critical — silently skip

    # ── Step 5: Market Bias ──────────────────────────────────────
    if len(market_data) >= 6:
        mkt_closes = [r["close"] for r in market_data]
        mkt_ret_5d = (mkt_closes[-1] - mkt_closes[-6]) / mkt_closes[-6] * 100
        if mkt_ret_5d > 1.5:
            market_bias = "Bullish"
        elif mkt_ret_5d < -1.5:
            market_bias = "Bearish"
        else:
            market_bias = "Neutral"
    else:
        mkt_ret_5d = 0.0
        market_bias = "Neutral"

    # VIX level
    vix_level = vix_data[-1]["close"] if vix_data else None

    # ── Step 6: Build Features (agent + context) ─────────────────
    base_features = compute_features(
        ohlcv=stock_data,
        market_ohlcv=market_data if len(market_data) >= 5 else None,
    )

    # Start with agent outputs replacing neutral placeholders
    PS = 0.60 * base_features["PS"] + 0.40 * pattern_result["pattern_score"]
    MA = base_features["MA"]
    SS = sector_result["sector_strength"]
    VC = base_features["VC"]
    LS = liquidity_result["liquidity_score"]
    MR = manipulation_result["manipulation_risk"]

    # ── Context adjustments ──────────────────────────────────────

    # Market bias → MA boost/penalty
    ma_adj = BIAS_MA_BOOST.get(market_bias, 0.0)
    MA = max(0.0, min(1.0, MA + ma_adj))

    # VIX high → increase MR penalty
    if vix_level and vix_level > VIX_HIGH_THRESHOLD:
        MR = min(1.0, MR + VIX_MR_PENALTY)

    # Sideways regime + breakout pattern → dampen PS
    if regime == "sideways" and pattern_result["pattern"] == "breakout":
        PS = max(0.0, PS - 0.08)  # High false breakout risk

    features = {
        "PS": round(PS, 4),
        "MA": round(MA, 4),
        "SS": round(SS, 4),
        "VC": round(VC, 4),
        "LS": round(LS, 4),
        "SE": round(SE, 4),
        "MR": round(MR, 4),
    }

    logger.info(f"[{symbol}] Features: {features} | Regime: {regime} | Bias: {market_bias}")

    # ── Step 7: Regime-Adjusted Score + Probability ──────────────
    weights = _get_adjusted_weights(regime)
    wscore = weighted_score(features, weights)
    p_win = probability_of_win(wscore)

    logger.info(f"[{symbol}] WScore={wscore}, P(win)={p_win}")

    # ── Step 8: Per-Stock Adjusted Risk / Reward + EV ─────────────
    closes = [r["close"] for r in stock_data]
    highs = [r["high"] for r in stock_data]
    lows = [r["low"] for r in stock_data]

    base_risk_params = REGIME_RISK_PARAMS.get(regime, DEFAULT_RISK_PARAMS)
    risk_params = _stock_adjusted_risk_params(
        regime_params=base_risk_params,
        pattern_score=pattern_result["pattern_score"],
        pattern_confidence=pattern_result["confidence"],
        sector_score=sector_result["sector_strength"],
        PS=PS,
        MR=MR,
        VC=features["VC"],
    )
    rr = compute_risk_reward(
        closes, highs, lows,
        sl_mult=risk_params["sl_mult"],
        tgt_mult=risk_params["tgt_mult"],
    )
    ev = calculate_ev(p_win, risk=rr["risk"], reward=rr["reward"])

    logger.info(f"[{symbol}] Entry={rr['entry']}, SL={rr['stop_loss']}, "
                f"Tgt={rr['target']}, ATR={rr['atr']}, RR={rr['reward_risk']}, EV={ev}")

    # ── Step 9: Rejection Rules ──────────────────────────────────
    p_win_threshold = MIN_P_WIN + risk_params["p_win_boost"]
    rejected, reason = should_reject(p_win, ev, rr["reward_risk"], rr["atr"], p_win_threshold)
    decision = "REJECT" if rejected else "ACCEPT"

    if rejected:
        logger.info(f"[{symbol}] REJECTED: {reason}")
    else:
        logger.info(f"[{symbol}] ACCEPTED — EV=₹{ev}, P(win)={p_win:.0%}")

    # ── Step 10: Build Reasoning ─────────────────────────────────
    reasoning = []

    # Pattern
    reasoning.append(pattern_result["explanation"])

    # Sector + persistence
    reasoning.append(sector_result["explanation"])

    # Sentiment
    if SE > 0.55:
        reasoning.append(f"Positive news sentiment (SE={SE:.2f})")
    elif SE < 0.45:
        reasoning.append(f"Negative news sentiment (SE={SE:.2f})")
    else:
        reasoning.append("Neutral news sentiment")

    # Market bias
    if market_bias != "Neutral":
        reasoning.append(f"Market bias: {market_bias} (NIFTY {mkt_ret_5d:+.1f}% 5d)")

    # Liquidity
    if liquidity_result["liquidity_score"] < 0.4:
        reasoning.append(f"⚠ {liquidity_result['explanation']}")

    # Manipulation
    if manipulation_result["manipulation_risk"] > 0.3:
        reasoning.append(f"⚠ {manipulation_result['explanation']}")
    elif manipulation_result["manipulation_risk"] < 0.1:
        reasoning.append("Clean price action — no manipulation signals")

    # VIX context
    if vix_level and vix_level > VIX_HIGH_THRESHOLD:
        reasoning.append(f"⚠ India VIX elevated at {vix_level:.1f} — increased risk")

    # Regime
    reasoning.append(f"Regime: {regime_result['explanation']}")

    # ── Step 11: Build Trade Analysis (description + pros/cons) ──
    trade_analysis = _build_trade_analysis(
        symbol=symbol,
        meta=meta,
        decision=decision,
        features=features,
        pattern_result=pattern_result,
        sector_result=sector_result,
        liquidity_result=liquidity_result,
        manipulation_result=manipulation_result,
        regime=regime,
        market_bias=market_bias,
        SE=SE,
        p_win=p_win,
        rr=rr,
        ev=ev,
        vix_level=vix_level,
    )

    # ── Response ─────────────────────────────────────────────────
    agents_summary = {
        "pattern": {
            "score": pattern_result["pattern_score"],
            "type": pattern_result["pattern"],
            "confidence": pattern_result["confidence"],
        },
        "sector": {
            "score": sector_result["sector_strength"],
            "sector": sector_result["sector"],
            "confidence": sector_result["confidence"],
        },
        "liquidity": {
            "score": liquidity_result["liquidity_score"],
            "confidence": liquidity_result["confidence"],
        },
        "manipulation": {
            "risk": manipulation_result["manipulation_risk"],
            "confidence": manipulation_result["confidence"],
        },
        "regime": {
            "regime": regime,
            "confidence": regime_result["confidence"],
        },
        "sentiment": {
            "score": SE,
            "source": "news_rss",
        },
    }

    return _sanitize({
        "symbol": symbol,
        "name": meta.get("name", symbol),
        "sector": meta.get("sector", "Unknown"),
        "score": wscore,
        "probability": p_win,
        "ev": ev,
        "entry": rr["entry"],
        "stop_loss": rr["stop_loss"],
        "target": rr["target"],
        "atr": rr["atr"],
        "reward_risk": rr["reward_risk"],
        "decision": decision,
        "rejection_reason": reason,
        "features": features,
        "agents": agents_summary,
        "regime": regime,
        "market_bias": market_bias,
        "reasoning": reasoning,
        "trade_analysis": trade_analysis,
        "data_points": len(stock_data),
    })
