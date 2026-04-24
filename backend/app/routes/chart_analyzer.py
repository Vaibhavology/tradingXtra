from fastapi import APIRouter, UploadFile, File, HTTPException
import logging
from app.services.chart_analyzer import analyze_chart_image

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/analyze-chart")
async def analyze_chart(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    try:
        contents = await file.read()
        result = analyze_chart_image(contents, file.content_type)
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"Failed to analyze chart: {e}")
        raise HTTPException(status_code=500, detail=str(e))
