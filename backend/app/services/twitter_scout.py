"""
Twitter Momentum Scout Service
SUPPORTING SIGNAL ONLY - Never overrides gates

Currently: no live Twitter API configured → all signals return neutral.
When Twitter API is added, plug it into MarketDataService.fetch_twitter_signals()
and inject the dict here via set_signals().
"""

from typing import Dict, List
from datetime import datetime


class TwitterScout:
    """
    Twitter Momentum Scout - DISCOVERY & CONFIRMATION ONLY

    Rules:
    - Twitter hype WITHOUT price + volume → IGNORE
    - Twitter + price + volume → CONFIRM (boost confidence)
    - Twitter is NEVER a decision maker
    """

    def __init__(self):
        # Signals are injected by DecisionEngine from live/mock source
        self.twitter_signals: Dict = {}

    def set_signals(self, signals: Dict):
        """Inject signals from external source (live API or mock)"""
        self.twitter_signals = signals

    def get_signal(self, symbol: str) -> Dict:
        signal = self.twitter_signals.get(symbol, {})
        if not signal:
            return {
                "symbol": symbol,
                "mentions": 0,
                "engagement_score": 0,
                "theme": None,
                "sentiment": 0,
                "is_trending": False,
                "status": "not_trending",
            }
        is_trending = signal.get("mentions", 0) >= 30 and signal.get("engagement_score", 0) >= 0.6
        return {
            "symbol":           symbol,
            "mentions":         signal.get("mentions", 0),
            "engagement_score": signal.get("engagement_score", 0),
            "theme":            signal.get("theme"),
            "sentiment":        signal.get("sentiment", 0),
            "is_trending":      is_trending,
            "status":           "trending" if is_trending else "not_trending",
        }

    def evaluate_signal(self, symbol: str, has_momentum: bool, has_volume: bool) -> Dict:
        """
        Evaluate Twitter signal in context of price/volume confirmation.
        Twitter can only CONFIRM, never DECIDE.
        """
        signal = self.get_signal(symbol)

        if not signal["is_trending"]:
            return {"symbol": symbol, "twitter_status": "not_trending",
                    "confidence_boost": 0, "is_hype_only": False, "warning": None}

        # Trending but no price/volume = HYPE ONLY
        if not has_momentum or not has_volume:
            return {"symbol": symbol, "twitter_status": "hype_only",
                    "confidence_boost": 0, "is_hype_only": True,
                    "warning": "Twitter trending without price/volume confirmation - IGNORED"}

        # Trending WITH confirmation = BOOST
        boost = 5 if signal["sentiment"] < 0.7 else 10
        return {"symbol": symbol, "twitter_status": "confirmed",
                "confidence_boost": boost, "is_hype_only": False,
                "warning": None, "theme": signal.get("theme")}

    def get_twitter_score(self, signal: Dict) -> float:
        if not signal.get("is_trending"):
            return 50  # neutral
        mentions_score    = min(50, signal.get("mentions", 0) / 2)
        engagement_score  = signal.get("engagement_score", 0) * 50
        return min(100, mentions_score + engagement_score)

    def get_signals(self) -> Dict:
        signals = []
        for symbol, data in self.twitter_signals.items():
            sig = self.get_signal(symbol)
            signals.append({
                "symbol":           symbol,
                "mentions":         sig["mentions"],
                "engagement_score": sig["engagement_score"],
                "theme":            sig["theme"],
                "sentiment":        sig["sentiment"],
                "is_confirmed":     False,
            })
        return {
            "signals":   signals,
            "timestamp": datetime.now().isoformat(),
            "note":      "Twitter is a SUPPORTING signal only. Never overrides price/volume gates.",
        }
