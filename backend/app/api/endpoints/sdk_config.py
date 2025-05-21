"""
Client SDK Configuration API endpoints for SQL Proxy

This module provides API endpoints for configuring and retrieving
client SDK settings for SQL Proxy integration.

Last updated: 2025-05-20 11:25:24
Updated by: Teeksss
"""

from fastapi import APIRouter, Depends, HTTPException, Body, Response, Header
from typing import Dict, List, Any, Optional
import json
import logging
import time
import hashlib
from datetime import datetime, timedelta

from app.db.session import get_db
from app.models.server import ServerConfig
from app.models.sdk import SDKConfig
from app.services.config_gen import generate_client_config
from app.auth.jwt import get_current_user, get_current_user_admin
from app.models.user import User
from app.core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/client-config")
async def get_client_config(
    client_id: str,
    format: str = "json",
    environment: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    if_none_match: Optional[str] = Header(None)
) -> Any:
    """
    Get client configuration for SDK integration
    
    Args:
        client_id: Client identifier
        format: Response format (json, yaml, ini)
        environment: Environment name (dev, staging, prod)
        current_user: Current authenticated user
        if_none_match: ETag for conditional request
        
    Returns:
        Client configuration in requested format
    """
    db = next(get_db())
    
    try:
        # Get SDK config for this client
        sdk_config = db.query(SDKConfig).filter(
            SDKConfig.client_id == client_id,
            SDKConfig.is_active == True
        ).first()
        
        if not sdk_config:
            raise HTTPException(status_code=404, detail=f"SDK configuration not found for client ID: {client_id}")
        
        # Check if user has access to this SDK config
        if current_user.role != 'admin' and current_user.id != sdk_config.owner_id:
            raise HTTPException(status_code=403, detail="You don't have permission to access this configuration")
        
        # Get servers accessible to this SDK
        allowed_server_ids = json.loads(sdk_config.allowed_servers) if sdk_config.allowed_servers else []
        
        if allowed_server_ids and allowed_server_ids[0] == "*":
            # All servers allowed
            servers = db.query(ServerConfig).filter(ServerConfig.is_active == True).all()
        else:
            # Only specific servers allowed
            servers = db.query(ServerConfig).filter(
                ServerConfig.id.in_(allowed_server_ids),
                ServerConfig.is_active == True
            ).all()
        
        # Filter by environment if specified
        if environment:
            servers = [s for s in servers if s.environment == environment]
        
        if not servers:
            raise HTTPException(status_code=404, detail="No accessible servers found for this client")
        
        # Generate client configuration
        client_config = generate_client_config(
            client_id=client_id,
            servers=servers,
            sdk_config=sdk_config,
            user=current_user
        )
        
        # Calculate ETag based on configuration
        config_hash = hashlib.md5(json.dumps(client_config).encode()).hexdigest()
        etag = f'"{config_hash}"'
        
        # Check if client already has the latest version
        if if_none_match and if_none_match == etag:
            return Response(status_code=304)
        
        # Format response based on requested format
        if format.lower() == "yaml":
            import yaml
            content = yaml.dump(client_config, default_flow_style=False)
            return Response(content=content, media_type="application/yaml", headers={"ETag": etag})
        
        elif format.lower() == "ini":
            import configparser
            import io
            
            config = configparser.ConfigParser()
            
            # Convert nested dictionary to flat ini format
            def add_config_section(section_name, section_data):
                config[section_name] = {}
                for key, value in section_data.items():
                    if isinstance(value, dict):
                        add_config_section(f"{section_name}.{key}", value)
                    else:
                        config[section_name][key] = str(value)
            
            # Add sections
            config['sqlproxy'] = {'client_id': client_id}
            
            for idx, server in enumerate(client_config['servers']):
                section_name = f"server.{server['server_alias']}"
                add_config_section(section_name, server)
            
            # Write to string
            output = io.StringIO()
            config.write(output)
            content = output.getvalue()
            
            return Response(content=content, media_type="text/plain", headers={"ETag": etag})
        
        else:  # Default to JSON
            return Response(
                content=json.dumps(client_config, indent=2),
                media_type="application/json",
                headers={"ETag": etag}
            )
    
    finally:
        db.close()

@router.post("/client-config")
async def create_client_config(
    config_data: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_user_admin)
) -> Dict[str, Any]:
    """
    Create a new client SDK configuration
    
    Args:
        config_data: SDK configuration data
        current_user: Current authenticated admin user
        
    Returns:
        Created SDK configuration details
    """
    db = next(get_db())
    
    try:
        # Extract required fields
        client_id = config_data.get("client_id")
        name = config_data.get("name")
        
        if not client_id or not name:
            raise HTTPException(status_code=400, detail="Client ID and name are required")
        
        # Check if client ID already exists
        existing = db.query(SDKConfig).filter(SDKConfig.client_id == client_id).first()
        if existing:
            raise HTTPException(status_code=409, detail=f"Client ID already exists: {client_id}")
        
        # Create SDK config
        sdk_config = SDKConfig(
            client_id=client_id,
            name=name,
            description=config_data.get("description"),
            allowed_servers=json.dumps(config_data.get("allowed_servers", [])),
            allowed_operations=json.dumps(config_data.get("allowed_operations", ["SELECT"])),
            rate_limit=config_data.get("rate_limit", 100),
            is_active=config_data.get("is_active", True),
            owner_id=config_data.get("owner_id", current_user.id),
            created_by=current_user.username,
            created_at=datetime.utcnow(),
            api_key=None,  # Will be generated
            expires_at=None
        )
        
        # Generate API key if requested
        if config_data.get("generate_api_key", False):
            expiry_days = config_data.get("api_key_expiry_days", 365)
            api_key = self._generate_api_key(client_id)
            
            sdk_config.api_key = api_key
            sdk_config.expires_at = datetime.utcnow() + timedelta(days=expiry_days)
        
        db.add(sdk_config)
        db.commit()
        
        return {
            "client_id": sdk_config.client_id,
            "name": sdk_config.name,
            "description": sdk_config.description,
            "is_active": sdk_config.is_active,
            "api_key": sdk_config.api_key,
            "expires_at": sdk_config.expires_at.isoformat() if sdk_config.expires_at else None,
            "created_at": sdk_config.created_at.isoformat()
        }
    
    finally:
        db.close()

@router.put("/client-config/{client_id}")
async def update_client_config(
    client_id: str,
    config_data: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_user_admin)
) -> Dict[str, Any]:
    """
    Update an existing client SDK configuration
    
    Args:
        client_id: Client identifier
        config_data: Updated SDK configuration data
        current_user: Current authenticated admin user
        
    Returns:
        Updated SDK configuration details
    """
    db = next(get_db())
    
    try:
        # Get existing SDK config
        sdk_config = db.query(SDKConfig).filter(SDKConfig.client_id == client_id).first()
        
        if not sdk_config:
            raise HTTPException(status_code=404, detail=f"SDK configuration not found: {client_id}")
        
        # Update fields
        if "name" in config_data:
            sdk_config.name = config_data["name"]
        
        if "description" in config_data:
            sdk_config.description = config_data["description"]
        
        if "allowed_servers" in config_data:
            sdk_config.allowed_servers = json.dumps(config_data["allowed_servers"])
        
        if "allowed_operations" in config_data:
            sdk_config.allowed_operations = json.dumps(config_data["allowed_operations"])
        
        if "rate_limit" in config_data:
            sdk_config.rate_limit = config_data["rate_limit"]
        
        if "is_active" in config_data:
            sdk_config.is_active = config_data["is_active"]
        
        if "owner_id" in config_data:
            sdk_config.owner_id = config_data["owner_id"]
        
        # Update timestamp and user
        sdk_config.updated_by = current_user.username
        sdk_config.updated_at = datetime.utcnow()
        
        # Generate new API key if requested
        if config_data.get("regenerate_api_key", False):
            expiry_days = config_data.get("api_key_expiry_days", 365)
            api_key = _generate_api_key(client_id)
            
            sdk_config.api_key = api_key
            sdk_config.expires_at = datetime.utcnow() + timedelta(days=expiry_days)
        
        # Revoke API key if requested
        if config_data.get("revoke_api_key", False):
            sdk_config.api_key = None
            sdk_config.expires_at = None
        
        db.commit()
        
        return {
            "client_id": sdk_config.client_id,
            "name": sdk_config.name,
            "description": sdk_config.description,
            "is_active": sdk_config.is_active,
            "api_key": sdk_config.api_key,
            "expires_at": sdk_config.expires_at.isoformat() if sdk_config.expires_at else None,
            "updated_at": sdk_config.updated_at.isoformat()
        }
    
    finally:
        db.close()

@router.delete("/client-config/{client_id}")
async def delete_client_config(
    client_id: str,
    current_user: User = Depends(get_current_user_admin)
) -> Dict[str, Any]:
    """
    Delete a client SDK configuration
    
    Args:
        client_id: Client identifier
        current_user: Current authenticated admin user
        
    Returns:
        Deletion status
    """
    db = next(get_db())
    
    try:
        # Get existing SDK config
        sdk_config = db.query(SDKConfig).filter(SDKConfig.client_id == client_id).first()
        
        if not sdk_config:
            raise HTTPException(status_code=404, detail=f"SDK configuration not found: {client_id}")
        
        # Delete configuration
        db.delete(sdk_config)
        db.commit()
        
        return {
            "status": "success",
            "message": f"SDK configuration deleted: {client_id}"
        }
    
    finally:
        db.close()

@router.get("/client-configs")
async def list_client_configs(
    current_user: User = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """
    List all client SDK configurations
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        List of SDK configurations
    """
    db = next(get_db())
    
    try:
        # Query configurations
        query = db.query(SDKConfig)
        
        # Filter by owner for non-admin users
        if current_user.role != 'admin':
            query = query.filter(SDKConfig.owner_id == current_user.id)
        
        sdk_configs = query.all()
        
        # Format response
        result = []
        for config in sdk_configs:
            result.append({
                "client_id": config.client_id,
                "name": config.name,
                "description": config.description,
                "is_active": config.is_active,
                "owner_id": config.owner_id,
                "created_at": config.created_at.isoformat() if config.created_at else None,
                "updated_at": config.updated_at.isoformat() if config.updated_at else None,
                "has_api_key": bool(config.api_key)
            })
        
        return result
    
    finally:
        db.close()

@router.post("/regenerate-api-key/{client_id}")
async def regenerate_api_key(
    client_id: str,
    expiry_days: int = Body(365, embed=True),
    current_user: User = Depends(get_current_user_admin)
) -> Dict[str, Any]:
    """
    Regenerate API key for a client SDK configuration
    
    Args:
        client_id: Client identifier
        expiry_days: Number of days until API key expires
        current_user: Current authenticated admin user
        
    Returns:
        New API key details
    """
    db = next(get_db())
    
    try:
        # Get existing SDK config
        sdk_config = db.query(SDKConfig).filter(SDKConfig.client_id == client_id).first()
        
        if not sdk_config:
            raise HTTPException(status_code=404, detail=f"SDK configuration not found: {client_id}")
        
        # Generate new API key
        api_key = _generate_api_key(client_id)
        
        # Update configuration
        sdk_config.api_key = api_key
        sdk_config.expires_at = datetime.utcnow() + timedelta(days=expiry_days)
        sdk_config.updated_by = current_user.username
        sdk_config.updated_at = datetime.utcnow()
        
        db.commit()
        
        return {
            "client_id": client_id,
            "api_key": api_key,
            "expires_at": sdk_config.expires_at.isoformat()
        }
    
    finally:
        db.close()

def _generate_api_key(client_id: str) -> str:
    """
    Generate a secure API key for a client
    
    Args:
        client_id: Client identifier
        
    Returns:
        Generated API key
    """
    # Generate a unique key with timestamp and client ID
    timestamp = int(time.time())
    key_base = f"{client_id}:{timestamp}:{settings.SECRET_KEY}"
    
    # Create hash
    hash_obj = hashlib.sha256(key_base.encode())
    hash_hex = hash_obj.hexdigest()
    
    # Format key as 'sqlp_' + first 32 chars of hash
    api_key = f"sqlp_{hash_hex[:32]}"
    
    return api_key

# Son güncelleme: 2025-05-20 11:25:24
# Güncelleyen: Teeksss