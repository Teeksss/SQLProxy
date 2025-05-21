"""
Security Service for SQL Proxy

This module provides enhanced security functionality for SQL Proxy,
including token management, API request signing, and encryption.

Last updated: 2025-05-21 06:32:20
Updated by: Teeksss
"""

import logging
import os
import json
import hashlib
import hmac
import base64
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Union

from jose import jwt, JWTError
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend

from app.core.config import settings

logger = logging.getLogger(__name__)

class SecurityService:
    """
    Enhanced security service for SQL Proxy
    
    Provides functionality for token management, encryption/decryption,
    and API request signing and verification.
    """
    
    def __init__(self):
        """Initialize security service"""
        self.secret_key = settings.SECRET_KEY
        self.algorithm = "HS256"
        self.access_token_expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire_days = settings.REFRESH_TOKEN_EXPIRE_DAYS
        
        # Initialize encryption key
        self.encryption_key = hashlib.sha256(self.secret_key.encode()).digest()
    
    def create_access_token(self, data: Dict[str, Any]) -> str:
        """
        Create a new access token
        
        Args:
            data: Token payload data
            
        Returns:
            JWT token string
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({"exp": expire})
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """
        Create a new refresh token
        
        Args:
            data: Token payload data
            
        Returns:
            JWT token string
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        to_encode.update({"exp": expire})
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Validate and decode a JWT token
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded token payload or None if invalid
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError:
            logger.warning("Invalid token", exc_info=True)
            return None
    
    def generate_api_key(self, user_id: int, scopes: Optional[list] = None) -> str:
        """
        Generate an API key for external access
        
        Args:
            user_id: User ID
            scopes: Optional list of permission scopes
            
        Returns:
            API key string
        """
        key_uuid = str(uuid.uuid4())
        key_hash = hashlib.sha256(f"{key_uuid}{self.secret_key}{user_id}".encode()).hexdigest()
        api_key = f"{key_uuid}.{key_hash[:32]}"
        
        return api_key
    
    def validate_api_key(self, api_key: str, expected_user_id: int) -> bool:
        """
        Validate an API key
        
        Args:
            api_key: API key to validate
            expected_user_id: Expected user ID
            
        Returns:
            True if valid, False otherwise
        """
        try:
            key_parts = api_key.split(".")
            
            if len(key_parts) != 2:
                return False
            
            key_uuid, key_hash = key_parts
            
            expected_hash = hashlib.sha256(f"{key_uuid}{self.secret_key}{expected_user_id}".encode()).hexdigest()[:32]
            
            return key_hash == expected_hash
        except:
            return False
    
    def encrypt(self, data: str) -> str:
        """
        Encrypt sensitive data
        
        Args:
            data: String data to encrypt
            
        Returns:
            Base64-encoded encrypted data
        """
        try:
            # Generate a random IV
            iv = os.urandom(16)
            
            # Create AES cipher
            cipher = Cipher(
                algorithms.AES(self.encryption_key),
                modes.CBC(iv),
                backend=default_backend()
            )
            
            # Add padding
            padder = padding.PKCS7(algorithms.AES.block_size).padder()
            padded_data = padder.update(data.encode()) + padder.finalize()
            
            # Encrypt
            encryptor = cipher.encryptor()
            encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
            
            # Combine IV and encrypted data and encode as base64
            result = base64.b64encode(iv + encrypted_data).decode()
            
            return result
        except Exception as e:
            logger.error(f"Encryption error: {e}", exc_info=True)
            raise
    
    def decrypt(self, encrypted_data: str) -> str:
        """
        Decrypt encrypted data
        
        Args:
            encrypted_data: Base64-encoded encrypted data
            
        Returns:
            Decrypted string
        """
        try:
            # Decode from base64
            binary_data = base64.b64decode(encrypted_data)
            
            # Extract IV and ciphertext
            iv = binary_data[:16]
            ciphertext = binary_data[16:]
            
            # Create AES cipher
            cipher = Cipher(
                algorithms.AES(self.encryption_key),
                modes.CBC(iv),
                backend=default_backend()
            )
            
            # Decrypt
            decryptor = cipher.decryptor()
            padded_data = decryptor.update(ciphertext) + decryptor.finalize()
            
            # Remove padding
            unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
            data = unpadder.update(padded_data) + unpadder.finalize()
            
            return data.decode()
        except Exception as e:
            logger.error(f"Decryption error: {e}", exc_info=True)
            raise
    
    def sign_request(self, data: Dict[str, Any]) -> str:
        """
        Sign request data for API verification
        
        Args:
            data: Request data to sign
            
        Returns:
            Request signature
        """
        try:
            # Add timestamp
            data_with_timestamp = data.copy()
            data_with_timestamp["timestamp"] = int(time.time())
            
            # Sort keys to ensure deterministic order
            serialized_data = json.dumps(data_with_timestamp, sort_keys=True)
            
            # Create signature
            signature = hmac.new(
                self.secret_key.encode(),
                serialized_data.encode(),
                hashlib.sha256
            ).hexdigest()
            
            return signature
        except Exception as e:
            logger.error(f"Error signing request: {e}", exc_info=True)
            raise
    
    def verify_signature(self, data: Dict[str, Any], signature: str, max_age_seconds: int = 300) -> bool:
        """
        Verify request signature
        
        Args:
            data: Request data
            signature: Request signature to verify
            max_age_seconds: Maximum age of the request in seconds
            
        Returns:
            True if signature is valid, False otherwise
        """
        try:
            # Check timestamp
            timestamp = data.get("timestamp")
            if not timestamp:
                return False
            
            current_time = int(time.time())
            if current_time - timestamp > max_age_seconds:
                return False
            
            # Sort keys to ensure deterministic order
            serialized_data = json.dumps(data, sort_keys=True)
            
            # Compute expected signature
            expected_signature = hmac.new(
                self.secret_key.encode(),
                serialized_data.encode(),
                hashlib.sha256
            ).hexdigest()
            
            return signature == expected_signature
        except Exception as e:
            logger.error(f"Error verifying signature: {e}", exc_info=True)
            return False
    
    def encrypt_powerbi_credentials(self, tenant_id: str, client_id: str, client_secret: str) -> Dict[str, str]:
        """
        Encrypt PowerBI credentials for secure storage
        
        Args:
            tenant_id: Azure tenant ID
            client_id: Azure client (application) ID
            client_secret: Azure client secret
            
        Returns:
            Dictionary of encrypted credentials
        """
        try:
            encrypted_tenant_id = self.encrypt(tenant_id)
            encrypted_client_id = self.encrypt(client_id)
            encrypted_client_secret = self.encrypt(client_secret)
            
            return {
                "tenant_id": encrypted_tenant_id,
                "client_id": encrypted_client_id,
                "client_secret": encrypted_client_secret
            }
        except Exception as e:
            logger.error(f"Error encrypting PowerBI credentials: {e}", exc_info=True)
            raise
    
    def decrypt_powerbi_credentials(self, encrypted_credentials: Dict[str, str]) -> Dict[str, str]:
        """
        Decrypt PowerBI credentials
        
        Args:
            encrypted_credentials: Dictionary of encrypted credentials
            
        Returns:
            Dictionary of decrypted credentials
        """
        try:
            tenant_id = self.decrypt(encrypted_credentials["tenant_id"])
            client_id = self.decrypt(encrypted_credentials["client_id"])
            client_secret = self.decrypt(encrypted_credentials["client_secret"])
            
            return {
                "tenant_id": tenant_id,
                "client_id": client_id,
                "client_secret": client_secret
            }
        except Exception as e:
            logger.error(f"Error decrypting PowerBI credentials: {e}", exc_info=True)
            raise

# Initialize security service
security_service = SecurityService()

# Son güncelleme: 2025-05-21 06:32:20
# Güncelleyen: Teeksss