"""
Configuration models for SQL Proxy

This module defines the database models for storing system configuration.

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

class SystemConfig(Base):
    """
    System configuration parameter
    
    Stores configuration parameters that can be changed at runtime
    """
    __tablename__ = "system_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Configuration structure
    section = Column(String(50), nullable=False, index=True)
    param = Column(String(50), nullable=False, index=True)
    value = Column(Text, nullable=False)  # JSON-encoded value
    
    # Metadata
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    
    # Audit fields
    created_by = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_by = Column(String(100), nullable=True)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    
    __table_args__ = (
        # Composite unique index on section and param
        {'sqlite_autoincrement': True},
    )
    
    def __repr__(self):
        return f"<SystemConfig(section='{self.section}', param='{self.param}')>"

# Son güncelleme: 2025-05-20 07:43:54
# Güncelleyen: Teeksss