from typing import Dict, Optional
import redis
from redis.cluster import RedisCluster
from redis.exceptions import RedisError
import json
import zlib

class DistributedCache:
    def __init__(self, nodes: List[Dict], replica_factor: int = 2):
        self.cluster = RedisCluster(
            startup_nodes=nodes,
            decode_responses=True,
            replica=replica_factor
        )
        self.compression_threshold = 1024  # 1KB
        
    def get(self, key: str) -> Optional[Dict]:
        """Distributed cache'den veri getirir."""
        try:
            data = self.cluster.get(key)
            if not data:
                return None
                
            # Compression kontrolü
            if self._is_compressed(data):
                data = self._decompress(data)
                
            return json.loads(data)
            
        except RedisError as e:
            self._handle_redis_error(e)
            return None
            
    def set(self, key: str, value: Dict, 
            ttl: int = None, 
            consistency: str = 'strong') -> bool:
        """Distributed cache'e veri kaydeder."""
        try:
            # Veriyi serialize et
            data = json.dumps(value)
            
            # Büyük veriyi compress et
            if len(data) > self.compression_threshold:
                data = self._compress(data)
                
            # Consistency level'a göre kaydet
            if consistency == 'strong':
                return self._set_strong_consistency(key, data, ttl)
            else:
                return self._set_eventual_consistency(key, data, ttl)
                
        except RedisError as e:
            self._handle_redis_error(e)
            return False
            
    def invalidate_pattern(self, pattern: str) -> int:
        """Pattern'e uyan tüm keyleri invalidate eder."""
        try:
            keys = self.cluster.keys(pattern)
            if keys:
                return self.cluster.delete(*keys)
            return 0
            
        except RedisError as e:
            self._handle_redis_error(e)
            return 0
            
    def _set_strong_consistency(self, key: str, 
                              data: str, 
                              ttl: int = None) -> bool:
        """Strong consistency ile veri kaydeder."""
        # Transaction başlat
        with self.cluster.pipeline() as pipe:
            try:
                # Watch key
                pipe.watch(key)
                
                # Multi/exec block
                pipe.multi()
                if ttl:
                    pipe.setex(key, ttl, data)
                else:
                    pipe.set(key, data)
                    
                pipe.execute()
                return True
                
            except redis.WatchError:
                # Key değişmiş, retry mekanizması
                return self._retry_set(key, data, ttl)