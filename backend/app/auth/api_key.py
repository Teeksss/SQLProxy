"""
API key authentication for SQL Proxy

Provides functionality for creating, validating and managing API keys
for API access without user credentials.

Last updated: 2025-05-20 07:43:54
Updated by: Teeksss
"""

import logging
import secrets
import uuid
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict, Any
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.models.api_key import ApiKey
from app.core.config import settings

logger = logging.getLogger(__name__)

class ApiKeyData(BaseModel):
    """
    Validated API key data
    
    Fields:
        key_id: The ID of the API key
        name: Name of the API key
        username: Username associated with the API key
        role: Role assigned to the API key
    """
    key_id: str
    name: str
    username: str
    role: str

def generate_api_key() -> Tuple[str, str]:
    """
    Generate a new API key
    
    Returns:
        Tuple containing (api_key, key_id)
    """
    # Generate a random key with high entropy
    raw_key = secrets.token_hex(32)
    
    # Generate a unique ID for the key
    key_id = str(uuid.uuid4())
    
    # Combine for the full API key (ID:Key format)
    api_key = f"{key_id}:{raw_key}"
    
    return api_key, key_id

def hash_api_key(api_key: str) -> str:
    """
    Hash an API key for secure storage
    
    Args:
        api_key: The API key to hash
        
    Returns:
        Hashed API key
    """
    # Use a secure hashing algorithm (SHA-256)
    return hashlib.sha256(api_key.encode()).hexdigest()

def parse_api_key(api_key: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Parse an API key into its components
    
    Args:
        api_key: The API key to parse (format: "key_id:key")
        
    Returns:
        Tuple containing (key_id, key) or (None, None) if invalid format
    """
    parts = api_key.split(':', 1)
    if len(parts) != 2:
        return None, None
    
    key_id, key = parts
    return key_id, key

def verify_api_key(api_key: str, db: Session) -> Optional[ApiKeyData]:
    """
    Verify an API key and return its associated data
    
    Args:
        api_key: The API key to verify
        db: Database session
        
    Returns:
        ApiKeyData if valid, None otherwise
    """
    try:
        # Parse the API key
        key_id, key = parse_api_key(api_key)
        if not key_id or not key:
            logger.warning("Invalid API key format")
            return None
        
        # Recreate the full key for hashing
        full_key = f"{key_id}:{key}"
        key_hash = hash_api_key(full_key)
        
        # Look up the key in the database
        db_key = db.query(ApiKey).filter(
            ApiKey.key_id == key_id,
            ApiKey.key_hash == key_hash,
            ApiKey.is_active == True,
            ApiKey.expires_at > datetime.utcnow()
        ).first()
        
        if not db_key:
            logger.warning(f"API key not found or inactive: {key_id}")
            return None
        
        # Update last used timestamp
        db_key.last_used_at = datetime.utcnow()
        db_key.use_count += 1
        db.commit()
        
        # Return API key data
        return ApiKeyData(
            key_id=db_key.key_id,
            name=db_key.name,
            username=db_key.created_by,
            role=db_key.role
        )
        
    except Exception as e:
        logger.error(f"Error verifying API key: {str(e)}")
        return None

def store_api_key(
    db: Session,
    key_id: str,
    name: str,
    role: str,
    created_by: str,
    description: str = "",
    expires_in_days: int = 365
) -> ApiKey:
    """
    Store an API key in the database
    
    Args:
        db: Database session
        key_id: ID of the API key
        name: Name of the API key
        role: Role assigned to the API key
        created_by: Username who created the key
        description: Description of the key
        expires_in_days: Number of days until the key expires
        
    Returns:
        ApiKey database object
    """
    # Calculate expiration date
    expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
    
    # We store the key_id and key_hash, but not the actual key
    # The actual key is returned to the user and never stored
    api_key_db = ApiKey(
        key_id=key_id,
        name=name,
        description=description,
        role=role,
        created_by=created_by,
        expires_at=expires_at,
        is_active=True
    )
    
    db.add(api_key_db)
    db.commit()
    db.refresh(api_key_db)
    
    return api_key_db

def revoke_api_key(db: Session, key_id: str, revoked_by: str) -> bool:
    """
    Revoke an API key
    
    Args:
        db: Database session
        key_id: ID of the API key to revoke
        revoked_by: Username who revoked the key
        
    Returns:
        True if the key was successfully revoked, False otherwise
    """
    try:
        # Find the API key
        api_key = db.query(ApiKey).filter(
            ApiKey.key_id == key_id,
            ApiKey.is_active == True
        ).first()
        
        if not api_key:
            logger.warning(f"API key not found or already inactive: {key_id}")
            return False
        
        # Revoke the key
        api_key.is_active = False
        api_key.revoked_at = datetime.utcnow()
        api_key.revoked_by = revoked_by
        
        db.commit()
        
        logger.info(f"API key {key_id} revoked by {revoked_by}")
        return True
        
    except Exception as e:
        logger.error(f"Error revoking API key: {str(e)}")
        db.rollback()
        return False

def refresh_api_key(
    db: Session,
    key_id: str,
    refreshed_by: str,
    expires_in_days: int = 365
) -> Optional[Tuple[str, ApiKey]]:
    """
    Refresh an API key with a new expiration date
    
    Args:
        db: Database session
        key_id: ID of the API key to refresh
        refreshed_by: Username who refreshed the key
        expires_in_days: Number of days until the new key expires
        
    Returns:
        Tuple containing (new_api_key, ApiKey) or None if failed
    """
    try:
        # Find the API key
        api_key = db.query(ApiKey).filter(
            ApiKey.key_id == key_id
        ).first()
        
        if not api_key:
            logger.warning(f"API key not found: {key_id}")
            return None
        
        # Generate a new API key
        new_api_key, new_key_id = generate_api_key()
        
        # Create a new key entry
        new_api_key_db = ApiKey(
            key_id=new_key_id,
            key_hash=hash_api_key(new_api_key),
            name=f"{api_key.name} (refreshed)",
            description=api_key.description,
            role=api_key.role,
            created_by=refreshed_by,
            expires_at=datetime.utcnow() + timedelta(days=expires_in_days),
            is_active=True,
            source_key_id=key_id
        )
        
        # Revoke the old key
        api_key.is_active = False
        api_key.revoked_at = datetime.utcnow()
        api_key.revoked_by = refreshed_by
        api_key.refreshed_key_id = new_key_id
        
        db.add(new_api_key_db)
        db.commit()
        db.refresh(new_api_key_db)
        
        logger.info(f"API key {key_id} refreshed by {refreshed_by}, new key ID: {new_key_id}")
        return new_api_key, new_api_key_db
        
    except Exception as e:
        logger.error(f"Error refreshing API key: {str(e)}")
        db.rollback()
        return None

def get_api_keys_for_user(db: Session, username: str) -> List[Dict[str, Any]]:
    """
    Get all API keys created by a user
    
    Args:
        db: Database session
        username: Username to get keys for
        
    Returns:
        List of API key dictionaries
    """
    try:
        keys = db.query(ApiKey).filter(
            ApiKey.created_by == username
        ).order_by(ApiKey.created_at.desc()).all()
        
        result = []
        for key in keys:
            result.append({
                "key_id": key.key_id,
                "name": key.name,
                "description": key.description,
                "role": key.role,
                "created_at": key.created_at.isoformat(),
                "expires_at": key.expires_at.isoformat(),
                "is_active": key.is_active,
                "last_used_at": key.last_used_at.isoformat() if key.last_used_at else None,
                "use_count": key.use_count,
                "revoked_at": key.revoked_at.isoformat() if key.revoked_at else None,
                "revoked_by": key.revoked_by
            })
        
        return result
        
    except Exception as e:
        logger.error(f"Error fetching API keys for user {username}: {str(e)}")
        return []

# Son güncelleme: 2025-05-20 07:43:54
# Güncelleyen: Teeksss