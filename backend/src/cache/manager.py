from typing import Dict, Any, Optional
import redis
import pickle
from datetime import datetime, timedelta
from .models import CacheConfig, CacheStats

class CacheManager:
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url)
        self.default_ttl = 3600  # 1 hour
        self.stats = CacheStats()
        
    async def get(self, key: str) -> Optional[Any]:
        """Cache'den veri alır."""
        try:
            data = self.redis.get(key)
            if data:
                self.stats.hits += 1
                return pickle.loads(data)
            
            self.stats.misses += 1
            return None
            
        except Exception as e:
            self.stats.errors += 1
            raise CacheError(f"Cache get error: {str(e)}")
            
    async def set(self, key: str, value: Any,
                  ttl: int = None) -> bool:
        """Cache'e veri ekler."""
        try:
            serialized = pickle.dumps(value)
            return self.redis.setex(
                key,
                ttl or self.default_ttl,
                serialized
            )
            
        except Exception as e:
            self.stats.errors += 1
            raise CacheError(f"Cache set error: {str(e)}")
            
    async def invalidate(self, pattern: str) -> int:
        """Pattern'e uyan cache'leri temizler."""
        try:
            keys = self.redis.keys(pattern)
            if keys:
                return self.redis.delete(*keys)
            return 0
            
        except Exception as e:
            self.stats.errors += 1
            raise CacheError(f"Cache invalidate error: {str(e)}")
            
    async def get_stats(self) -> CacheStats:
        """Cache istatistiklerini döner."""
        return self.stats
        
class QueryCache:
    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager
        
    async def get_query_result(self, query: str,
                             context: Dict) -> Optional[Dict]:
        """Query sonucunu cache'den alır."""
        cache_key = self._generate_cache_key(query, context)
        return await self.cache.get(cache_key)
        
    async def cache_query_result(self, query: str,
                               context: Dict,
                               result: Dict) -> None:
        """Query sonucunu cache'e ekler."""
        cache_key = self._generate_cache_key(query, context)
        
        # Calculate TTL based on query type
        ttl = self._calculate_cache_ttl(query, result)
        
        await self.cache.set(cache_key, result, ttl)
        
    def _generate_cache_key(self, query: str,
                          context: Dict) -> str:
        """Cache key oluşturur."""
        return f"query:{hash(query)}:{hash(str(context))}"
        
    def _calculate_cache_ttl(self, query: str,
                           result: Dict) -> int:
        """Cache TTL hesaplar."""
        if 'SELECT' not in query.upper():
            return 0  # Don't cache non-SELECT queries
            
        if len(result.get('rows', [])) > 1000:
            return 300  # 5 minutes for large results
            
        return 3600  # 1 hour default