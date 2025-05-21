"""
User Models for SQL Proxy

This module defines database models for user management.

Last updated: 2025-05-20 12:14:46
Updated by: Teeksss
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import (
    Boolean, Column, String, Integer, DateTime, 
    ForeignKey, Table, Text, Enum
)
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import relationship

from app.db.base_class import Base

# User-Role association table
user_role = Table(
    "user_role",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("role_id", Integer, ForeignKey("roles.id"), primary_key=True)
)

class User(Base):
    """
    User model
    
    Represents a user in the system with authentication and profile information.
    """
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=False)
    full_name = Column(String(100), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    
    # Two-factor authentication
    two_factor_enabled = Column(Boolean, default=False)
    two_factor_secret = Column(String(32), nullable=True)
    
    # Profile information
    avatar_url = Column(String(500), nullable=True)
    bio = Column(Text, nullable=True)
    company = Column(String(100), nullable=True)
    position = Column(String(100), nullable=True)
    
    # Contact information
    phone = Column(String(20), nullable=True)
    location = Column(String(100), nullable=True)
    website = Column(String(200), nullable=True)
    
    # Social media
    twitter = Column(String(100), nullable=True)
    github = Column(String(100), nullable=True)
    linkedin = Column(String(100), nullable=True)
    
    # Preferences
    preferences = Column(Text, nullable=True)  # JSON string
    
    # Usage statistics
    login_count = Column(Integer, default=0)
    last_login = Column(DateTime, nullable=True)
    last_active = Column(DateTime, nullable=True)
    last_ip = Column(String(45), nullable=True)
    
    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    password_changed_at = Column(DateTime, nullable=True)
    email_verified_at = Column(DateTime, nullable=True)
    
    # Relationships
    roles = relationship("Role", secondary=user_role, back_populates="users")
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
    queries = relationship("QueryHistory", back_populates="user", cascade="all, delete-orphan")
    sdk_configs = relationship("SDKConfig", back_populates="owner")
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"

class Role(Base):
    """
    Role model
    
    Represents a role for role-based access control.
    """
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, index=True, nullable=False)
    description = Column(String(200), nullable=True)
    
    # Permissions (stored as JSON string)
    permissions = Column(Text, nullable=True)
    
    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    users = relationship("User", secondary=user_role, back_populates="roles")
    
    def __repr__(self):
        return f"<Role(id={self.id}, name='{self.name}')>"

class APIKey(Base):
    """
    API Key model
    
    Represents an API key for authentication.
    """
    __tablename__ = "api_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    key_prefix = Column(String(8), nullable=False)
    key_hash = Column(String(255), nullable=False)
    
    # Scope and permissions
    scope = Column(String(255), nullable=True)  # Comma-separated scopes
    
    # Status
    is_active = Column(Boolean, default=True)
    is_admin_key = Column(Boolean, default=False)
    expires_at = Column(DateTime, nullable=True)
    
    # Rate limiting
    rate_limit = Column(Integer, default=100)  # Requests per minute
    
    # Usage statistics
    last_used_at = Column(DateTime, nullable=True)
    use_count = Column(Integer, default=0)
    
    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(50), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="api_keys")
    
    def __repr__(self):
        return f"<APIKey(id={self.id}, name='{self.name}', prefix='{self.key_prefix}')>"

class UserSession(Base):
    """
    User Session model
    
    Represents a user session for authentication tracking.
    """
    __tablename__ = "user_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_id = Column(String(64), unique=True, index=True, nullable=False)
    refresh_token = Column(String(255), nullable=True)
    
    # Device information
    user_agent = Column(String(500), nullable=True)
    ip_address = Column(String(45), nullable=True)
    device_type = Column(String(50), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime, nullable=False)
    
    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<UserSession(id={self.id}, user_id={self.user_id}, active={self.is_active})>"

# Son güncelleme: 2025-05-20 12:14:46
# Güncelleyen: Teeksss