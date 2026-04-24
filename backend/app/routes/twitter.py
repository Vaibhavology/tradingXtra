"""Twitter momentum scout endpoint"""

from fastapi import APIRouter
from app.services.twitter_scout import TwitterScout
from app.models.schemas import TwitterSignalsResponse

router = APIRouter()
scout = TwitterScout()

@router.get("/twitter-signals", response_model=TwitterSignalsResponse)
async def get_twitter_signals():
    """
    Get Twitter momentum signals.
    
    NOTE: Twitter is a SUPPORTING signal only.
    - Used to discover trader attention
    - Used to confirm momentum themes
    - NEVER overrides price/volume gates
    """
    return scout.get_signals()
