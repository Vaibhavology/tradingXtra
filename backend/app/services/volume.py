"""
Volume Gate Service
Confirms momentum with volume expansion.

Uses PEAK volume in the last 3 sessions vs the prior baseline average.
This correctly captures momentum volume even on quiet follow-through days.
"""

from typing import Dict
from app.config import settings


class VolumeService:
    """
    Volume Gate - CONFIRMATION FILTER

    Rules:
    - ≥1.5× baseline average (peak of last 3 sessions) = acceptable
    - ≥2.0× = strong
    - Volume spike without trend = flag as suspicious
    """

    def __init__(self):
        self.min_multiple = settings.VOLUME_MIN_MULTIPLE

    def calculate_volume_metrics(self, volume_history: list) -> Dict:
        """
        Calculate volume metrics from volume history.

        Args:
            volume_history: List of last 20 volume values (oldest → newest)

        Returns:
            Dict with volume metrics and gate result
        """
        if len(volume_history) < 10:
            return {
                "passed": False,
                "volume_multiple": 0,
                "avg_baseline": 0,
                "current_volume": 0,
                "is_expanding": False,
                "reason": "Insufficient volume history",
            }

        # Peak of last 3 sessions vs baseline (everything before last 3)
        recent_3_max = max(volume_history[-3:])
        baseline     = volume_history[:-3]
        baseline_avg = sum(baseline) / len(baseline) if baseline else 1

        volume_multiple = recent_3_max / baseline_avg if baseline_avg > 0 else 0
        current_volume  = volume_history[-1]

        # Is volume trend expanding?
        recent_avg  = sum(volume_history[-5:]) / 5
        earlier_avg = sum(volume_history[:5]) / 5
        is_expanding = recent_avg > earlier_avg * 1.1

        passed = volume_multiple >= self.min_multiple

        reason = None
        if not passed:
            reason = f"Volume {volume_multiple:.1f}x < {self.min_multiple}x threshold"

        return {
            "passed":          passed,
            "volume_multiple": round(volume_multiple, 2),
            "avg_baseline":    round(baseline_avg, 0),
            "current_volume":  current_volume,
            "is_expanding":    is_expanding,
            "strength":        self._get_strength(volume_multiple),
            "reason":          reason,
        }

    def _get_strength(self, multiple: float) -> str:
        if multiple >= 2.5:
            return "very_strong"
        elif multiple >= 2.0:
            return "strong"
        elif multiple >= 1.5:
            return "acceptable"
        else:
            return "weak"

    def get_volume_score(self, volume_multiple: float) -> float:
        """Normalize volume to 0-100. 1× = 0, 3×+ = 100"""
        return min(100, max(0, (volume_multiple - 1) * 50))
