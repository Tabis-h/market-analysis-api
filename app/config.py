import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # API Keys
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    API_KEY: str = os.getenv("API_KEY", "default-api-key-123")
    
    # Rate Limiting
    REQUESTS_PER_MINUTE: int = int(os.getenv("REQUESTS_PER_MINUTE", "10"))
    REQUESTS_PER_HOUR: int = int(os.getenv("REQUESTS_PER_HOUR", "100"))
    
    # App Settings
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    APP_TITLE: str = "Market Analysis API"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "FastAPI service for analyzing market data and providing trade opportunities"

settings = Settings()
