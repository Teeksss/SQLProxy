"""
Client Configuration Generator for SQL Proxy

This module provides functions for generating client configuration data
for SDK integration with SQL Proxy.

Last updated: 2025-05-20 11:25:24
Updated by: Teeksss
"""

import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from app.models.server import ServerConfig
from app.models.sdk import SDKConfig
from app.models.user import User
from app.core.config import settings

logger = logging.getLogger(__name__)

def generate_client_config(
    client_id: str,
    servers: List[ServerConfig],
    sdk_config: SDKConfig,
    user: User
) -> Dict[str, Any]:
    """
    Generate client configuration for SDK integration
    
    Args:
        client_id: Client identifier
        servers: List of accessible servers
        sdk_config: SDK configuration
        user: User requesting the configuration
        
    Returns:
        Client configuration data
    """
    # Base configuration
    config = {
        "client_id": client_id,
        "api_version": settings.API_VERSION,
        "generated_at": datetime.utcnow().isoformat(),
        "expires_at": sdk_config.expires_at.isoformat() if sdk_config.expires_at else None,
        "servers": [],
        "settings": {
            "connect_timeout_seconds": settings.CLIENT_CONNECT_TIMEOUT,
            "request_timeout_seconds": settings.CLIENT_REQUEST_TIMEOUT,
            "max_retries": settings.CLIENT_MAX_RETRIES,
            "retry_delay_seconds": settings.CLIENT_RETRY_DELAY,
            "enable_response_validation": True,
            "enable_ssl_verification": True,
            "enable_compression": True,
            "cache_ttl_seconds": settings.CLIENT_CACHE_TTL,
            "max_batch_size": settings.CLIENT_MAX_BATCH_SIZE,
            "logging_level": "INFO"
        },
        "rate_limit": {
            "requests_per_minute": sdk_config.rate_limit,
            "max_concurrent_requests": settings.CLIENT_MAX_CONCURRENT_REQUESTS
        },
        "api": {
            "base_url": settings.API_BASE_URL,
            "query_endpoint": "/v1/query",
            "batch_endpoint": "/v1/batch",
            "status_endpoint": "/v1/status"
        }
    }
    
    # Parse allowed operations
    allowed_operations = json.loads(sdk_config.allowed_operations) if sdk_config.allowed_operations else ["SELECT"]
    
    # Add server configurations
    for server in servers:
        server_config = {
            "server_id": server.id,
            "server_alias": server.alias,
            "description": server.description,
            "server_type": server.server_type,
            "environment": server.environment,
            "features": {
                "read_only": "INSERT" not in allowed_operations and "UPDATE" not in allowed_operations and "DELETE" not in allowed_operations,
                "allowed_operations": allowed_operations,
                "transaction_support": server.server_type in ["mysql", "postgresql", "sqlserver"],
                "batch_support": server.server_type in ["mysql", "postgresql", "sqlserver", "oracle"],
                "prepared_statements": server.server_type in ["mysql", "postgresql", "sqlserver", "oracle"]
            },
            "connection_info": {
                "pool_size": settings.CLIENT_CONNECTION_POOL_SIZE,
                "max_overflow": settings.CLIENT_CONNECTION_MAX_OVERFLOW,
                "pool_recycle": settings.CLIENT_CONNECTION_POOL_RECYCLE
            }
        }
        
        config["servers"].append(server_config)
    
    # Add SDK-specific settings
    sdk_settings = {
        "max_result_size": settings.CLIENT_MAX_RESULT_SIZE,
        "result_streaming_threshold": settings.CLIENT_RESULT_STREAMING_THRESHOLD
    }
    
    config["settings"].update(sdk_settings)
    
    return config

# Son güncelleme: 2025-05-20 11:25:24
# Güncelleyen: Teeksss