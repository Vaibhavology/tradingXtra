"""
Risk Rules Service
HARD REJECTION RULES - No exceptions
"""

from typing import Dict, List

class RiskRules:
    """
    Risk Rules - HARD REJECTION
    
    These rules CANNOT be overridden by any signal or score.
    
    REJECT:
    - Dead / sideways stocks
    - Low volume
    - Weak sector
    - One-day spike
    - Social hype without price
    """
    
    def apply_rules(
        self,
        momentum_result: Dict,
        volume_result: Dict,
        sector_result: Dict,
        manipulation_result: Dict,
        twitter_result: Dict
    ) -> Dict:
        """
        Apply all hard rejection rules.
        
        Returns:
            Dict with pass/fail and rejection reasons
        """
        rejections = []
        
        # Rule 1: Dead / sideways stocks
        if not momentum_result.get("passed"):
            rejections.append({
                "rule": "MOMENTUM_GATE",
                "reason": momentum_result.get("reason", "Failed momentum gate")
            })
        
        # Rule 2: Low volume
        if not volume_result.get("passed"):
            rejections.append({
                "rule": "VOLUME_GATE",
                "reason": volume_result.get("reason", "Failed volume gate")
            })
        
        # Rule 3: Weak sector
        if not sector_result.get("passed"):
            rejections.append({
                "rule": "SECTOR_GATE",
                "reason": sector_result.get("reason", "Failed sector gate")
            })
        
        # Rule 4: One-day spike
        if momentum_result.get("is_single_day_spike"):
            rejections.append({
                "rule": "SINGLE_DAY_SPIKE",
                "reason": "Single-day spike detected - not sustainable momentum"
            })
        
        # Rule 5: Manipulation detected
        if manipulation_result.get("is_suspicious"):
            rejections.append({
                "rule": "MANIPULATION_FLAG",
                "reason": manipulation_result.get("reason", "Manipulation signals detected")
            })
        
        # Rule 6: Twitter hype without price (not rejection, but ignore Twitter boost)
        twitter_warning = None
        if twitter_result.get("is_hype_only"):
            twitter_warning = "Twitter hype ignored - no price/volume confirmation"
        
        passed = len(rejections) == 0
        
        return {
            "passed": passed,
            "rejections": rejections,
            "rejection_count": len(rejections),
            "primary_rejection": rejections[0] if rejections else None,
            "twitter_warning": twitter_warning
        }
    
    def calculate_entry_sl_targets(
        self,
        current_price: float,
        price_history: List[float],
        direction: str = "LONG"
    ) -> Dict:
        """
        Calculate entry zone, stop-loss, and targets.
        
        Uses recent price action to determine levels.
        """
        if len(price_history) < 5:
            return None
        
        recent_low = min(price_history[-5:])
        recent_high = max(price_history[-5:])
        
        if direction == "LONG":
            # Entry zone: current price to slight pullback
            entry_low = round(current_price * 0.99, 2)
            entry_high = round(current_price * 1.01, 2)
            
            # Stop-loss: below recent low
            sl = round(recent_low * 0.98, 2)
            
            # Targets: based on recent range
            range_size = recent_high - recent_low
            target1 = round(current_price + range_size * 0.8, 2)
            target2 = round(current_price + range_size * 1.5, 2)
            
            # Expected move
            expected_move = round(((target1 - current_price) / current_price) * 100, 1)
        else:
            # SHORT logic (inverse)
            entry_low = round(current_price * 0.99, 2)
            entry_high = round(current_price * 1.01, 2)
            sl = round(recent_high * 1.02, 2)
            range_size = recent_high - recent_low
            target1 = round(current_price - range_size * 0.8, 2)
            target2 = round(current_price - range_size * 1.5, 2)
            expected_move = round(((current_price - target1) / current_price) * 100, 1)
        
        return {
            "entry": [entry_low, entry_high],
            "sl": sl,
            "targets": [target1, target2],
            "expected_move": expected_move
        }
