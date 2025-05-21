"""
SDK Configuration Models for SQL Proxy

This module defines database models for client SDK configuration.

Last updated: 2025-05-20 11:25:24
Updated by: Teeksss
"""

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, 
    ForeignKey, JSON, Enum, func, Index
)
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base_class import Base

class SDKConfig(Base):
    """
    SDK configuration for client integrations
    
    Stores settings and credentials for client SDKs to access SQL Proxy.
    """
    __tablename__ = "sdk_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    
    # Configuration
    allowed_servers = Column(Text, nullable=True)  # JSON list of server IDs
    allowed_operations = Column(Text, nullable=True)  # JSON list of operations (SELECT, INSERT, etc.)
    rate_limit = Column(Integer, default=100)  # Queries per minute
    
    # Authentication
    api_key = Column(String(100), nullable=True, unique=True, index=True)
    expires_at = Column(DateTime, nullable=True)
    
    # Ownership
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True, index=True)
    
    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(100), nullable=True)
    updated_by = Column(String(100), nullable=True)
    
    # Relationships
    owner = relationship("User", back_populates="sdk_configs")
    
    def __repr__(self):
        return f"<SDKConfig(id={self.id}, client_id='{self.client_id}', name='{self.name}')>"

# Son güncelleme: 2025-05-20 11:25:24
# Güncelleyen: Teeksss