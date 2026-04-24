"""
Momentum Gate Service
HARD FILTER: Rejects stocks without recent price momentum
"""

from typing import Dict, Tuple
from app.config import settings

class MomentumService:
    """
    Momentum Gate - THE FIRST FILTER
    
    A stock is eligible ONLY if:
    - ≥4-6% move in last 5-10 sessions
    - Higher-high / higher-close structure
    - Not a single-day spike
    """
    
    def __init__(self):
        self.min_move = settings.MOMENTUM_MIN_MOVE
    
    def calculate_momentum(self, price_history: list) -> Dict:
        """
        Calculate momentum metrics from price history.
        
        Args:
            price_history: List of last 10 closing prices (oldest to newest)
        
        Returns:
            Dict with momentum metrics and gate result
        """
        if len(price_history) < 10:
            return {
                "passed": False,
                "move_pct": 0,
                "is_trending": False,
                "is_single_day_spike": True,
                "reason": "Insufficient price history"
            }
        
        # Calculate max move in 5-10 session window
        recent_prices = price_history[-10:]
        start_price = recent_prices[0]
        current_price = recent_prices[-1]
        
        # Overall move
        overall_move = ((current_price - start_price) / start_price) * 100
        
        # Check for higher-highs (trending structure)
        higher_highs = self._check_higher_highs(recent_prices)
        
        # Check if it's a single-day spike (reject these)
        is_single_day_spike = self._is_single_day_spike(recent_prices)
        
        # Calculate max move within window
        min_price = min(recent_prices)
        max_price = max(recent_prices)
        max_move = ((max_price - min_price) / min_price) * 100
        
        # GATE DECISION
        passed = (
            abs(overall_move) >= self.min_move and
            higher_highs and
            not is_single_day_spike
        )
        
        reason = None
        if not passed:
            if abs(overall_move) < self.min_move:
                reason = f"Move {overall_move:.1f}% < {self.min_move}% threshold"
            elif not higher_highs:
                reason = "No trending structure (higher-highs)"
            elif is_single_day_spike:
                reason = "Single-day spike detected"
        
        return {
            "passed": passed,
            "move_pct": round(overall_move, 2),
            "max_move_pct": round(max_move, 2),
            "is_trending": higher_highs,
            "is_single_day_spike": is_single_day_spike,
            "reason": reason
        }
    
    def _check_higher_highs(self, prices: list) -> bool:
        """Check if price is making higher highs (bullish) or lower lows (bearish)"""
        if len(prices) < 5:
            return False
        
        # Split into two halves
        first_half = prices[:5]
        second_half = prices[5:]
        
        # Bullish: second half highs > first half highs
        bullish = max(second_half) > max(first_half)
        
        # Bearish: second half lows < first half lows
        bearish = min(second_half) < min(first_half)
        
        return bullish or bearish
    
    def _is_single_day_spike(self, prices: list) -> bool:
        """
        Detect if the move is just a single-day spike.
        A spike is when one day accounts for >60% of the total move.
        """
        if len(prices) < 3:
            return True
        
        total_move = abs(prices[-1] - prices[0])
        if total_move == 0:
            return True
        
        # Find the largest single-day move
        max_daily_move = 0
        for i in range(1, len(prices)):
            daily_move = abs(prices[i] - prices[i-1])
            max_daily_move = max(max_daily_move, daily_move)
        
        # If one day accounts for >60% of total move, it's a spike
        return (max_daily_move / total_move) > 0.6
    
    def get_momentum_score(self, move_pct: float) -> float:
        """
        Normalize momentum to 0-100 score.
        0% move = 0 score
        10%+ move = 100 score
        """
        return min(100, max(0, move_pct * 10))
