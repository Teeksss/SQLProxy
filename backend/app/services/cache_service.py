"""
Cache Service for SQL Proxy

This module provides caching functionality for SQL queries and PowerBI data.

Last updated: 2025-05-21 06:54:19
Updated by: Teeksss
"""

import logging
import pickle
import json
import hashlib
from typing import Dict, Any, Optional, List, Union, Callable
from datetime import datetime, timedelta
import asyncio

import redis.asyncio as redis

from app.core.config import settings

logger = logging.getLogger(__name__)

class CacheService:
    """
    Service for caching data
    
    Provides caching functionality for SQL query results, PowerBI data,
    and other frequently accessed data to improve performance.
    """
    
    def __init__(self):
        """Initialize cache service"""
        self.redis = None
        self.cache_enabled = settings.CACHE_ENABLED if hasattr(settings, 'CACHE_ENABLED') else True
        self.default_ttl = settings.CACHE_DEFAULT_TTL if hasattr(settings, 'CACHE_DEFAULT_TTL') else 3600
        self.connect()
    
    async def connect(self):
        """Connect to Redis cache"""
        if not self.cache_enabled:
            logger.info("Cache is disabled")
            return
        
        try:
            if settings.REDIS_URL:
                self.redis = await redis.from_url(settings.REDIS_URL, decode_responses=False)
                logger.info("Connected to Redis cache")
            else:
                logger.warning("Redis URL not set, cache will not be available")
                self.cache_enabled = False
        except Exception as e:
            logger.error(f"Error connecting to Redis: {e}", exc_info=True)
            self.cache_enabled = False
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get data from cache
        
        Args:
            key: Cache key
            
        Returns:
            Cached data or None if not found
        """
        if not self.cache_enabled or not self.redis:
            return None
        
        try:
            # Add namespace prefix to key
            prefixed_key = f"sqlproxy:{key}"
            
            # Get from cache
            data = await self.redis.get(prefixed_key)
            if data is None:
                return None
            
            # Deserialize
            return pickle.loads(data)
        except Exception as e:
            logger.error(f"Error getting from cache: {e}", exc_info=True)
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set data in cache
        
        Args:
            key: Cache key
            value: Data to cache
            ttl: Time to live in seconds (None for default)
            
        Returns:
            Success status
        """
        if not self.cache_enabled or not self.redis:
            return False
        
        try:
            # Add namespace prefix to key
            prefixed_key = f"sqlproxy:{key}"
            
            # Serialize
            data = pickle.dumps(value)
            
            # Set in cache
            await self.redis.set(
                prefixed_key,
                data,
                ex=(ttl if ttl is not None else self.default_ttl)
            )
            
            return True
        except Exception as e:
            logger.error(f"Error setting in cache: {e}", exc_info=True)
            return False
    
    async def delete(self, key: str) -> bool:
        """
        Delete data from cache
        
        Args:
            key: Cache key
            
        Returns:
            Success status
        """
        if not self.cache_enabled or not self.redis:
            return False
        
        try:
            # Add namespace prefix to key
            prefixed_key = f"sqlproxy:{key}"
            
            # Delete from cache
            await self.redis.delete(prefixed_key)
            
            return True
        except Exception as e:
            logger.error(f"Error deleting from cache: {e}", exc_info=True)
            return False
    
    async def clear_pattern(self, pattern: str) -> bool:
        """
        Clear cache keys matching pattern
        
        Args:
            pattern: Key pattern
            
        Returns:
            Success status
        """
        if not self.cache_enabled or not self.redis:
            return False
        
        try:
            # Add namespace prefix to pattern
            prefixed_pattern = f"sqlproxy:{pattern}"
            
            # Get keys matching pattern
            cursor = b'0'
            deleted_count = 0
            
            while cursor:
                cursor, keys = await self.redis.scan(
                    cursor=cursor,
                    match=prefixed_pattern,
                    count=100
                )
                
                if keys:
                    deleted = await self.redis.delete(*keys)
                    deleted_count += deleted
                
                if cursor == b'0':
                    break
            
            logger.info(f"Cleared {deleted_count} keys matching pattern {pattern}")
            return True
        except Exception as e:
            logger.error(f"Error clearing cache pattern: {e}", exc_info=True)
            return False
    
    async def clear_all(self) -> bool:
        """
        Clear all cache data
        
        Returns:
            Success status
        """
        if not self.cache_enabled or not self.redis:
            return False
        
        try:
            # Clear all keys with sqlproxy prefix
            await self.clear_pattern('*')
            return True
        except Exception as e:
            logger.error(f"Error clearing all cache: {e}", exc_info=True)
            return False
    
    def generate_query_key(
        self,
        sql_text: str,
        server_id: str,
        params: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate cache key for SQL query
        
        Args:
            sql_text: SQL query text
            server_id: Server ID
            params: Optional query parameters
            
        Returns:
            Cache key
        """
        # Create key parts
        key_parts = [
            f"query:{server_id}",
            sql_text
        ]
        
        # Add params if provided
        if params:
            params_str = json.dumps(params, sort_keys=True)
            key_parts.append(params_str)
        
        # Join and hash
        key_string = ":".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def generate_powerbi_key(
        self,
        entity_type: str,
        entity_id: str,
        workspace_id: Optional[str] = None,
        action: Optional[str] = None
    ) -> str:
        """
        Generate cache key for PowerBI data
        
        Args:
            entity_type: Entity type (report, dataset, etc.)
            entity_id: Entity ID
            workspace_id: Optional workspace ID
            action: Optional action
            
        Returns:
            Cache key
        """
        # Create key parts
        key_parts = [
            "powerbi",
            entity_type,
            entity_id
        ]
        
        # Add workspace_id if provided
        if workspace_id:
            key_parts.append(workspace_id)
        
        # Add action if provided
        if action:
            key_parts.append(action)
        
        # Join
        return ":".join(key_parts)
    
    async def cached(
        self,
        key_or_func: Union[str, Callable],
        func: Optional[Callable] = None,
        ttl: Optional[int] = None,
        *args,
        **kwargs
    ) -> Any:
        """
        Get cached data or execute function and cache result
        
        Can be used as a decorator or directly called.
        
        Args:
            key_or_func: Cache key or function
            func: Function to execute if cache miss (for direct call)
            ttl: Optional cache TTL
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Cached data or function result
        """
        if not self.cache_enabled:
            # If caching is disabled, just execute the function
            if callable(key_or_func):
                return await key_or_func(*args, **kwargs)
            elif func:
                return await func(*args, **kwargs)
            return None
        
        # Determine cache key and function
        if callable(key_or_func):
            # Used as decorator
            cache_key = hashlib.md5(
                (key_or_func.__module__ + key_or_func.__name__ + str(args) + str(sorted(kwargs.items()))).encode()
            ).hexdigest()
            func_to_call = key_or_func
        else:
            # Used directly
            cache_key = key_or_func
            func_to_call = func
        
        # Try to get from cache
        cached_data = await self.get(cache_key)
        if cached_data is not None:
            return cached_data
        
        # Execute function
        if func_to_call:
            result = await func_to_call(*args, **kwargs)
            
            # Cache result
            await self.set(cache_key, result, ttl)
            
            return result
        
        return None
    
    async def cache_query_result(
        self,
        sql_text: str,
        server_id: str,
        result: Any,
        params: Optional[Dict[str, Any]] = None,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Cache SQL query result
        
        Args:
            sql_text: SQL query text
            server_id: Server ID
            result: Query result
            params: Optional query parameters
            ttl: Optional cache TTL
            
        Returns:
            Success status
        """
        cache_key = self.generate_query_key(sql_text, server_id, params)
        return await self.set(cache_key, result, ttl)
    
    async def get_cached_query_result(
        self,
        sql_text: str,
        server_id: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Optional[Any]:
        """
        Get cached SQL query result
        
        Args:
            sql_text: SQL query text
            server_id: Server ID
            params: Optional query parameters
            
        Returns:
            Cached query result or None
        """
        cache_key = self.generate_query_key(sql_text, server_id, params)
        return await self.get(cache_key)
    
    async def invalidate_query_cache(
        self,
        server_id: Optional[str] = None
    ) -> bool:
        """
        Invalidate SQL query cache
        
        Args:
            server_id: Optional server ID to invalidate only queries for that server
            
        Returns:
            Success status
        """
        pattern = f"query:{server_id}*" if server_id else "query:*"
        return await self.clear_pattern(pattern)
    
    async def cache_powerbi_data(
        self,
        entity_type: str,
        entity_id: str,
        data: Any,
        workspace_id: Optional[str] = None,
        action: Optional[str] = None,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Cache PowerBI data
        
        Args:
            entity_type: Entity type (report, dataset, etc.)
            entity_id: Entity ID
            data: Data to cache
            workspace_id: Optional workspace ID
            action: Optional action
            ttl: Optional cache TTL
            
        Returns:
            Success status
        """
        cache_key = self.generate_powerbi_key(entity_type, entity_id, workspace_id, action)
        return await self.set(cache_key, data, ttl)
    
    async def get_cached_powerbi_data(
        self,
        entity_type: str,
        entity_id: str,
        workspace_id: Optional[str] = None,
        action: Optional[str] = None
    ) -> Optional[Any]:
        """
        Get cached PowerBI data
        
        Args:
            entity_type: Entity type (report, dataset, etc.)
            entity_id: Entity ID
            workspace_id: Optional workspace ID
            action: Optional action
            
        Returns:
            Cached data or None
        """
        cache_key = self.generate_powerbi_key(entity_type, entity_id, workspace_id, action)
        return await self.get(cache_key)
    
    async def invalidate_powerbi_cache(
        self,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        workspace_id: Optional[str] = None
    ) -> bool:
        """
        Invalidate PowerBI cache
        
        Args:
            entity_type: Optional entity type
            entity_id: Optional entity ID
            workspace_id: Optional workspace ID
            
        Returns:
            Success status
        """
        # Build pattern based on parameters
        pattern_parts = ["powerbi"]
        
        if entity_type:
            pattern_parts.append(entity_type)
            
            if entity_id:
                pattern_parts.append(entity_id)
                
                if workspace_id:
                    pattern_parts.append(workspace_id)
        else:
            pattern_parts.append("*")
        
        pattern = ":".join(pattern_parts)
        if not pattern.endswith("*"):
            pattern += "*"
        
        return await self.clear_pattern(pattern)
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics
        
        Returns:
            Cache statistics
        """
        if not self.cache_enabled or not self.redis:
            return {
                "enabled": False,
                "keys": 0,
                "memory_used": 0,
                "hit_rate": 0
            }
        
        try:
            # Get Redis info
            info = await self.redis.info()
            
            # Count sqlproxy keys
            cursor = b'0'
            key_count = 0
            
            while cursor:
                cursor, keys = await self.redis.scan(
                    cursor=cursor,
                    match="sqlproxy:*",
                    count=100
                )
                
                key_count += len(keys)
                
                if cursor == b'0':
                    break
            
            # Calculate stats
            memory_used = info.get('used_memory_human', 'N/A')
            hit_rate = 0
            hits = int(info.get('keyspace_hits', 0))
            misses = int(info.get('keyspace_misses', 0))
            
            if hits + misses > 0:
                hit_rate = hits / (hits + misses) * 100
            
            return {
                "enabled": True,
                "keys": key_count,
                "memory_used": memory_used,
                "hit_rate": hit_rate,
                "uptime_days": info.get('uptime_in_days', 0)
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}", exc_info=True)
            return {
                "enabled": self.cache_enabled,
                "error": str(e)
            }

# Initialize cache service
cache_service = CacheService()

# Son güncelleme: 2025-05-21 06:54:19
# Güncelleyen: Teeksss