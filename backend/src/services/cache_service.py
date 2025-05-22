from typing import Any, Optional
import redis
import json
import hashlib

class CacheService:
    def __init__(self):
        self.redis = redis.Redis(
            host='localhost',
            port=6379,
            db=0,
            decode_responses=True
        )
        self.default_expire = 300  # 5 minutes
        
    def get(self, key: str) -> Optional[Any]:
        data = self.redis.get(key)
        return json.loads(data) if data else None
        
    def set(self, key: str, value: Any, expire: int = None) -> None:
        self.redis.setex(
            key,
            expire or self.default_expire,
            json.dumps(value)
        )
        
    def generate_key(self, database: str, query: str) -> str:
        # Create unique cache key based on database and query
        combined = f"{database}:{query}"
        return hashlib.md5(combined.encode()).hexdigest()
        
    def invalidate(self, pattern: str) -> None:
        keys = self.redis.keys(pattern)
        if keys:
            self.redis.delete(*keys)