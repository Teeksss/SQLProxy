from typing import Dict, Optional, Any
import hashlib
import json
import redis
from datetime import datetime, timedelta
from dataclasses import dataclass

@dataclass
class CacheConfig:
    ttl: int  # seconds
    max_size: int  # MB
    strategy: str  # LRU, LFU, FIFO
    compression: bool

class CacheManager:
    def __init__(self, config: CacheConfig):
        self.config = config
        self.redis = redis.Redis(
            host='localhost',
            port=6379,
            db=0,
            decode_responses=True
        )
        self.stats = CacheStats()
        
    def get(self, query: str) -> Optional[Dict]:
        """Cache'den query sonucunu getirir."""
        cache_key = self._generate_cache_key(query)
        
        try:
            cached_data = self.redis.get(cache_key)
            if cached_data:
                self.stats.record_hit(cache_key)
                return self._deserialize_cache_data(cached_data)
            
            self.stats.record_miss(cache_key)
            return None
            
        except Exception as e:
            self.stats.record_error(cache_key, str(e))
            return None
            
    def set(self, query: str, result: Dict):
        """Query sonucunu cache'e kaydeder."""
        cache_key = self._generate_cache_key(query)
        
        try:
            # Cache size kontrolü
            if self._check_size_limit():
                # Eviction policy uygula
                self._apply_eviction_policy()
                
            # Veriyi serialize et
            cached_data = self._serialize_cache_data(result)
            
            # Cache'e kaydet
            self.redis.setex(
                cache_key,
                self.config.ttl,
                cached_data
            )
            
            self.stats.record_set(cache_key)
            
        except Exception as e:
            self.stats.record_error(cache_key, str(e))
            
    def invalidate(self, pattern: str = None):
        """Cache invalidation yapar."""
        if pattern:
            keys = self.redis.keys(f"*{pattern}*")
            if keys:
                self.redis.delete(*keys)
                self.stats.record_invalidation(pattern, len(keys))
        else:
            self.redis.flushdb()
            self.stats.record_invalidation('all', None)
            
    def _generate_cache_key(self, query: str) -> str:
        """Query için unique cache key oluşturur."""
        # Query'yi normalize et
        normalized_query = self._normalize_query(query)
        
        # Hash oluştur
        return hashlib.md5(normalized_query.encode()).hexdigest()
        
    def _normalize_query(self, query: str) -> str:
        """Query'yi cache key için normalize eder."""
        # Whitespace'leri temizle
        query = ' '.join(query.split())
        
        # Case-insensitive yap
        query = query.upper()
        
        # Literal değerleri parameterize et
        return self._parameterize_literals(query)
        
    def _check_size_limit(self) -> bool:
        """Cache size limitini kontrol eder."""
        current_size = self._get_cache_size()
        return current_size > self.config.max_size
        
    def _apply_eviction_policy(self):
        """Configured eviction policy'yi uygular."""
        if self.config.strategy == 'LRU':
            self._apply_lru_eviction()
        elif self.config.strategy == 'LFU':
            self._apply_lfu_eviction()
        elif self.config.strategy == 'FIFO':
            self._apply_fifo_eviction()