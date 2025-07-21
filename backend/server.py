from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from typing import List
import uuid
from datetime import datetime

# Import models and services
from models import (
    StatusCheck, StatusCheckCreate, CryptoData, PatternDetection, 
    PatternDetectionCreate, CryptoAnalysisRequest, CryptoAnalysisResponse
)
from services.crypto_service import CoinGeckoService
from services.pattern_service import PatternDetectionService

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Initialize services
crypto_service = CoinGeckoService()
pattern_service = PatternDetectionService()

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Existing endpoints
@api_router.get("/")
async def root():
    return {"message": "Crypto Pattern Detector API"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.dict()
    status_obj = StatusCheck(**status_dict)
    _ = await db.status_checks.insert_one(status_obj.dict())
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]

# New crypto endpoints
@api_router.get("/crypto/supported")
async def get_supported_cryptos():
    """Get list of supported cryptocurrencies"""
    try:
        supported = crypto_service.get_supported_coins()
        return {
            "supported_cryptos": [
                {"symbol": symbol, "name": coin_id.replace('-', ' ').title(), "id": coin_id}
                for symbol, coin_id in supported.items()
            ]
        }
    except Exception as e:
        logger.error(f"Error getting supported cryptos: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch supported cryptocurrencies")

@api_router.post("/crypto/analyze", response_model=CryptoAnalysisResponse)
async def analyze_crypto(request: CryptoAnalysisRequest):
    """Analyze crypto data and detect patterns"""
    try:
        logger.info(f"Analyzing {request.symbol} for {request.days} days")
        
        # Fetch historical data
        historical_data = crypto_service.get_historical_data(request.symbol, request.days)
        
        if not historical_data:
            raise HTTPException(status_code=404, detail=f"No data found for {request.symbol}")
        
        # Get current price info
        price_info = crypto_service.get_current_price(request.symbol)
        
        # Convert to CryptoData models
        crypto_data = [CryptoData(**item) for item in historical_data]
        
        # Detect patterns
        detected_patterns = pattern_service.detect_head_and_shoulders(historical_data)
        
        # Save patterns to database
        pattern_models = []
        for pattern_data in detected_patterns:
            pattern = PatternDetectionCreate(**pattern_data)
            pattern_obj = PatternDetection(**pattern.dict())
            
            # Save to database
            await db.pattern_detections.insert_one(pattern_obj.dict())
            pattern_models.append(pattern_obj)
        
        # Save crypto data to database (optional, for caching)
        for data_point in crypto_data:
            await db.crypto_data.update_one(
                {"symbol": data_point.symbol, "date": data_point.date},
                {"$set": data_point.dict()},
                upsert=True
            )
        
        logger.info(f"Found {len(pattern_models)} patterns for {request.symbol}")
        
        return CryptoAnalysisResponse(
            symbol=request.symbol,
            current_price=price_info.get('current_price', 0),
            price_change_24h=price_info.get('current_price', 0) * price_info.get('price_change_24h', 0) / 100,
            price_change_percentage_24h=price_info.get('price_change_24h', 0),
            data=crypto_data,
            patterns=pattern_models
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing {request.symbol}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@api_router.get("/crypto/{symbol}/patterns", response_model=List[PatternDetection])
async def get_crypto_patterns(symbol: str):
    """Get historical patterns for a specific cryptocurrency"""
    try:
        patterns = await db.pattern_detections.find(
            {"symbol": symbol.upper()}
        ).sort("detected_at", -1).limit(50).to_list(50)
        
        return [PatternDetection(**pattern) for pattern in patterns]
        
    except Exception as e:
        logger.error(f"Error fetching patterns for {symbol}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch patterns")

@api_router.delete("/crypto/{symbol}/patterns")
async def clear_crypto_patterns(symbol: str):
    """Clear all patterns for a specific cryptocurrency"""
    try:
        result = await db.pattern_detections.delete_many({"symbol": symbol.upper()})
        return {"deleted_count": result.deleted_count}
        
    except Exception as e:
        logger.error(f"Error clearing patterns for {symbol}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to clear patterns")

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()