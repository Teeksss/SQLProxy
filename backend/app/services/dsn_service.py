"""
DSN (Data Source Name) Service for SQL Proxy

This module provides functionality for creating and managing DSN
configurations for PowerBI and other data connectors.

Last updated: 2025-05-21 06:45:04
Updated by: Teeksss
"""

import logging
import os
import json
from typing import Dict, List, Any, Optional
from pathlib import Path
import re
import base64

from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException

from app.db.session import get_db
from app.models.user import User
from app.models.server import Server
from app.core.config import settings
from app.services.security_service import security_service

logger = logging.getLogger(__name__)

class DSNService:
    """
    Service for generating and managing DSN configurations
    
    Provides functionality for creating, updating, and managing Data Source
    Name (DSN) configurations for PowerBI and other database connectors.
    """
    
    def __init__(self):
        """Initialize DSN service"""
        self.dsn_template_dir = Path(settings.DSN_TEMPLATE_DIR) if hasattr(settings, 'DSN_TEMPLATE_DIR') else Path("./dsn_templates")
        self.dsn_output_dir = Path(settings.DSN_OUTPUT_DIR) if hasattr(settings, 'DSN_OUTPUT_DIR') else Path("./dsn_output")
        
        # Create directories if they don't exist
        if not self.dsn_template_dir.exists():
            self.dsn_template_dir.mkdir(parents=True, exist_ok=True)
        
        if not self.dsn_output_dir.exists():
            self.dsn_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Default templates for common database types
        self.default_templates = {
            "postgresql": {
                "template": "[ODBC]\nDriver={PostgreSQL Unicode}\nServer=${server}\nPort=${port}\nDatabase=${database}\nUID=${username}\nPWD=${password}\n",
                "file_extension": "dsn"
            },
            "mysql": {
                "template": "[ODBC]\nDriver={MySQL ODBC 8.0 Unicode Driver}\nServer=${server}\nPort=${port}\nDatabase=${database}\nUID=${username}\nPWD=${password}\n",
                "file_extension": "dsn"
            },
            "sqlserver": {
                "template": "[ODBC]\nDriver={ODBC Driver 17 for SQL Server}\nServer=${server},${port}\nDatabase=${database}\nUID=${username}\nPWD=${password}\nTrustServerCertificate=yes\n",
                "file_extension": "dsn"
            },
            "oracle": {
                "template": "[ODBC]\nDriver={Oracle in OraClient19Home1}\nDBQ=${server}:${port}/${service_name}\nUID=${username}\nPWD=${password}\n",
                "file_extension": "dsn"
            },
            "powerbi_odbc": {
                "template": "DSN=${dsn_name}\nDriver={${driver}}\nServer=${server}\nPort=${port}\nDatabase=${database}\nUID=${username}\nPWD=${password}\n${additional_params}",
                "file_extension": "pbids"
            },
            "powerbi_direct": {
                "template": JSON.stringify({
                    "version": "0.1",
                    "connections": [
                        {
                            "details": {
                                "protocol": "sqlserver",
                                "address": {
                                    "server": "${server}",
                                    "database": "${database}"
                                },
                                "authentication": {
                                    "username": "${username}",
                                    "password": "${password}"
                                },
                                "options": {
                                    "port": "${port}"
                                }
                            }
                        }
                    ]
                }, null, 2),
                "file_extension": "pbids"
            }
        }
    
    async def get_dsn_templates(self) -> Dict[str, Any]:
        """
        Get available DSN templates
        
        Returns:
            Dictionary of available templates
        """
        try:
            templates = self.default_templates.copy()
            
            # Add custom templates from template directory
            for template_file in self.dsn_template_dir.glob("*.json"):
                try:
                    with open(template_file, "r") as f:
                        template_data = json.load(f)
                    
                    templates[template_file.stem] = template_data
                except Exception as e:
                    logger.error(f"Error loading template {template_file}: {e}", exc_info=True)
            
            return templates
        except Exception as e:
            logger.error(f"Error getting DSN templates: {e}", exc_info=True)
            raise
    
    async def generate_dsn(
        self,
        template_id: str,
        server_id: Optional[str] = None,
        server_details: Optional[Dict[str, Any]] = None,
        dsn_name: Optional[str] = None,
        additional_params: Optional[Dict[str, Any]] = None,
        user_id: Optional[int] = None,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """
        Generate a DSN configuration file
        
        Args:
            template_id: Template identifier
            server_id: Optional server ID to use server details
            server_details: Optional manual server details
            dsn_name: Optional DSN name
            additional_params: Optional additional parameters
            user_id: Optional user ID for user-specific DSN
            db: Optional database session
            
        Returns:
            DSN generation result with file path and download URL
        """
        try:
            # Get templates
            templates = await self.get_dsn_templates()
            
            if template_id not in templates:
                raise ValueError(f"DSN template '{template_id}' not found")
            
            template = templates[template_id]
            
            # Get server details if server_id is provided
            if server_id and db:
                server = db.query(Server).filter(Server.id == server_id).first()
                if not server:
                    raise ValueError(f"Server with ID {server_id} not found")
                
                # Decrypt password if encrypted
                password = server.password
                if server.is_encrypted and password:
                    password = security_service.decrypt(password)
                
                server_details = {
                    "server": server.host,
                    "port": server.port,
                    "database": server.database,
                    "username": server.username,
                    "password": password,
                    "service_name": server.service_name,
                    "driver": f"SQL Server" if server.db_type == "sqlserver" else server.db_type.capitalize()
                }
            
            if not server_details:
                raise ValueError("Either server_id or server_details must be provided")
            
            # Generate DSN name if not provided
            if not dsn_name:
                dsn_name = f"{server_details['database']}_{template_id}_dsn"
            
            # Normalize DSN name
            dsn_name = re.sub(r'[^a-zA-Z0-9_]', '_', dsn_name)
            
            # Prepare template parameters
            params = {**server_details}
            
            # Add additional parameters
            additional_str = ""
            if additional_params:
                for key, value in additional_params.items():
                    if key not in params:
                        params[key] = value
                    
                    # Build additional parameters string for ODBC
                    additional_str += f"{key}={value}\n"
            
            params["dsn_name"] = dsn_name
            params["additional_params"] = additional_str.strip()
            
            # Apply template parameters
            content = template["template"]
            for key, value in params.items():
                content = content.replace(f"${{{key}}}", str(value))
            
            # Generate output file path
            file_extension = template.get("file_extension", "dsn")
            output_filename = f"{dsn_name}.{file_extension}"
            
            # Add user_id prefix for user-specific DSN
            if user_id:
                output_filename = f"user_{user_id}_{output_filename}"
            
            output_path = self.dsn_output_dir / output_filename
            
            # Write DSN file
            with open(output_path, "w") as f:
                f.write(content)
            
            # Generate download URL
            download_url = f"/api/dsn/download/{output_filename}"
            
            # Create result
            result = {
                "dsn_name": dsn_name,
                "template_id": template_id,
                "file_path": str(output_path),
                "file_name": output_filename,
                "download_url": download_url,
                "content_preview": content[:200] + ("..." if len(content) > 200 else "")
            }
            
            # Store DSN in user's settings if user_id provided
            if user_id and db:
                user = db.query(User).filter(User.id == user_id).first()
                if user:
                    if not user.settings:
                        user.settings = {}
                    
                    if "dsn_configs" not in user.settings:
                        user.settings["dsn_configs"] = []
                    
                    # Add to user's DSN configs
                    dsn_info = {
                        "dsn_name": dsn_name,
                        "template_id": template_id,
                        "file_name": output_filename,
                        "server_id": server_id,
                        "created_at": datetime.datetime.utcnow().isoformat()
                    }
                    
                    user.settings["dsn_configs"].append(dsn_info)
                    db.commit()
            
            return result
        except ValueError as e:
            logger.error(f"Value error generating DSN: {e}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Error generating DSN: {e}", exc_info=True)
            raise
    
    async def get_user_dsn_configs(
        self,
        user_id: int,
        db: Session
    ) -> List[Dict[str, Any]]:
        """
        Get DSN configurations for a user
        
        Args:
            user_id: User ID
            db: Database session
            
        Returns:
            List of user's DSN configurations
        """
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError(f"User with ID {user_id} not found")
            
            if not user.settings or "dsn_configs" not in user.settings:
                return []
            
            # Get DSN configs and add download URLs
            dsn_configs = user.settings["dsn_configs"]
            for config in dsn_configs:
                if "file_name" in config:
                    config["download_url"] = f"/api/dsn/download/{config['file_name']}"
            
            return dsn_configs
        except ValueError as e:
            logger.error(f"Value error getting user DSN configs: {e}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Error getting user DSN configs: {e}", exc_info=True)
            raise
    
    async def delete_user_dsn_config(
        self,
        user_id: int,
        dsn_name: str,
        db: Session
    ) -> bool:
        """
        Delete a DSN configuration for a user
        
        Args:
            user_id: User ID
            dsn_name: DSN name
            db: Database session
            
        Returns:
            Success status
        """
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError(f"User with ID {user_id} not found")
            
            if not user.settings or "dsn_configs" not in user.settings:
                return False
            
            # Find and remove DSN config
            dsn_configs = user.settings["dsn_configs"]
            original_len = len(dsn_configs)
            
            user.settings["dsn_configs"] = [
                config for config in dsn_configs
                if config.get("dsn_name") != dsn_name
            ]
            
            # Check if any config was removed
            if len(user.settings["dsn_configs"]) < original_len:
                db.commit()
                
                # Try to remove DSN file
                try:
                    file_name = f"user_{user_id}_{dsn_name}.dsn"
                    file_path = self.dsn_output_dir / file_name
                    if file_path.exists():
                        os.remove(file_path)
                except:
                    pass
                
                return True
            
            return False
        except ValueError as e:
            logger.error(f"Value error deleting user DSN config: {e}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Error deleting user DSN config: {e}", exc_info=True)
            raise
    
    async def generate_powerbi_connection_string(
        self,
        server_id: str,
        db: Session
    ) -> Dict[str, Any]:
        """
        Generate a PowerBI connection string for a server
        
        Args:
            server_id: Server ID
            db: Database session
            
        Returns:
            Connection string details
        """
        try:
            # Get server details
            server = db.query(Server).filter(Server.id == server_id).first()
            if not server:
                raise ValueError(f"Server with ID {server_id} not found")
            
            # Generate basic connection string based on server type
            if server.db_type == "sqlserver":
                conn_string = f"Server={server.host},{server.port};Database={server.database};User Id={server.username};Password=YOUR_PASSWORD_HERE;"
            elif server.db_type == "postgresql":
                conn_string = f"Server={server.host};Port={server.port};Database={server.database};User Id={server.username};Password=YOUR_PASSWORD_HERE;"
            elif server.db_type == "mysql":
                conn_string = f"Server={server.host};Port={server.port};Database={server.database};Uid={server.username};Pwd=YOUR_PASSWORD_HERE;"
            elif server.db_type == "oracle":
                conn_string = f"Data Source={server.host}:{server.port}/{server.service_name};User Id={server.username};Password=YOUR_PASSWORD_HERE;"
            else:
                conn_string = f"Server={server.host};Port={server.port};Database={server.database};User={server.username};Password=YOUR_PASSWORD_HERE;"
            
            # Generate connection details for PowerBI direct connection
            connection_details = {
                "server": server.host,
                "port": server.port,
                "database": server.database,
                "username": server.username,
                "connection_string": conn_string,
                "server_type": server.db_type,
                "server_name": server.alias or server.host
            }
            
            # Generate a base64 encoded connection string for direct import
            pbids_content = {
                "version": "0.1",
                "connections": [
                    {
                        "details": {
                            "protocol": server.db_type,
                            "address": {
                                "server": server.host,
                                "database": server.database
                            },
                            "authentication": {
                                "username": server.username,
                                "password": "YOUR_PASSWORD_HERE"
                            },
                            "options": {
                                "port": server.port
                            }
                        }
                    }
                ]
            }
            
            pbids_base64 = base64.b64encode(json.dumps(pbids_content).encode()).decode()
            connection_details["pbids_base64"] = pbids_base64
            
            return connection_details
        except ValueError as e:
            logger.error(f"Value error generating PowerBI connection string: {e}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Error generating PowerBI connection string: {e}", exc_info=True)
            raise

# Initialize DSN service
dsn_service = DSNService()

# Son güncelleme: 2025-05-21 06:45:04
# Güncelleyen: Teeksss