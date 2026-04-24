"""
Manipulation Filter Service
Distinguishes real momentum from pump-and-dump
"""

from typing import Dict

class ManipulationFilter:
    """
    Manipulation Filter - SMART DETECTION
    
    Rules:
    - Volume high AND trend strong → VALID momentum
    - Volume high AND NO trend → FLAG as suspicious
    - Twitter hype AND NO price action → IGNORE
    
    Do NOT punish genuine momentum.
    """
    
    def check(
        self,
        price_move: float,
        volume_multiple: float,
        is_trending: bool,
        twitter_trending: bool,
        delivery_pct: float
    ) -> Dict:
        """
        Check for manipulation signals.
        
        Args:
            price_move: % price move in period
            volume_multiple: Volume vs 20-day average
            is_trending: Is price making higher-highs?
            twitter_trending: Is stock trending on Twitter?
            delivery_pct: Delivery percentage (higher = more genuine)
        
        Returns:
            Dict with manipulation check result
        """
        flags = []
        is_suspicious = False
        
        # High volume without trend = suspicious
        if volume_multiple >= 2.0 and not is_trending:
            flags.append("High volume without trending structure")
            is_suspicious = True
        
        # High volume without price move = suspicious
        if volume_multiple >= 2.0 and abs(price_move) < 2.0:
            flags.append("Volume spike without price movement")
            is_suspicious = True
        
        # Twitter hype without price action = ignore (not manipulation, just hype)
        if twitter_trending and abs(price_move) < 3.0:
            flags.append("Twitter hype without price confirmation")
            # Not necessarily manipulation, but should be ignored
        
        # Low delivery on high volume = potential manipulation
        if volume_multiple >= 2.0 and delivery_pct < 30:
            flags.append("Low delivery on high volume - potential intraday manipulation")
            is_suspicious = True
        
        # VALID MOMENTUM: High volume + trend + decent delivery
        is_valid_momentum = (
            volume_multiple >= 1.5 and
            is_trending and
            abs(price_move) >= 4.0 and
            delivery_pct >= 35
        )
        
        return {
            "passed": not is_suspicious,
            "is_suspicious": is_suspicious,
            "is_valid_momentum": is_valid_momentum,
            "flags": flags,
            "reason": flags[0] if flags else None
        }
    
    def get_manipulation_score(self, check_result: Dict) -> float:
        """
        Return a penalty score for manipulation signals.
        0 = no penalty (clean)
        Higher = more suspicious
        """
        if check_result["is_valid_momentum"]:
            return 0
        
        penalty = len(check_result["flags"]) * 15
        return min(50, penalty)
