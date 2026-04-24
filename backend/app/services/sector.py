"""
Sector Gate Service
Validates sector outperformance vs NIFTY
"""

from typing import Dict
from app.config import settings

class SectorService:
    """
    Sector Gate - CONTEXT FILTER
    
    Rules:
    - Sector must outperform NIFTY
    - Weak-sector stocks → downgrade or reject
    - Stock should not underperform its sector
    """
    
    def __init__(self):
        self.min_outperformance = settings.SECTOR_MIN_OUTPERFORMANCE
    
    def analyze_sector(
        self, 
        sector_return: float, 
        nifty_return: float,
        stock_return: float = None
    ) -> Dict:
        """
        Analyze sector strength relative to NIFTY.
        
        Args:
            sector_return: 7-day sector return %
            nifty_return: 7-day NIFTY return %
            stock_return: Optional stock return for relative analysis
        
        Returns:
            Dict with sector analysis and gate result
        """
        # Sector vs NIFTY
        sector_vs_nifty = sector_return - nifty_return
        
        # Is sector outperforming?
        is_outperforming = sector_vs_nifty >= self.min_outperformance
        
        # Stock vs sector (if provided)
        stock_vs_sector = None
        stock_underperforming = False
        if stock_return is not None:
            stock_vs_sector = stock_return - sector_return
            stock_underperforming = stock_vs_sector < -1.0  # Stock lagging sector by >1%
        
        # GATE DECISION
        passed = is_outperforming and not stock_underperforming
        
        reason = None
        if not passed:
            if not is_outperforming:
                reason = f"Sector underperforming NIFTY by {abs(sector_vs_nifty):.1f}%"
            elif stock_underperforming:
                reason = f"Stock underperforming sector by {abs(stock_vs_sector):.1f}%"
        
        return {
            "passed": passed,
            "sector_return": round(sector_return, 2),
            "nifty_return": round(nifty_return, 2),
            "sector_vs_nifty": round(sector_vs_nifty, 2),
            "is_outperforming": is_outperforming,
            "stock_vs_sector": round(stock_vs_sector, 2) if stock_vs_sector else None,
            "stock_underperforming": stock_underperforming,
            "strength": self._get_strength(sector_vs_nifty),
            "reason": reason
        }
    
    def _get_strength(self, vs_nifty: float) -> str:
        """Classify sector strength"""
        if vs_nifty >= 3.0:
            return "very_strong"
        elif vs_nifty >= 2.0:
            return "strong"
        elif vs_nifty >= 0.5:
            return "moderate"
        elif vs_nifty >= 0:
            return "neutral"
        else:
            return "weak"
    
    def get_sector_score(self, sector_vs_nifty: float) -> float:
        """
        Normalize sector strength to 0-100 score.
        -2% vs NIFTY = 0 score
        +2% vs NIFTY = 100 score
        """
        return min(100, max(0, (sector_vs_nifty + 2) * 25))
    
    def get_top_sectors(self, sectors: Dict[str, float], nifty_return: float, top_n: int = 5) -> list:
        """Get top N outperforming sectors"""
        sector_scores = []
        for sector, return_pct in sectors.items():
            vs_nifty = return_pct - nifty_return
            sector_scores.append({
                "sector": sector,
                "return": return_pct,
                "vs_nifty": vs_nifty,
                "is_outperforming": vs_nifty >= self.min_outperformance
            })
        
        # Sort by vs_nifty descending
        sector_scores.sort(key=lambda x: x["vs_nifty"], reverse=True)
        return sector_scores[:top_n]
