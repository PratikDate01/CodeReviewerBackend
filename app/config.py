import os
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    cohere_api_key: str = ""
    cohere_api_key_1: str = ""
    cohere_api_key_2: str = ""
    cohere_api_keys: list = []
    
    max_code_length: int = 50000
    
    database_url: str = "sqlite:///./reviews.db"
    redis_url: str = ""
    
    cache_ttl: int = 3600
    environment: str = "development"
    debug: bool = True
    log_level: str = "INFO"
    
    frontend_url: str = "https://devpilot-ai.vercel.app"
    port: int = 8000
    
    cors_origins: list = ["*"]
    
    class Config:
        env_file = str(Path(__file__).parent.parent.parent / ".env")
        case_sensitive = False
        extra = "ignore"


settings = Settings()

# Populate cohere_api_keys list from cohere_api_key_1 and cohere_api_key_2 if empty
if not settings.cohere_api_keys:
    settings.cohere_api_keys = [
        settings.cohere_api_key_1,
        settings.cohere_api_key_2
    ]
if settings.cohere_api_key and settings.cohere_api_key not in settings.cohere_api_keys:
    settings.cohere_api_keys.append(settings.cohere_api_key)
