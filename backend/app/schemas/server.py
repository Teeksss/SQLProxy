"""
Server Schemas for SQL Proxy

This module provides Pydantic schemas for validating and serializing
server data.

Last updated: 2025-05-21 06:51:05
Updated by: Teeksss
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime

# Base Server Schema
class ServerBase(BaseModel):
    """Base server schema with common fields"""
    alias: Optional[str] = Field(None, description="Server alias/friendly name")
    host: str = Field(..., description="Server hostname or IP address")
    port: int = Field(..., description="Server port")
    username: str = Field(..., description="Database username")
    database: str = Field(..., description="Database name")
    service_name: Optional[str] = Field(None, description="Service name (for Oracle)")
    db_type: str = Field(..., description="Database type (postgresql, mysql, sqlserver, oracle)")
    ssl_enabled: bool = Field(False, description="Whether SSL is enabled")
    ssl_ca: Optional[str] = Field(None, description="SSL CA certificate")
    ssl_cert: Optional[str] = Field(None, description="SSL client certificate")
    ssl_key: Optional[str] = Field(None, description="SSL client key")
    connection_params: Optional[Dict[str, Any]] = Field(None, description="Additional connection parameters")
    use_vault: bool = Field(False, description="Whether to store credentials in Vault")  # Added field

# Server Create Schema
class ServerCreate(ServerBase):
    """Schema for creating a server"""
    password: Optional[str] = Field(None, description="Database password")

# Server Update Schema
class ServerUpdate(BaseModel):
    """Schema for updating a server"""
    alias: Optional[str] = Field(None, description="Server alias/friendly name")
    host: Optional[str] = Field(None, description="Server hostname or IP address")
    port: Optional[int] = Field(None, description="Server port")
    username: Optional[str] = Field(None, description="Database username")
    password: Optional[str] = Field(None, description="Database password")
    database: Optional[str] = Field(None, description="Database name")
    service_name: Optional[str] = Field(None, description="Service name (for Oracle)")
    db_type: Optional[str] = Field(None, description="Database type (postgresql, mysql, sqlserver, oracle)")
    ssl_enabled: Optional[bool] = Field(None, description="Whether SSL is enabled")
    ssl_ca: Optional[str] = Field(None, description="SSL CA certificate")
    ssl_cert: Optional[str] = Field(None, description="SSL client certificate")
    ssl_key: Optional[str] = Field(None, description="SSL client key")
    connection_params: Optional[Dict[str, Any]] = Field(None, description="Additional connection parameters")
    use_vault: Optional[bool] = Field(None, description="Whether to store credentials in Vault")  # Added field

# Server Response Schema
class ServerResponse(ServerBase):
    """Schema for server response"""
    id: str = Field(..., description="Server ID")
    user_id: int = Field(..., description="User ID")
    is_encrypted: bool = Field(..., description="Whether password is encrypted")
    created_at: datetime = Field(..., description="Creation datetime")
    updated_at: Optional[datetime] = Field(None, description="Update datetime")
    
    class Config:
        orm_mode = True

# Server List Schema
class ServerListResponse(BaseModel):
    """Schema for listing servers"""
    items: List[ServerResponse] = Field(..., description="Servers")
    total: int = Field(..., description="Total number of servers")

# Son güncelleme: 2025-05-21 06:51:05
# Güncelleyen: Teeksss