import asyncio
import json
import random
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from datetime import datetime

router = APIRouter()

@router.websocket("/ws/orderbook")
async def websocket_orderbook(websocket: WebSocket, symbol: str = "NIFTY"):
    await websocket.accept()
    
    # Base price centered around 22500 (can be updated to pull from yfinance later)
    base_price = 22500.0
    
    try:
        while True:
            # Random walk for the base price
            base_price += random.uniform(-2, 2)
            
            bids = []
            asks = []
            
            # Generate 5 levels of depth
            current_bid = base_price - random.uniform(0.1, 0.5)
            current_ask = base_price + random.uniform(0.1, 0.5)
            
            for i in range(5):
                # Bids (lower prices)
                bids.append({
                    "price": round(current_bid - (i * random.uniform(0.5, 2.0)), 2),
                    "volume": random.randint(100, 5000),
                    "orders": random.randint(1, 20)
                })
                # Asks (higher prices)
                asks.append({
                    "price": round(current_ask + (i * random.uniform(0.5, 2.0)), 2),
                    "volume": random.randint(100, 5000),
                    "orders": random.randint(1, 20)
                })
                
            data = {
                "type": "orderbook",
                "symbol": symbol,
                "timestamp": datetime.now().isoformat(),
                "data": {
                    "bids": bids,
                    "asks": asks,
                    "ltp": round(base_price, 2),
                    "volume": random.randint(10000, 50000)
                }
            }
            
            await websocket.send_text(json.dumps(data))
            await asyncio.sleep(0.5)  # 500ms real-time updates
            
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WebSocket Error: {e}")
