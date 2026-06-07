from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    # Project info
    PROJECT_NAME: str = "E-Commerce FastAPI"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = "sqlite:///./ecommerce.db"
    
    # JWT
    SECRET_KEY: str = "your-super-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_ENABLED: bool = False
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    # Recommendation System
    MIN_SIMILARITY_THRESHOLD: float = 0.3
    TOP_N_RECOMMENDATIONS: int = 5
    COLD_START_TRENDING_ITEMS: int = 10
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
