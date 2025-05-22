import redis
from typing import Any, Dict, Optional
import json

class RedisConnection:
    def __init__(self, 
                 host: str = 'localhost',
                 port: int = 6379,
                 db: int = 0,
                 password: Optional[str] = None):
        self.client = redis.Redis(
            host=host,
            port=port,
            db=db,
            password=password,
            decode_responses=True
        )

    def set_value(self, key: str, value: Any, 
                  expire: Optional[int] = None) -> bool:
        """Set key-value pair in Redis"""
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            self.client.set(key, value)
            if expire:
                self.client.expire(key, expire)
            return True
        except Exception:
            return False

    def get_value(self, key: str, 
                  default: Any = None) -> Any:
        """Get value from Redis"""
        try:
            value = self.client.get(key)
            if value is None:
                return default
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        except Exception:
            return default

    def delete_key(self, key: str) -> bool:
        """Delete key from Redis"""
        return bool(self.client.delete(key))

    def test_connection(self) -> bool:
        """Test Redis connection"""
        try:
            return bool(self.client.ping())
        except Exception:
            return False