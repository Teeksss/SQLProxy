from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool
import redis

class ConnectionPool:
    def __init__(self):
        self.pools = {}
        self.redis_client = redis.Redis(host='localhost', port=6379, db=0)
        
    def get_connection(self, db_name: str):
        if db_name not in self.pools:
            engine = create_engine(
                self._get_connection_string(db_name),
                poolclass=QueuePool,
                pool_size=5,
                max_overflow=10
            )
            self.pools[db_name] = engine
            
        return self.pools[db_name]
        
    def cache_query(self, query: str, result: dict, expire_time: int = 300):
        self.redis_client.setex(
            self._generate_cache_key(query),
            expire_time,
            str(result)
        )