"""
Audit Models for SQL Proxy

This module defines database models for auditing user actions and system events.

Last updated: 2025-05-21 06:54:19
Updated by: Teeksss
"""

from sqlalchemy import Column, String, Integer, Text, DateTime, JSON, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base_class import Base

class AuditLog(Base):
    """Audit log model"""
    __tablename__ = "audit_logs"
    
    id = Column(String(36), primary_key=True, index=True)
    event_type = Column(String(50), nullable=False, index=True)  # security, data, system
    resource_type = Column(String(50), nullable=False, index=True)  # query, server, user, powerbi
    resource_id = Column(String(255), nullable=True, index=True)
    action = Column(String(50), nullable=False, index=True)  # create, update, delete, access, etc.
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    username = Column(String(100), nullable=True)
    client_ip = Column(String(45), nullable=True)  # IPv6 support
    details = Column(JSON, nullable=True)
    status = Column(String(20), nullable=False, index=True)  # success, failure, error
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")
    
    # Indexes
    __table_args__ = (
        Index('ix_audit_logs_timestamp_user_id', timestamp, user_id),
        Index('ix_audit_logs_resource_action', resource_type, action),
        Index('ix_audit_logs_event_status', event_type, status),
    )

# Update User model relationship in app/models/user.py:
# User.audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")

# Son güncelleme: 2025-05-21 06:54:19
# Güncelleyen: Teeksss