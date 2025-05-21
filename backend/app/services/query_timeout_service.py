"""
Query timeout service for SQL Proxy

This service manages query timeouts based on user roles and server configurations.
It tracks executing queries and automatically terminates them if they exceed their allowed duration.

Last updated: 2025-05-20 07:15:16
Updated by: Teeksss
"""

import logging
import threading
import time
import uuid
from typing import Dict, Tuple, Optional, List, Any
from datetime import datetime, timedelta
import asyncio

from app.core.config import settings

logger = logging.getLogger(__name__)

class QueryTimeoutService:
    """
    Service for managing query timeouts
    
    Tracks executing queries and provides timeout functionality based on user roles.
    """
    
    def __init__(self):
        """Initialize the query timeout service"""
        # Dictionary to track active queries
        self.active_queries = {}
        
        # Dictionary to store query information for lookup
        self.query_info = {}
        
        # Lock for thread safety
        self.lock = threading.RLock()
        
        # Default timeouts by role (in seconds)
        self.default_timeouts = {
            'admin': settings.DEFAULT_TIMEOUT_ADMIN,
            'analyst': settings.DEFAULT_TIMEOUT_ANALYST,
            'powerbi': settings.DEFAULT_TIMEOUT_POWERBI,
            'readonly': settings.DEFAULT_TIMEOUT_READONLY
        }
        
        # Any custom timeouts (populated from database later)
        self.custom_timeouts = {}
        
        # Server-specific timeouts
        self.server_timeouts = {}
        
        # Start cleanup thread
        self.cleanup_thread = threading.Thread(target=self._cleanup_thread, daemon=True)
        self.cleanup_thread.start()
        
        logger.info("Query timeout service initialized")
    
    def register_query(self, query_id: str, username: str, role: str, server_alias: Optional[str] = None) -> Tuple[int, threading.Timer]:
        """
        Register a query for timeout tracking
        
        Args:
            query_id: Unique identifier for the query
            username: Username of the user executing the query
            role: Role of the user
            server_alias: Optional server alias (for server-specific timeouts)
        
        Returns:
            Tuple of (timeout in seconds, timer object)
        """
        with self.lock:
            # Determine timeout based on role and server
            timeout = self._get_timeout(username, role, server_alias)
            
            # Create a timer
            timer = threading.Timer(timeout, self._handle_timeout, args=[query_id, username, timeout])
            timer.daemon = True
            timer.start()
            
            # Store in active queries
            self.active_queries[query_id] = timer
            
            # Store query info for lookup
            self.query_info[query_id] = {
                'username': username,
                'role': role,
                'server_alias': server_alias,
                'start_time': datetime.utcnow(),
                'timeout': timeout
            }
            
            logger.debug(f"Registered query {query_id} for user {username} with timeout {timeout}s")
            
            return timeout, timer
    
    def unregister_query(self, query_id: str) -> bool:
        """
        Unregister a query from timeout tracking (e.g. when it completes)
        
        Args:
            query_id: Unique identifier for the query
            
        Returns:
            True if the query was found and unregistered, False otherwise
        """
        with self.lock:
            if query_id in self.active_queries:
                # Cancel the timer
                timer = self.active_queries[query_id]
                timer.cancel()
                
                # Remove from active queries
                del self.active_queries[query_id]
                
                # Remove from query info (keep it for a while for diagnostics)
                info = self.query_info.get(query_id, {})
                if info:
                    info['end_time'] = datetime.utcnow()
                    duration = (info['end_time'] - info['start_time']).total_seconds()
                    info['duration'] = duration
                    logger.debug(f"Unregistered query {query_id} after {duration:.2f}s")
                
                return True
            
            return False
    
    def extend_timeout(self, query_id: str, additional_seconds: int) -> bool:
        """
        Extend the timeout for a running query
        
        Args:
            query_id: Unique identifier for the query
            additional_seconds: Additional seconds to add to the timeout
            
        Returns:
            True if the query's timeout was extended, False if not found
        """
        with self.lock:
            if query_id not in self.active_queries or query_id not in self.query_info:
                return False
            
            # Cancel the existing timer
            timer = self.active_queries[query_id]
            timer.cancel()
            
            # Get query info
            info = self.query_info[query_id]
            current_time = datetime.utcnow()
            elapsed_time = (current_time - info['start_time']).total_seconds()
            
            # Calculate new timeout (remaining time + additional)
            new_timeout = max(0.1, info['timeout'] - elapsed_time + additional_seconds)
            
            # Create a new timer
            new_timer = threading.Timer(
                new_timeout, 
                self._handle_timeout, 
                args=[query_id, info['username'], info['timeout'] + additional_seconds]
            )
            new_timer.daemon = True
            new_timer.start()
            
            # Update active queries
            self.active_queries[query_id] = new_timer
            
            # Update query info
            info['timeout'] = info['timeout'] + additional_seconds
            
            logger.debug(f"Extended timeout for query {query_id} by {additional_seconds}s, new total: {info['timeout']}s")
            
            return True
    
    def get_active_queries(self) -> List[Dict[str, Any]]:
        """
        Get a list of currently active queries
        
        Returns:
            List of active query information dictionaries
        """
        with self.lock:
            active_list = []
            current_time = datetime.utcnow()
            
            for query_id, info in self.query_info.items():
                if query_id in self.active_queries:
                    elapsed_time = (current_time - info['start_time']).total_seconds()
                    remaining_time = max(0, info['timeout'] - elapsed_time)
                    
                    active_list.append({
                        'query_id': query_id,
                        'username': info['username'],
                        'role': info['role'],
                        'server_alias': info['server_alias'],
                        'start_time': info['start_time'].isoformat(),
                        'elapsed_seconds': round(elapsed_time, 2),
                        'total_timeout': info['timeout'],
                        'remaining_seconds': round(remaining_time, 2)
                    })
            
            return active_list
    
    def get_query_info(self, query_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific query
        
        Args:
            query_id: Unique identifier for the query
            
        Returns:
            Dictionary with query information or None if not found
        """
        with self.lock:
            if query_id not in self.query_info:
                return None
            
            info = self.query_info[query_id].copy()
            
            # Add some calculated fields
            info['is_active'] = query_id in self.active_queries
            
            if info['is_active']:
                current_time = datetime.utcnow()
                elapsed_time = (current_time - info['start_time']).total_seconds()
                info['elapsed_seconds'] = round(elapsed_time, 2)
                info['remaining_seconds'] = round(max(0, info['timeout'] - elapsed_time), 2)
            elif 'end_time' in info:
                info['elapsed_seconds'] = info.get('duration', 0)
                info['remaining_seconds'] = 0
            
            return info
    
    def cancel_query(self, query_id: str) -> bool:
        """
        Cancel a running query manually
        
        Args:
            query_id: Unique identifier for the query
            
        Returns:
            True if the query was found and canceled, False otherwise
        """
        with self.lock:
            if query_id not in self.active_queries:
                return False
            
            # Get the query info for the log
            info = self.query_info.get(query_id, {})
            username = info.get('username', 'unknown')
            
            # Cancel the timer
            timer = self.active_queries[query_id]
            timer.cancel()
            
            # Remove from active queries
            del self.active_queries[query_id]
            
            # Update query info
            if info:
                info['end_time'] = datetime.utcnow()
                info['duration'] = (info['end_time'] - info['start_time']).total_seconds()
                info['canceled'] = True
            
            logger.info(f"Manually canceled query {query_id} for user {username}")
            
            # Here you would actually stop the running query in your database
            # This is application-specific and depends on how your database connector works
            
            return True
    
    def update_timeouts(self, role_timeouts: Dict[str, int], server_timeouts: Dict[str, int], custom_timeouts: Dict[str, int]):
        """
        Update timeout settings
        
        Args:
            role_timeouts: Dictionary mapping roles to timeout values
            server_timeouts: Dictionary mapping server aliases to timeout values
            custom_timeouts: Dictionary mapping usernames to timeout values
        """
        with self.lock:
            # Update role-based timeouts
            for role, timeout in role_timeouts.items():
                if timeout > 0:
                    self.default_timeouts[role] = timeout
            
            # Update server-specific timeouts
            self.server_timeouts = {k: v for k, v in server_timeouts.items() if v > 0}
            
            # Update custom user timeouts
            self.custom_timeouts = {k: v for k, v in custom_timeouts.items() if v > 0}
            
            logger.info("Updated timeout settings")
    
    def _get_timeout(self, username: str, role: str, server_alias: Optional[str] = None) -> int:
        """
        Determine the appropriate timeout value for a query
        
        Args:
            username: Username of the user executing the query
            role: Role of the user
            server_alias: Optional server alias
            
        Returns:
            Timeout value in seconds
        """
        # Check user-specific timeout first
        if username in self.custom_timeouts:
            return self.custom_timeouts[username]
        
        # Check server-specific timeout next
        if server_alias and server_alias in self.server_timeouts:
            return self.server_timeouts[server_alias]
        
        # Fall back to role-based timeout
        if role in self.default_timeouts:
            return self.default_timeouts[role]
        
        # Default timeout if nothing else matches
        return 60  # 1 minute default
    
    def _handle_timeout(self, query_id: str, username: str, timeout: int):
        """
        Handler called when a query times out
        
        Args:
            query_id: Unique identifier for the query
            username: Username of the user executing the query
            timeout: Timeout value that was set (for logging)
        """
        with self.lock:
            if query_id not in self.active_queries:
                return  # Query already completed or was canceled
            
            # Get query info
            info = self.query_info.get(query_id, {})
            server_alias = info.get('server_alias', 'unknown')
            
            # Remove from active queries
            del self.active_queries[query_id]
            
            # Update query info
            if info:
                info['end_time'] = datetime.utcnow()
                info['duration'] = (info['end_time'] - info['start_time']).total_seconds()
                info['timed_out'] = True
            
            logger.warning(f"Query {query_id} for user {username} timed out after {timeout}s on server {server_alias}")
            
            # Here you would actually kill the running query in your database
            # This is application-specific and depends on how your database connector works
            
            # Trigger notification or other actions as needed
            # This would likely be a call to another service
            # self._notify_timeout(query_id, username, timeout, server_alias)
    
    async def _notify_timeout(self, query_id: str, username: str, timeout: int, server_alias: str):
        """
        Send notifications about query timeout
        
        Args:
            query_id: Unique identifier for the query
            username: Username of the user executing the query
            timeout: Timeout value that was set
            server_alias: Target server alias
        """
        try:
            # Import notification service (import inside method to avoid circular imports)
            from app.services.notification_service import notification_service
            
            # Create notification message
            title = f"Query Timeout"
            message = f"Your query timed out after {timeout} seconds. Server: {server_alias}"
            
            # Send notification
            await notification_service.send_user_notification(
                username,
                title,
                message,
                notification_type="timeout"
            )
            
            logger.info(f"Sent timeout notification to user {username} for query {query_id}")
        except Exception as e:
            logger.error(f"Error sending timeout notification: {str(e)}")
    
    def _cleanup_thread(self):
        """Background thread that periodically cleans up inactive query records"""
        while True:
            try:
                time.sleep(300)  # Run every 5 minutes
                
                with self.lock:
                    # Find completed queries that have been in query_info for too long
                    current_time = datetime.utcnow()
                    to_remove = []
                    
                    for query_id, info in self.query_info.items():
                        if query_id not in self.active_queries and 'end_time' in info:
                            # If query has been completed for more than 1 hour, clean it up
                            age = (current_time - info['end_time']).total_seconds()
                            if age > 3600:  # 1 hour
                                to_remove.append(query_id)
                    
                    # Remove old query info
                    for query_id in to_remove:
                        del self.query_info[query_id]
                    
                    if to_remove:
                        logger.debug(f"Cleaned up {len(to_remove)} old query records")
            except Exception as e:
                logger.error(f"Error in timeout cleanup thread: {str(e)}")

# Create a singleton instance
query_timeout_service = QueryTimeoutService()

# Son güncelleme: 2025-05-20 07:15:16
# Güncelleyen: Teeksss