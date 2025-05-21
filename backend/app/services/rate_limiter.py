import time
from redis import Redis
from typing import Tuple, Optional
from fastapi import HTTPException, status, Request, Depends
from app.core.config import settings
from app.auth.jwt import get_current_user, TokenData

class RateLimitConfig:
    def __init__(
        self, 
        max_requests: int, 
        window_seconds: int,
        key_prefix: str = "ratelimit"
    ):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.key_prefix = key_prefix

class RateLimiter:
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        
        # Default limit configurations
        self.default_limits = {
            "readonly": RateLimitConfig(max_requests=30, window_seconds=60),
            "analyst": RateLimitConfig(max_requests=100, window_seconds=60),
            "powerbi": RateLimitConfig(max_requests=200, window_seconds=60),
            "admin": RateLimitConfig(max_requests=300, window_seconds=60),
        }
        
        # IP-based rate limit for unauthenticated requests
        self.ip_limit = RateLimitConfig(max_requests=10, window_seconds=60, key_prefix="ip")
        
        # Custom limits for specific users or groups can be loaded from DB
        self.custom_limits = {}  # To be loaded from DB
    
    def _get_rate_limit_key(self, identifier: str, key_type: str = "user") -> str:
        """Generate Redis key for rate limiting."""
        prefix = "ip" if key_type == "ip" else "user"
        return f"ratelimit:{prefix}:{identifier}"
    
    def check_rate_limit(
        self, 
        identifier: str, 
        role: str = "readonly", 
        key_type: str = "user"
    ) -> Tuple[bool, dict]:
        """
        Check if the request exceeds rate limits.
        Returns (is_allowed, limit_info)
        """
        # Determine which limit config to use
        if identifier in self.custom_limits:
            limit_config = self.custom_limits[identifier]
        elif key_type == "ip":
            limit_config = self.ip_limit
        else:
            limit_config = self.default_limits.get(role, self.default_limits["readonly"])
        
        # Get current time
        current_time = int(time.time())
        window_start = current_time - limit_config.window_seconds
        
        redis_key = self._get_rate_limit_key(identifier, key_type)
        
        # Use Redis sorted set to track timestamps of requests
        # Add current request timestamp to the set
        pipeline = self.redis.pipeline()
        pipeline.zadd(redis_key, {str(current_time): current_time})
        
        # Remove timestamps outside the current window
        pipeline.zremrangebyscore(redis_key, 0, window_start)
        
        # Count requests in the current window
        pipeline.zcard(redis_key)
        
        # Set expiry on the key to clean up automatically
        pipeline.expire(redis_key, limit_config.window_seconds * 2)
        
        # Execute pipeline
        _, _, request_count, _ = pipeline.execute()
        
        # Check if limit is exceeded
        is_allowed = request_count <= limit_config.max_requests
        
        # Return limit information for headers
        limit_info = {
            "X-RateLimit-Limit": limit_config.max_requests,
            "X-RateLimit-Remaining": max(0, limit_config.max_requests - request_count),
            "X-RateLimit-Reset": current_time + limit_config.window_seconds
        }
        
        return is_allowed, limit_info

    async def limit_by_user(
        self,
        request: Request,
        user: TokenData = Depends(get_current_user)
    ):
        """Dependency for FastAPI to rate limit by authenticated user."""
        is_allowed, limit_info = self.check_rate_limit(
            identifier=user.username,
            role=user.role,
            key_type="user"
        )
        
        # Add rate limit info to response headers
        request.state.rate_limit_headers = limit_info
        
        if not is_allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded",
                headers=limit_info
            )
        
        return user

    async def limit_by_ip(self, request: Request):
        """Dependency for FastAPI to rate limit by IP address."""
        # Get client IP (considering forwarded headers for proxy setups)
        ip = request.client.host
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            ip = forwarded.split(",")[0].strip()
        
        is_allowed, limit_info = self.check_rate_limit(
            identifier=ip,
            key_type="ip"
        )
        
        # Add rate limit info to response headers
        request.state.rate_limit_headers = limit_info
        
        if not is_allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded",
                headers=limit_info
            )
        
        return ip