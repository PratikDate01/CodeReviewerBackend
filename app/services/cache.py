import hashlib
import json
from cachetools import TTLCache
from app.config import settings

class CacheManager:
    def __init__(self, ttl=None):
        self.ttl = ttl or settings.cache_ttl
        self.cache = TTLCache(maxsize=1000, ttl=self.ttl)
    
    def get_key(self, code: str, review_mode: str) -> str:
        combined = f"{code}:{review_mode}"
        return hashlib.sha256(combined.encode()).hexdigest()
    
    def get(self, code: str, review_mode: str):
        key = self.get_key(code, review_mode)
        return self.cache.get(key)
    
    def set(self, code: str, review_mode: str, result: dict):
        key = self.get_key(code, review_mode)
        self.cache[key] = result
    
    def clear(self):
        self.cache.clear()
    
    def get_stats(self) -> dict:
        return {
            "cached_items": len(self.cache),
            "max_size": self.cache.maxsize,
            "ttl": self.ttl
        }


cache_manager = CacheManager()
