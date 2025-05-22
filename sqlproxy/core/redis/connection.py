"""
Redis connection management
"""
import logging
from typing import Any, Dict, List, Optional, Union

import redis

logger = logging.getLogger(__name__)

class RedisConnection:
    """
    Redis connection manager
    """
    
    def __init__(self, host: str = 'localhost', port: int = 6379, db: int = 0, password: Optional[str] = None):
        """
        Initialize Redis connection
        
        Args:
            host: Redis host
            port: Redis port
            db: Redis database
            password: Redis password
        """
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        
        self.client = redis.Redis(
            host=host,
            port=port,
            db=db,
            password=password,
            decode_responses=True
        )
        self._test_connection()
    
    def _test_connection(self) -> bool:
        """Test Redis connection"""
        try:
            self.client.ping()
            logger.info("Redis connection successful")
            return True
        except redis.RedisError as e:
            logger.error(f"Redis connection failed: {str(e)}")
            raise
    
    def get(self, key: str) -> Any:
        """
        Get value from Redis
        
        Args:
            key: Redis key
            
        Returns:
            Value from Redis
        """
        try:
            return self.client.get(key)
        except redis.RedisError as e:
            logger.error(f"Redis get failed: {str(e)}")
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set value in Redis
        
        Args:
            key: Redis key
            value: Value to set
            ttl: Time to live in seconds
            
        Returns:
            Success or failure
        """
        try:
            return self.client.set(key, value, ex=ttl)
        except redis.RedisError as e:
            logger.error(f"Redis set failed: {str(e)}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        Delete key from Redis
        
        Args:
            key: Redis key
            
        Returns:
            Success or failure
        """
        try:
            return bool(self.client.delete(key))
        except redis.RedisError as e:
            logger.error(f"Redis delete failed: {str(e)}")
            return False
    
    def test_connection(self) -> bool:
        """Public method to test connection"""
        return self._test_connection()