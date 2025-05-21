"""
Configuration Manager Service for SQL Proxy

Provides centralized management of dynamic system configurations,
allowing settings to be changed at runtime and persisted to database.

Last updated: 2025-05-20 07:43:54
Updated by: Teeksss
"""

import logging
import json
import copy
from typing import Dict, Any, Optional, List, Set
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.config import SystemConfig
from app.models.server import ServerConfig
from app.core.config import settings

logger = logging.getLogger(__name__)

class ConfigurationManager:
    """
    Service for managing dynamic system configurations
    
    Provides functionality to load, update, and validate system configuration
    parameters that can be changed at runtime.
    """
    
    def __init__(self):
        """Initialize the configuration manager"""
        # In-memory configuration
        self._config = {}
        
        # Last time configurations were loaded from DB
        self._last_load_time = 0
        
        # Default configurations with validation rules
        self._config_schema = {
            # Query execution settings
            "query": {
                "max_execution_time": {
                    "default": 600,  # Maximum execution time in seconds
                    "type": "int",
                    "min": 1,
                    "max": 3600,
                    "description": "Maximum query execution time in seconds"
                },
                "max_results": {
                    "default": 10000,  # Maximum number of results to return
                    "type": "int",
                    "min": 100,
                    "max": 100000,
                    "description": "Maximum number of rows to return in query results"
                },
                "default_limit": {
                    "default": 1000,  # Default LIMIT if not specified
                    "type": "int",
                    "min": 10,
                    "max": 10000,
                    "description": "Default LIMIT to apply to queries if not specified"
                },
                "enforce_where_clause": {
                    "default": True,  # Require WHERE clause for certain operations
                    "type": "bool",
                    "description": "Require WHERE clause for UPDATE and DELETE operations"
                }
            },
            
            # Authentication settings
            "auth": {
                "token_expiry_minutes": {
                    "default": 480,  # 8 hours
                    "type": "int",
                    "min": 5,
                    "max": 1440,  # 24 hours
                    "description": "JWT token expiry time in minutes"
                },
                "max_failed_logins": {
                    "default": 5,  # Maximum failed login attempts
                    "type": "int",
                    "min": 1,
                    "max": 20,
                    "description": "Maximum failed login attempts before account lockout"
                },
                "lockout_minutes": {
                    "default": 30,  # Account lockout time in minutes
                    "type": "int",
                    "min": 1,
                    "max": 1440,  # 24 hours
                    "description": "Account lockout time in minutes after max failed logins"
                },
                "api_key_expiry_days": {
                    "default": 365,  # Default API key expiry in days
                    "type": "int",
                    "min": 1,
                    "max": 3650,  # 10 years
                    "description": "Default API key expiry time in days"
                }
            },
            
            # Rate limiting settings
            "rate_limit": {
                "enabled": {
                    "default": True,
                    "type": "bool",
                    "description": "Enable rate limiting"
                },
                "default_limit": {
                    "default": 60,  # Requests per minute
                    "type": "int",
                    "min": 1,
                    "max": 1000,
                    "description": "Default rate limit (requests per minute)"
                },
                "admin_limit": {
                    "default": 180,  # Requests per minute for admins
                    "type": "int",
                    "min": 1,
                    "max": 1000,
                    "description": "Rate limit for admin users (requests per minute)"
                }
            },
            
            # Notification settings
            "notifications": {
                "email_enabled": {
                    "default": False,
                    "type": "bool",
                    "description": "Enable email notifications"
                },
                "slack_enabled": {
                    "default": False,
                    "type": "bool",
                    "description": "Enable Slack notifications"
                },
                "notify_on_query_approval": {
                    "default": True,
                    "type": "bool",
                    "description": "Notify when a query is approved or rejected"
                },
                "notify_on_whitelist_change": {
                    "default": True,
                    "type": "bool",
                    "description": "Notify when a whitelist entry is added or removed"
                },
                "notify_on_error": {
                    "default": True,
                    "type": "bool",
                    "description": "Notify on system errors"
                },
                "notify_on_timeout": {
                    "default": True,
                    "type": "bool",
                    "description": "Notify when a query times out"
                }
            },
            
            # Data masking settings
            "masking": {
                "enabled": {
                    "default": True,
                    "type": "bool",
                    "description": "Enable data masking"
                },
                "mask_sensitive_logs": {
                    "default": True,
                    "type": "bool",
                    "description": "Apply masking to sensitive data in logs"
                },
                "exempt_roles": {
                    "default": ["admin"],
                    "type": "array",
                    "description": "Roles exempt from data masking"
                }
            },
            
            # Security settings
            "security": {
                "auto_approval_similarity": {
                    "default": 0.9,  # 90% similarity threshold for auto-approval
                    "type": "float",
                    "min": 0.7,
                    "max": 1.0,
                    "description": "Similarity threshold for automatic query approval"
                },
                "query_normalization_level": {
                    "default": "medium",
                    "type": "enum",
                    "options": ["basic", "medium", "high"],
                    "description": "Level of query normalization for similarity comparison"
                },
                "analyze_historical_patterns": {
                    "default": True,
                    "type": "bool",
                    "description": "Analyze historical query patterns for security"
                }
            },
            
            # Cache settings
            "cache": {
                "enabled": {
                    "default": True,
                    "type": "bool",
                    "description": "Enable query result caching"
                },
                "ttl_seconds": {
                    "default": 300,  # 5 minutes
                    "type": "int",
                    "min": 10,
                    "max": 86400,  # 24 hours
                    "description": "Cache time-to-live in seconds"
                },
                "max_size_mb": {
                    "default": 100,  # 100 MB
                    "type": "int",
                    "min": 10,
                    "max": 1024,  # 1 GB
                    "description": "Maximum cache size in MB"
                }
            }
        }
        
        # Initialize with defaults
        self._load_defaults()
        
        logger.info("Configuration manager initialized")
    
    def _load_defaults(self):
        """Load default configuration values"""
        config = {}
        
        for section, params in self._config_schema.items():
            config[section] = {}
            for name, schema in params.items():
                config[section][name] = schema["default"]
        
        self._config = config
    
    def load_config(self, db: Session, force_reload: bool = False) -> Dict[str, Any]:
        """
        Load configuration from database
        
        Args:
            db: Database session
            force_reload: Whether to force a reload even if cache is fresh
            
        Returns:
            Dictionary with current configuration
        """
        # Check if reload is needed
        current_time = int(datetime.utcnow().timestamp())
        if not force_reload and current_time - self._last_load_time < 60:  # Cache for 60 seconds
            return copy.deepcopy(self._config)
        
        try:
            # Get all active configurations
            db_configs = db.query(SystemConfig).filter(
                SystemConfig.is_active == True
            ).all()
            
            # Reset to defaults first
            self._load_defaults()
            
            # Update with values from database
            for config in db_configs:
                try:
                    section = config.section
                    param = config.param
                    value = json.loads(config.value)
                    
                    # Skip if section or param is invalid
                    if section not in self._config or param not in self._config[section]:
                        logger.warning(f"Invalid configuration: {section}.{param}")
                        continue
                    
                    # Validate the value
                    schema = self._config_schema[section][param]
                    if self._validate_value(value, schema):
                        self._config[section][param] = value
                    else:
                        logger.warning(f"Invalid value for {section}.{param}: {value}")
                except Exception as e:
                    logger.error(f"Error processing config {config.section}.{config.param}: {str(e)}")
            
            # Update last load time
            self._last_load_time = current_time
            
            logger.info(f"Loaded {len(db_configs)} configurations from database")
            
            return copy.deepcopy(self._config)
        
        except Exception as e:
            logger.error(f"Error loading configurations: {str(e)}")
            return copy.deepcopy(self._config)
    
    def get_config(self, section: str, param: str, db: Session = None) -> Any:
        """
        Get a specific configuration parameter
        
        Args:
            section: Configuration section
            param: Parameter name
            db: Optional database session (to ensure fresh config)
            
        Returns:
            Parameter value
        """
        # If DB session provided, ensure config is loaded
        if db:
            self.load_config(db)
        
        # Return from in-memory config
        if section in self._config and param in self._config[section]:
            return self._config[section][param]
        
        # Return default if available
        if section in self._config_schema and param in self._config_schema[section]:
            return self._config_schema[section][param]["default"]
        
        # Not found
        logger.warning(f"Config not found: {section}.{param}")
        return None
    
    def update_config(self, db: Session, section: str, param: str, value: Any, updated_by: str) -> bool:
        """
        Update a configuration parameter
        
        Args:
            db: Database session
            section: Configuration section
            param: Parameter name
            value: New value
            updated_by: Username who updated the config
            
        Returns:
            True if update was successful, False otherwise
        """
        try:
            # Validate section and parameter
            if section not in self._config_schema or param not in self._config_schema[section]:
                logger.warning(f"Invalid configuration: {section}.{param}")
                return False
            
            # Validate the value
            schema = self._config_schema[section][param]
            if not self._validate_value(value, schema):
                logger.warning(f"Invalid value for {section}.{param}: {value}")
                return False
            
            # Convert value to JSON string
            value_json = json.dumps(value)
            
            # Check if config already exists
            config = db.query(SystemConfig).filter(
                SystemConfig.section == section,
                SystemConfig.param == param
            ).first()
            
            if config:
                # Update existing config
                config.value = value_json
                config.updated_by = updated_by
                config.updated_at = datetime.utcnow()
                config.is_active = True
            else:
                # Create new config
                config = SystemConfig(
                    section=section,
                    param=param,
                    value=value_json,
                    description=schema.get("description", ""),
                    created_by=updated_by,
                    is_active=True
                )
                db.add(config)
            
            db.commit()
            
            # Update in-memory config
            self._config[section][param] = value
            
            logger.info(f"Updated configuration {section}.{param} to {value} by {updated_by}")
            return True
        
        except Exception as e:
            logger.error(f"Error updating configuration {section}.{param}: {str(e)}")
            db.rollback()
            return False
    
    def reset_to_default(self, db: Session, section: str, param: str, updated_by: str) -> bool:
        """
        Reset a configuration parameter to its default value
        
        Args:
            db: Database session
            section: Configuration section
            param: Parameter name
            updated_by: Username who reset the config
            
        Returns:
            True if reset was successful, False otherwise
        """
        try:
            # Validate section and parameter
            if section not in self._config_schema or param not in self._config_schema[section]:
                logger.warning(f"Invalid configuration: {section}.{param}")
                return False
            
            # Get default value
            default_value = self._config_schema[section][param]["default"]
            
            # Check if config exists
            config = db.query(SystemConfig).filter(
                SystemConfig.section == section,
                SystemConfig.param == param
            ).first()
            
            if config:
                # Update existing config
                config.value = json.dumps(default_value)
                config.updated_by = updated_by
                config.updated_at = datetime.utcnow()
                config.is_active = True
                db.commit()
            
            # Update in-memory config
            self._config[section][param] = default_value
            
            logger.info(f"Reset configuration {section}.{param} to default value by {updated_by}")
            return True
        
        except Exception as e:
            logger.error(f"Error resetting configuration {section}.{param}: {str(e)}")
            db.rollback()
            return False
    
    def get_server_config(self, db: Session, server_alias: str) -> Optional[Dict[str, Any]]:
        """
        Get configuration for a specific server
        
        Args:
            db: Database session
            server_alias: Server alias
            
        Returns:
            Server configuration dictionary or None if server not found
        """
        try:
            # Get server config from database
            server = db.query(ServerConfig).filter(
                ServerConfig.server_alias == server_alias,
                ServerConfig.is_active == True
            ).first()
            
            if not server:
                logger.warning(f"Server not found: {server_alias}")
                return None
            
            # Convert to dictionary
            return {
                "server_alias": server.server_alias,
                "server_name": server.server_name,
                "server_host": server.server_host,
                "server_port": server.server_port,
                "database_name": server.database_name,
                "db_type": server.db_type,
                "allowed_roles": server.allowed_roles,
                "description": server.description,
                "max_connections": server.max_connections,
                "connection_timeout": server.connection_timeout,
                "query_timeout": server.query_timeout,
                "enable_masking": server.enable_masking,
                "is_active": server.is_active
            }
        
        except Exception as e:
            logger.error(f"Error getting server config for {server_alias}: {str(e)}")
            return None
    
    def get_config_schema(self) -> Dict[str, Any]:
        """
        Get configuration schema with metadata
        
        Returns:
            Configuration schema dictionary
        """
        return copy.deepcopy(self._config_schema)
    
    def _validate_value(self, value: Any, schema: Dict[str, Any]) -> bool:
        """
        Validate a configuration value against its schema
        
        Args:
            value: Value to validate
            schema: Schema to validate against
            
        Returns:
            True if value is valid, False otherwise
        """
        try:
            value_type = schema["type"]
            
            if value_type == "int":
                if not isinstance(value, int):
                    return False
                if "min" in schema and value < schema["min"]:
                    return False
                if "max" in schema and value > schema["max"]:
                    return False
            
            elif value_type == "float":
                if not isinstance(value, (int, float)):
                    return False
                if "min" in schema and value < schema["min"]:
                    return False
                if "max" in schema and value > schema["max"]:
                    return False
            
            elif value_type == "bool":
                if not isinstance(value, bool):
                    return False
            
            elif value_type == "string":
                if not isinstance(value, str):
                    return False
                if "min_length" in schema and len(value) < schema["min_length"]:
                    return False
                if "max_length" in schema and len(value) > schema["max_length"]:
                    return False
            
            elif value_type == "enum":
                if not isinstance(value, str):
                    return False
                if "options" in schema and value not in schema["options"]:
                    return False
            
            elif value_type == "array":
                if not isinstance(value, list):
                    return False
            
            elif value_type == "object":
                if not isinstance(value, dict):
                    return False
            
            return True
        
        except Exception as e:
            logger.error(f"Error validating value {value}: {str(e)}")
            return False

# Create a singleton instance
config_manager = ConfigurationManager()

# Son güncelleme: 2025-05-20 07:43:54
# Güncelleyen: Teeksss