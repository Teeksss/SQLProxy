"""
Rate Limiter Middleware for SQL Proxy

This module provides rate limiting functionality to protect API endpoints
from abuse or excessive usage.

Last updated: 2025-05-21 07:11:02
Updated by: Teeksss
"""

import time
from typing import Dict, Any, Optional, List, Tuple, Callable
import redis
import json
from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.config import settings

class RateLimiter(BaseHTTPMiddleware):
    """
    Rate limiter middleware for limiting API request rates
    
    Features:
    - Different rate limits per endpoint or endpoint groups
    - User-based and IP-based rate limiting
    - Redis-based storage for distributed setups
    - Configurable rate limit windows and quotas
    """
    
    def __init__(
        self,
        app: ASGIApp,
        redis_url: Optional[str] = None,
        default_limit: int = 100,
        default_window: int = 60,  # 1 minute
        endpoint_limits: Optional[Dict[str, Tuple[int, int]]] = None
    ):
        """
        Initialize rate limiter middleware
        
        Args:
            app: ASGI application
            redis_url: Optional Redis URL (falls back to memory if None)
            default_limit: Default request limit per window
            default_window: Default time window in seconds
            endpoint_limits: Optional custom limits per endpoint pattern {pattern: (limit, window)}
        """
        super().__init__(app)
        self.redis_url = redis_url or settings.REDIS_URL if hasattr(settings, 'REDIS_URL') else None
        self.default_limit = default_limit
        self.default_window = default_window
        self.endpoint_limits = endpoint_limits or {}
        
        # Connect to Redis if available
        self.redis = None
        if self.redis_url:
            try:
                self.redis = redis.from_url(self.redis_url)
                self.redis.ping()  # Test connection
            except Exception as e:
                print(f"Error connecting to Redis for rate limiting: {e}")
                self.redis = None
        
        # Fallback to memory storage if Redis not available
        self.memory_storage = {}
        
        # Whitelist certain paths
        self.whitelist = [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
            "/metrics"
        ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process each request through rate limiting
        
        Args:
            request: HTTP request
            call_next: Next middleware or endpoint handler
            
        Returns:
            HTTP response
        """
        # Skip rate limiting for whitelisted paths
        path = request.url.path
        if any(path.startswith(wp) for wp in self.whitelist):
            return await call_next(request)
        
        # Get rate limit key (user ID or IP)
        key = await self._get_rate_limit_key(request)
        
        # Get endpoint-specific limit
        limit, window = self._get_endpoint_limits(path)
        
        # Check rate limit
        allowed, current, reset_time = await self._check_rate_limit(key, path, limit, window)
        
        if not allowed:
            # Return rate limit exceeded response
            return self._create_rate_limit_response(current, limit, reset_time)
        
        # Process the request
        response = await call_next(request)
        
        # Add rate limit headers
        remaining = max(0, limit - current)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_time)
        
        return response
    
    async def _get_rate_limit_key(self, request: Request) -> str:
        """
        Get rate limit key for a request
        
        Args:
            request: HTTP request
            
        Returns:
            Rate limit key (user ID or IP)
        """
        # Try to get user from request state (set by auth middleware)
        user = request.state.user if hasattr(request.state, "user") else None
        
        if user and hasattr(user, "id"):
            # Use user ID if authenticated
            return f"ratelimit:user:{user.id}"
        else:
            # Fall back to client IP
            client_ip = request.client.host if request.client else "unknown"
            return f"ratelimit:ip:{client_ip}"
    
    def _get_endpoint_limits(self, path: str) -> Tuple[int, int]:
        """
        Get rate limit configuration for an endpoint
        
        Args:
            path: Request path
            
        Returns:
            Limit and window tuple
        """
        # Check for exact path match
        if path in self.endpoint_limits:
            return self.endpoint_limits[path]
        
        # Check for pattern matching
        for pattern, limits in self.endpoint_limits.items():
            if pattern.endswith('*') and path.startswith(pattern[:-1]):
                return limits
        
        # Return default limits
        return self.default_limit, self.default_window
    
    async def _check_rate_limit(
        self,
        key: str,
        path: str,
        limit: int,
        window: int
    ) -> Tuple[bool, int, int]:
        """
        Check if a request is within rate limits
        
        Args:
            key: Rate limit key
            path: Request path
            limit: Request limit
            window: Time window in seconds
            
        Returns:
            Tuple of (allowed, current count, reset time)
        """
        now = int(time.time())
        window_key = f"{key}:{path}:{now // window}"
        reset_time = (now // window + 1) * window
        
        if self.redis:
            # Use Redis for distributed rate limiting
            current = self.redis.incr(window_key)
            
            # Set expiration if new key
            if current == 1:
                self.redis.expire(window_key, window)
            
            allowed = current <= limit
        else:
            # Use memory storage as fallback
            if window_key not in self.memory_storage:
                self.memory_storage[window_key] = 1
                
                # Clean up old entries
                for old_key in list(self.memory_storage.keys()):
                    if old_key.split(':')[-1].isdigit() and int(old_key.split(':')[-1]) < now // window:
                        del self.memory_storage[old_key]
            else:
                self.memory_storage[window_key] += 1
            
            current = self.memory_storage[window_key]
            allowed = current <= limit
        
        return allowed, current, reset_time
    
    def _create_rate_limit_response(
        self,
        current: int,
        limit: int,
        reset_time: int
    ) -> Response:
        """
        Create rate limit exceeded response
        
        Args:
            current: Current request count
            limit: Request limit
            reset_time: Reset time timestamp
            
        Returns:
            Rate limit exceeded response
        """
        content = {
            "detail": "Rate limit exceeded",
            "limit": limit,
            "current": current,
            "reset": reset_time
        }
        
        response = Response(
            content=json.dumps(content),
            status_code=429,
            media_type="application/json"
        )
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = "0"
        response.headers["X-RateLimit-Reset"] = str(reset_time)
        response.headers["Retry-After"] = str(reset_time - int(time.time()))
        
        return response

# Son güncelleme: 2025-05-21 07:11:02
# Güncelleyen: Teeksss