from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import uuid


class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheckCreate(BaseModel):
    client_name: str


class CryptoData(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    symbol: str
    date: str
    timestamp: int
    open_price: float = Field(alias="open")
    high_price: float = Field(alias="high")
    low_price: float = Field(alias="low")
    close_price: float = Field(alias="close")
    volume: float
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True


class PatternDetection(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    symbol: str
    pattern_type: str
    left_shoulder: float
    head: float
    right_shoulder: float
    confidence: int
    signal: str
    strength: str
    start_index: int
    center_index: int
    end_index: int
    detected_at: datetime = Field(default_factory=datetime.utcnow)


class PatternDetectionCreate(BaseModel):
    symbol: str
    pattern_type: str
    left_shoulder: float
    head: float
    right_shoulder: float
    confidence: int
    signal: str
    strength: str
    start_index: int
    center_index: int
    end_index: int


class CryptoAnalysisRequest(BaseModel):
    symbol: str
    days: int = Field(default=30, ge=7, le=365)


class CryptoAnalysisResponse(BaseModel):
    symbol: str
    current_price: float
    price_change_24h: float
    price_change_percentage_24h: float
    data: List[CryptoData]
    patterns: List[PatternDetection]