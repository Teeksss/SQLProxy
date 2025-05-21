"""
Vault Service for SQL Proxy

This module provides functionality for integrating with HashiCorp Vault
for secure secret management.

Last updated: 2025-05-21 06:51:05
Updated by: Teeksss
"""

import logging
import os
from typing import Dict, Any, Optional, List, Tuple
import hvac
from hvac.exceptions import InvalidPath, VaultError

from app.core.config import settings

logger = logging.getLogger(__name__)

class VaultService:
    """
    Service for interacting with HashiCorp Vault
    
    Provides functionality for storing, retrieving, and managing secrets
    securely using HashiCorp Vault.
    """
    
    def __init__(self):
        """Initialize Vault service"""
        self.enabled = settings.VAULT_ENABLED if hasattr(settings, 'VAULT_ENABLED') else False
        self.client = None
        
        if self.enabled:
            try:
                # Initialize Vault client
                self.client = hvac.Client(
                    url=settings.VAULT_URL,
                    token=settings.VAULT_TOKEN
                )
                
                # Check if the client is authenticated
                if not self.client.is_authenticated():
                    logger.error("Vault client failed to authenticate")
                    self.enabled = False
                else:
                    logger.info("Vault client successfully authenticated")
                
                # Initialize the KV secrets engine if needed
                self._initialize_secrets_engine()
            except Exception as e:
                logger.error(f"Error initializing Vault client: {e}", exc_info=True)
                self.enabled = False
    
    def _initialize_secrets_engine(self):
        """Initialize KV secrets engine if it doesn't exist"""
        try:
            # Check if the KV v2 secrets engine is mounted
            mounts = self.client.sys.list_mounted_secrets_engines()
            kv_path = f"{settings.VAULT_MOUNT_POINT}/"
            
            if kv_path not in mounts:
                logger.info(f"Creating KV secrets engine at {kv_path}")
                self.client.sys.enable_secrets_engine(
                    backend_type='kv',
                    path=settings.VAULT_MOUNT_POINT,
                    options={'version': '2'}
                )
        except Exception as e:
            logger.error(f"Error initializing secrets engine: {e}", exc_info=True)
    
    async def get_secret(
        self,
        path: str,
        key: Optional[str] = None
    ) -> Optional[Any]:
        """
        Get a secret from Vault
        
        Args:
            path: Secret path
            key: Optional specific key to retrieve
            
        Returns:
            Secret value or None if not found
        """
        if not self.enabled or not self.client:
            logger.warning("Vault is disabled or not configured properly")
            return None
        
        try:
            # Get secret from Vault KV v2
            mount_point = settings.VAULT_MOUNT_POINT
            response = self.client.secrets.kv.v2.read_secret_version(
                path=path,
                mount_point=mount_point
            )
            
            data = response.get('data', {}).get('data', {})
            
            # Return specific key or all data
            if key:
                return data.get(key)
            
            return data
        except InvalidPath:
            logger.warning(f"Secret not found at path {path}")
            return None
        except Exception as e:
            logger.error(f"Error retrieving secret from Vault: {e}", exc_info=True)
            return None
    
    async def set_secret(
        self,
        path: str,
        data: Dict[str, Any]
    ) -> bool:
        """
        Store a secret in Vault
        
        Args:
            path: Secret path
            data: Secret data to store
            
        Returns:
            Success status
        """
        if not self.enabled or not self.client:
            logger.warning("Vault is disabled or not configured properly")
            return False
        
        try:
            # Store secret in Vault KV v2
            mount_point = settings.VAULT_MOUNT_POINT
            self.client.secrets.kv.v2.create_or_update_secret(
                path=path,
                secret=data,
                mount_point=mount_point
            )
            
            logger.info(f"Secret stored successfully at path {path}")
            return True
        except Exception as e:
            logger.error(f"Error storing secret in Vault: {e}", exc_info=True)
            return False
    
    async def delete_secret(
        self,
        path: str
    ) -> bool:
        """
        Delete a secret from Vault
        
        Args:
            path: Secret path
            
        Returns:
            Success status
        """
        if not self.enabled or not self.client:
            logger.warning("Vault is disabled or not configured properly")
            return False
        
        try:
            # Delete secret from Vault KV v2
            mount_point = settings.VAULT_MOUNT_POINT
            self.client.secrets.kv.v2.delete_metadata_and_all_versions(
                path=path,
                mount_point=mount_point
            )
            
            logger.info(f"Secret deleted successfully at path {path}")
            return True
        except Exception as e:
            logger.error(f"Error deleting secret from Vault: {e}", exc_info=True)
            return False
    
    async def list_secrets(
        self,
        path: str
    ) -> List[str]:
        """
        List secrets at a path
        
        Args:
            path: Secret path
            
        Returns:
            List of secret keys
        """
        if not self.enabled or not self.client:
            logger.warning("Vault is disabled or not configured properly")
            return []
        
        try:
            # List secrets at path
            mount_point = settings.VAULT_MOUNT_POINT
            response = self.client.secrets.kv.v2.list_secrets(
                path=path,
                mount_point=mount_point
            )
            
            return response.get('data', {}).get('keys', [])
        except InvalidPath:
            logger.warning(f"No secrets found at path {path}")
            return []
        except Exception as e:
            logger.error(f"Error listing secrets from Vault: {e}", exc_info=True)
            return []
    
    async def get_database_credentials(
        self,
        server_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get database credentials from Vault
        
        Args:
            server_id: Server ID
            
        Returns:
            Database credentials or None if not found
        """
        path = f"database/servers/{server_id}"
        return await self.get_secret(path)
    
    async def store_database_credentials(
        self,
        server_id: str,
        credentials: Dict[str, Any]
    ) -> bool:
        """
        Store database credentials in Vault
        
        Args:
            server_id: Server ID
            credentials: Database credentials
            
        Returns:
            Success status
        """
        path = f"database/servers/{server_id}"
        return await self.set_secret(path, credentials)
    
    async def get_powerbi_credentials(self) -> Optional[Dict[str, Any]]:
        """
        Get PowerBI credentials from Vault
        
        Returns:
            PowerBI credentials or None if not found
        """
        return await self.get_secret("powerbi/credentials")
    
    async def store_powerbi_credentials(
        self,
        credentials: Dict[str, Any]
    ) -> bool:
        """
        Store PowerBI credentials in Vault
        
        Args:
            credentials: PowerBI credentials
            
        Returns:
            Success status
        """
        return await self.set_secret("powerbi/credentials", credentials)
    
    def is_enabled(self) -> bool:
        """
        Check if Vault integration is enabled
        
        Returns:
            True if enabled, False otherwise
        """
        return self.enabled and self.client is not None

# Initialize vault service
vault_service = VaultService()

# Son güncelleme: 2025-05-21 06:51:05
# Güncelleyen: Teeksss