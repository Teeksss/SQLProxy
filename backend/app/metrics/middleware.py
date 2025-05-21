"""
Metrics Middleware for SQL Proxy

This module provides middleware for collecting metrics from HTTP requests.

Last updated: 2025-05-20 11:46:15
Updated by: Teeksss
"""

import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.metrics.metrics_collector import metrics_collector

class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware for collecting metrics from HTTP requests
    
    This middleware collects metrics such as request duration, status code,
    and request method for each HTTP request processed by the application.
    """
    
    def __init__(
        self,
        app: ASGIApp,
    ):
        """
        Initialize metrics middleware
        
        Args:
            app: ASGI application
        """
        super().__init__(app)
    
    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        """
        Process a request and collect metrics
        
        Args:
            request: HTTP request
            call_next: Function to call the next middleware or route handler
            
        Returns:
            HTTP response
        """
        # Get request details
        method = request.method
        path = request.url.path
        
        # Track request start
        metrics_collector.track_api_request_start(method, path)
        
        # Start timer
        start_time = time.time()
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Record metrics
            metrics_collector.observe_api_request(
                method=method,
                path=path,
                duration=duration,
                status=response.status_code
            )
            
            return response
            
        except Exception as e:
            # Calculate duration
            duration = time.time() - start_time
            
            # Record metrics (with error status)
            metrics_collector.observe_api_request(
                method=method,
                path=path,
                duration=duration,
                status=500
            )
            
            # Re-raise exception
            raise
            
        finally:
            # Track request end
            metrics_collector.track_api_request_end(method, path)

# Son güncelleme: 2025-05-20 11:46:15
# Güncelleyen: Teeksss