"""
Notification Models for SQL Proxy

This module defines database models for user notifications.

Last updated: 2025-05-21 06:32:20
Updated by: Teeksss
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base_class import Base

class Notification(Base):
    """Notification model"""
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String(50), nullable=False)  # e.g., 'system', 'powerbi_refresh', 'query_complete'
    entity_type = Column(String(50), nullable=True)  # e.g., 'powerbi_dataset', 'query', 'server'
    entity_id = Column(String(255), nullable=True)  # ID of the related entity
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    read_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="notifications")

# Update User model relationship in app/models/user.py:
# User.notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")

# Son güncelleme: 2025-05-21 06:32:20
# Güncelleyen: Teeksss