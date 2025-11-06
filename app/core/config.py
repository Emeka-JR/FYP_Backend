from pydantic import BaseModel
from typing import List, ClassVar
from functools import lru_cache

class Settings(BaseModel):
    PROJECT_NAME: str = "Covenant University News Aggregator"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # CORS Configuration
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:4200",
        "http://127.0.0.1:4200",
        "http://localhost:8000",
        "http://127.0.0.1:8000"
    ]
    
    # MongoDB settings
    MONGODB_URL: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "cu_news_aggregator"
    
    # JWT settings
    SECRET_KEY: str = "your-secret-key-here"  # Change this in production!
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # News Categories
    NEWS_CATEGORIES: ClassVar[List[str]] = [
        "Academics",
        "Events",
        "Sports",
        "Technology and Innovation",
        "Chaplaincy",
        "Opportunities"
    ]
    
    class Config:
        case_sensitive = True
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings() 