import os
import json
import logging
from typing import Dict, Any
from google import genai
from google.genai import types
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class ChartAnalysisResult(BaseModel):
    pattern: str
    prediction: str
    strength: int

def analyze_chart_image(image_bytes: bytes, mime_type: str) -> Dict[str, Any]:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not set")
    
    client = genai.Client(api_key=api_key)
    
    prompt = """
    You are an expert technical stock analyst and quantitative trader.
    Analyze the uploaded stock chart image.
    1. Identify the primary technical pattern (e.g., Bull Flag, Head and Shoulders, Double Bottom, Consolidation, Breakout, etc.).
    2. Provide a concise prediction of what is likely to happen next based on this pattern and standard technical analysis principles. (Keep it under 3 sentences).
    3. Assign a 'strength' value from 1 to 100 representing the conviction/reliability of this setup (100 being a textbook perfect setup).
    
    Return your analysis strictly in JSON format matching this schema:
    {
      "pattern": "String",
      "prediction": "String",
      "strength": Integer
    }
    """
    
    logger.info("Sending chart image to Gemini for analysis...")
    
    MODELS = ['gemini-2.5-flash', 'gemini-2.5-pro', 'gemini-2.5-flash-lite']
    
    last_error = None
    for model_name in MODELS:
        try:
            logger.info(f"ChartAnalyzer: trying model {model_name}")
            response = client.models.generate_content(
                model=model_name,
                contents=[
                    prompt,
                    types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=ChartAnalysisResult,
                    temperature=0.2,
                )
            )
            
            text = response.text
            return json.loads(text)
        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                logger.warning(f"ChartAnalyzer: {model_name} rate limited, trying next...")
                last_error = e
                continue
            if "503" in err_str or "UNAVAILABLE" in err_str:
                logger.warning(f"ChartAnalyzer: {model_name} unavailable (503), trying next...")
                last_error = e
                continue
            if "404" in err_str or "NOT_FOUND" in err_str:
                logger.warning(f"ChartAnalyzer: {model_name} not found, trying next...")
                last_error = e
                continue
            logger.error(f"Error analyzing chart with Gemini ({model_name}): {e}")
            raise e
            
    if last_error:
        raise last_error
