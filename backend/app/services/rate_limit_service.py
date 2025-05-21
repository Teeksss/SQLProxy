"""
Rate Limiting Service for SQL Proxy

This module provides functionality for managing API rate limits
to prevent abuse and ensure fair usage of external APIs.

Last updated: 2025-05-21 06:32:20
Updated by: Teeksss
"""

import logging
import time
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import asyncio
from contextlib import asynccontextmanager

from fastapi import HTTPException
from redis.asyncio import Redis

from app.core.config import settings

logger = logging.getLogger(__name__)

class RateLimitService:
    """
    Service for managing API rate limits
    
    Provides functionality for tracking API usage, enforcing rate limits,
    and handling backoff strategies for external API calls.
    """
    
    def __init__(self):
        """Initialize rate limit service"""
        self.redis = None
        self.enabled = settings.ENABLE_RATE_LIMITING
        
        # Define rate limits for different APIs
        self.rate_limits = {
            "powerbi": {
                "default": {"requests": 100, "period": 60},  # 100 requests per minute
                "embed": {"requests": 200, "period": 60},    # 200 requests per minute for embed tokens
                "refresh": {"requests": 20, "period": 60},   # 20 refresh requests per minute
                "export": {"requests": 10, "period": 60}     # 10 export requests per minute
            },
            "sql": {
                "default": {"requests": 50, "period": 60},   # 50 SQL queries per minute
                "admin": {"requests": 100, "period": 60}     # 100 admin SQL queries per minute
            }
        }
        
        # Initialize backoff parameters
        self.max_retries = 3
        self.base_delay = 1.0  # seconds
    
    async def setup(self):
        """Set up Redis connection for rate limiting"""
        if not self.enabled:
            logger.info("Rate limiting is disabled")
            return
        
        if settings.REDIS_URL:
            try:
                self.redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)
                logger.info("Connected to Redis for rate limiting")
            except Exception as e:
                logger.error(f"Error connecting to Redis: {e}", exc_info=True)
                self.redis = None
                self.enabled = False
        else:
            logger.warning("Redis URL not configured, rate limiting will use in-memory storage")
            self.redis = None
    
    async def check_rate_limit(
        self, 
        key: str, 
        api: str = "default", 
        operation: str = "default",
        user_id: Optional[int] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if a rate limit has been exceeded
        
        Args:
            key: Rate limit key
            api: API name
            operation: Operation name
            user_id: Optional user ID
            
        Returns:
            Tuple of (is_allowed, limit_info)
        """
        if not self.enabled:
            return True, {"allowed": True, "remaining": 999, "reset": 0}
        
        # Generate a unique key for this rate limit
        rate_key = f"ratelimit:{api}:{operation}:{key}"
        if user_id:
            rate_key += f":{user_id}"
        
        # Get rate limit config
        limit_config = self.rate_limits.get(api, {}).get(operation)
        if not limit_config:
            limit_config = self.rate_limits.get(api, {}).get("default")
        if not limit_config:
            limit_config = {"requests": 100, "period": 60}  # Default fallback
        
        max_requests = limit_config["requests"]
        period = limit_config["period"]
        
        # Check rate limit
        current_time = int(time.time())
        window_start = current_time - (current_time % period)
        window_end = window_start + period
        remaining_time = window_end - current_time
        
        if self.redis:
            # Use Redis for distributed rate limiting
            try:
                # Get current count
                count = await self.redis.get(rate_key)
                count = int(count) if count else 0
                
                if count >= max_requests:
                    return False, {
                        "allowed": False,
                        "remaining": 0,
                        "reset": remaining_time,
                        "limit": max_requests
                    }
                
                # Increment count and set expiry
                count = await self.redis.incr(rate_key)
                await self.redis.expire(rate_key, period)
                
                return True, {
                    "allowed": True,
                    "remaining": max_requests - count,
                    "reset": remaining_time,
                    "limit": max_requests
                }
            except Exception as e:
                logger.error(f"Redis rate limiting error: {e}", exc_info=True)
                return True, {"allowed": True, "remaining": 999, "reset": 0}
        else:
            # Use in-memory rate limiting (not distributed)
            # In a real implementation, we would use a more sophisticated in-memory storage
            # This is simplified for demonstration
            global _in_memory_rate_limits
            
            if not hasattr(self, '_in_memory_rate_limits'):
                self._in_memory_rate_limits = {}
            
            if rate_key not in self._in_memory_rate_limits:
                self._in_memory_rate_limits[rate_key] = {
                    "count": 0,
                    "window_start": window_start
                }
            
            limit_data = self._in_memory_rate_limits[rate_key]
            
            # Reset if window has changed
            if limit_data["window_start"] < window_start:
                limit_data["count"] = 0
                limit_data["window_start"] = window_start
            
            if limit_data["count"] >= max_requests:
                return False, {
                    "allowed": False,
                    "remaining": 0,
                    "reset": remaining_time,
                    "limit": max_requests
                }
            
            limit_data["count"] += 1
            
            return True, {
                "allowed": True,
                "remaining": max_requests - limit_data["count"],
                "reset": remaining_time,
                "limit": max_requests
            }
    
    @asynccontextmanager
    async def rate_limiter(
        self, 
        key: str, 
        api: str = "default", 
        operation: str = "default",
        user_id: Optional[int] = None
    ):
        """
        Context manager for rate limiting
        
        Args:
            key: Rate limit key
            api: API name
            operation: Operation name
            user_id: Optional user ID
            
        Yields:
            Rate limit info
        """
        is_allowed, limit_info = await self.check_rate_limit(key, api, operation, user_id)
        
        if not is_allowed:
            reset_seconds = limit_info.get("reset", 60)
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Try again in {reset_seconds} seconds."
            )
        
        try:
            yield limit_info
        except Exception as e:
            # Log and re-raise the exception
            logger.error(f"Error during rate-limited operation: {e}", exc_info=True)
            raise
    
    async def with_backoff(self, func, *args, **kwargs):
        """
        Execute a function with exponential backoff retry
        
        Args:
            func: Async function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
        """
        max_retries = kwargs.pop('max_retries', self.max_retries)
        base_delay = kwargs.pop('base_delay', self.base_delay)
        
        for retry in range(max_retries + 1):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                # Check if we should retry
                if retry >= max_retries:
                    logger.error(f"Max retries ({max_retries}) exceeded for {func.__name__}", exc_info=True)
                    raise
                
                # Calculate backoff delay with jitter
                import random
                delay = base_delay * (2 ** retry) * (0.5 + random.random() / 2)
                
                logger.warning(
                    f"Retry {retry+1}/{max_retries} for {func.__name__} after error: {str(e)}. "
                    f"Backing off for {delay:.2f} seconds."
                )
                
                await asyncio.sleep(delay)
    
    async def record_api_usage(
        self,
        api: str,
        operation: str,
        user_id: Optional[int] = None,
        success: bool = True,
        response_time: Optional[float] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Record API usage for analytics
        
        Args:
            api: API name
            operation: Operation name
            user_id: Optional user ID
            success: Whether the request was successful
            response_time: Optional response time in seconds
            details: Optional additional details
        """
        if not self.enabled or not self.redis:
            return
        
        try:
            usage_data = {
                "api": api,
                "operation": operation,
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat(),
                "success": success,
                "response_time": response_time
            }
            
            if details:
                usage_data["details"] = details
            
            # Store usage data in Redis
            usage_id = f"api_usage:{int(time.time())}:{api}:{operation}:{user_id or 'anonymous'}"
            await self.redis.set(usage_id, json.dumps(usage_data))
            await self.redis.expire(usage_id, 86400 * 7)  # Keep for 7 days
            
            # Update daily counter
            day_key = f"api_usage_day:{datetime.utcnow().strftime('%Y-%m-%d')}:{api}:{operation}"
            await self.redis.incr(day_key)
            await self.redis.expire(day_key, 86400 * 30)  # Keep for 30 days
            
        except Exception as e:
            logger.error(f"Error recording API usage: {e}", exc_info=True)

# Initialize rate limit service
rate_limit_service = RateLimitService()

# Setup function to be called on startup
async def setup_rate_limit_service():
    await rate_limit_service.setup()

# Son güncelleme: 2025-05-21 06:32:20
# Güncelleyen: Teeksss