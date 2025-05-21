"""
Configuration settings for SQL Proxy

This module defines configuration settings loaded from environment
variables or .env files.

Last updated: 2025-05-21 06:51:05
Updated by: Teeksss
"""

import os
import secrets
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseSettings, PostgresDsn, validator, AnyHttpUrl, EmailStr, Field

class Settings(BaseSettings):
    # ... Mevcut yapılandırma ayarları ...
    
    # Vault Configuration
    VAULT_ENABLED: bool = Field(False, env="VAULT_ENABLED")
    VAULT_URL: Optional[str] = Field(None, env="VAULT_URL")
    VAULT_TOKEN: Optional[str] = Field(None, env="VAULT_TOKEN")
    VAULT_MOUNT_POINT: str = Field("sqlproxy", env="VAULT_MOUNT_POINT")
    
    @validator("VAULT_ENABLED")
    def validate_vault_enabled(cls, v: bool, values: Dict[str, Any]) -> bool:
        if v and not (values.get("VAULT_URL") and values.get("VAULT_TOKEN")):
            raise ValueError("VAULT_URL and VAULT_TOKEN must be set if VAULT_ENABLED is True")
        return v
    
    # ... Diğer yapılandırma ayarları ...

# Son güncelleme: 2025-05-21 06:51:05
# Güncelleyen: Teeksss