from pydantic import BaseSettings
from typing import Optional

class RedisConfig(BaseSettings):
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    REDIS_SSL: bool = False
    REDIS_TIMEOUT: int = 5
    REDIS_RETRY_COUNT: int = 3
    REDIS_RETRY_DELAY: int = 1
    
    class Config:
        env_prefix = "REDIS_"
        
class RedisConnection:
    def __init__(self, config: RedisConfig):
        self.config = config
        self._client = None
        
    async def get_client(self):
        """Redis client'ı döndürür veya oluşturur"""
        if self._client is None:
            import redis
            
            self._client = redis.Redis(
                host=self.config.REDIS_HOST,
                port=self.config.REDIS_PORT,
                db=self.config.REDIS_DB,
                password=self.config.REDIS_PASSWORD,
                ssl=self.config.REDIS_SSL,
                socket_timeout=self.config.REDIS_TIMEOUT,
                retry_on_timeout=True,
                decode_responses=True
            )
            
        return self._client
        
    async def health_check(self):
        """Redis sağlık kontrolü yapar"""
        client = await self.get_client()
        try:
            return client.ping()
        except Exception as e:
            return False