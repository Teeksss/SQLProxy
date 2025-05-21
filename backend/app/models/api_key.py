"""
API key model for SQL Proxy

Defines the database model for API keys used for authentication.

Last updated: 2025-05-20 07:43:54
Updated by: Teeksss
"""

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, 
    ForeignKey, func
)
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base_class import Base

class ApiKey(Base):
    """
    API key model
    
    Stores API keys securely for API authentication
    """
    __tablename__ = "api_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    key_id = Column(String(36), unique=True, index=True, nullable=False)  # UUID
    key_hash = Column(String(64), nullable=False)  # SHA-256 hash of the key
    
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    
    # Role assigned to this API key
    role = Column(String(50), nullable=False, index=True)
    
    # Ownership and creation information
    created_by = Column(String(100), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Expiration
    expires_at = Column(DateTime, nullable=False, index=True)
    
    # State
    is_active = Column(Boolean, default=True, index=True)
    last_used_at = Column(DateTime, nullable=True)
    use_count = Column(Integer, default=0)
    
    # Revocation information
    revoked_at = Column(DateTime, nullable=True)
    revoked_by = Column(String(100), nullable=True)
    
    # For refreshed keys
    source_key_id = Column(String(36), ForeignKey("api_keys.key_id"), nullable=True)
    refreshed_key_id = Column(String(36), ForeignKey("api_keys.key_id"), nullable=True)
    
    # Relationships for key chains (refresh history)
    previous_key = relationship("ApiKey", foreign_keys=[source_key_id], remote_side=[key_id], backref="newer_key")
    next_key = relationship("ApiKey", foreign_keys=[refreshed_key_id], remote_side=[key_id], backref="older_key")
    
    def __repr__(self):
        return f"<ApiKey(id={self.id}, name='{self.name}')>"

# Son güncelleme: 2025-05-20 07:43:54
# Güncelleyen: Teeksss