from pydantic import BaseModel, field_validator, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime

class ApiKeyInfo(BaseModel):
    """Information about API key usage"""
    key_hash: str
    requests_made: int
    last_used: str
    created_at: str

class SectorAnalysisResponse(BaseModel):
    sector: str
    analysis_report: str
    timestamp: str
    data_sources: int
    session_id: str

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    timestamp: str

class HealthCheck(BaseModel):
    status: str
    timestamp: str
    version: str
    gemini_api_configured: bool

class RateLimitInfo(BaseModel):
    requests_per_minute: int
    requests_per_hour: int
    current_usage: Dict[str, int]

class SectorRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "sector": "pharmaceuticals"
            }
        }
    )
    
    sector: str
    
    @field_validator('sector')
    @classmethod
    def validate_sector(cls, v: str) -> str:
        if not v or len(v.strip()) == 0:
            raise ValueError('Sector name cannot be empty')
        
        # List of supported sectors
        supported_sectors = [
            'pharmaceuticals', 'technology', 'banking', 'automotive', 
            'agriculture', 'energy', 'steel', 'cement', 'fmcg', 'telecom',
            'textiles', 'aviation', 'real_estate', 'infrastructure',
            'chemicals', 'mining', 'oil_gas', 'power', 'retail',
            'media', 'hospitality', 'defense'
        ]
        
        sector_lower = v.strip().lower()
        if sector_lower not in supported_sectors:
            # Allow any sector but warn about supported ones
            pass
            
        return v.strip()

class MarketData(BaseModel):
    sector: str
    companies: List[str]
    news_articles: int
    market_indicators: Dict[str, Any]
    timestamp: str

class AnalysisMetrics(BaseModel):
    processing_time: float
    data_points_collected: int
    ai_tokens_used: Optional[int] = None
    cache_hit: bool = False
