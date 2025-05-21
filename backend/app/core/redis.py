import redis
from app.core.config import settings

def get_redis_client():
    """Get Redis client singleton."""
    redis_client = redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB,
        password=settings.REDIS_PASSWORD,
        decode_responses=True
    )
    return redis_client