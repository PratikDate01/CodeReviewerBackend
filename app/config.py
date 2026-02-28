import os
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    cohere_api_key: str = os.getenv("COHERE_API_KEY", "")
    max_code_length: int = 50000
    
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./reviews.db")
    redis_url: str = os.getenv("REDIS_URL", "")
    
    cache_ttl: int = 3600
    environment: str = os.getenv("ENVIRONMENT", "development")
    debug: bool = os.getenv("DEBUG", "true").lower() == "true"
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    cors_origins: list = ["*"]
    
    class Config:
        env_file = str(Path(__file__).parent.parent.parent / ".env")
        case_sensitive = False


settings = Settings()
