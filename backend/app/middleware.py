import time
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger(__name__)

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        # In-memory dictionary: { "ip_address": [{"time": float, "is_llm": bool}] }
        self.rate_limits = {}
        
        # Define limits
        self.LLM_LIMIT = 5   # 5 requests per minute for AI/Gemini endpoints
        self.GENERAL_LIMIT = 100 # 100 requests per minute for general endpoints
        self.WINDOW = 60 # 60 seconds (1 minute)

    async def dispatch(self, request: Request, call_next):
        # Extract IP, handling reverse proxies (like Nginx/Vercel)
        client_ip = request.client.host if request.client else "unknown"
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()

        path = request.url.path
        
        # Don't limit static assets or health checks
        if path.startswith("/docs") or path.startswith("/openapi.json"):
            return await call_next(request)
            
        current_time = time.time()
        
        if client_ip not in self.rate_limits:
            self.rate_limits[client_ip] = []
            
        # Clean up requests older than our time window
        self.rate_limits[client_ip] = [
            t for t in self.rate_limits[client_ip] 
            if current_time - t["time"] < self.WINDOW
        ]
        
        # Check if the route is an expensive LLM endpoint
        is_llm_route = "analyze-chart" in path or "market-brief" in path
        limit = self.LLM_LIMIT if is_llm_route else self.GENERAL_LIMIT
        
        # Count requests in the current window for this specific route type
        route_count = sum(1 for t in self.rate_limits[client_ip] if t["is_llm"] == is_llm_route)
        
        if route_count >= limit:
            logger.warning(f"Rate limit exceeded for IP {client_ip} on {path} (Limit: {limit}/min)")
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded. Please try again later.",
                    "code": "rate_limit_exceeded"
                }
            )
            
        # Record the current request
        self.rate_limits[client_ip].append({"time": current_time, "is_llm": is_llm_route})
        
        # Proceed with the request
        return await call_next(request)
