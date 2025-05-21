"""
Dashboard Models for SQL Proxy

This module defines database models for user dashboards.

Last updated: 2025-05-21 06:42:20
Updated by: Teeksss
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.db.base_class import Base

class Dashboard(Base):
    """Dashboard model"""
    __tablename__ = "dashboards"
    
    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_default = Column(Boolean, default=False)
    config = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="dashboards")

# Update User model relationship in app/models/user.py:
# User.dashboards = relationship("Dashboard", back_populates="user", cascade="all, delete-orphan")

# Son güncelleme: 2025-05-21 06:42:20
# Güncelleyen: Teeksss