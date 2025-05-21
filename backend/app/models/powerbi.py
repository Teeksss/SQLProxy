"""
PowerBI Models for SQL Proxy

This module defines database models for PowerBI integration.

Last updated: 2025-05-21 05:44:49
Updated by: Teeksss
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base_class import Base

class PowerBIWorkspace(Base):
    """PowerBI workspace model"""
    __tablename__ = "powerbi_workspaces"
    
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    created_by = relationship("User", back_populates="powerbi_workspaces")
    reports = relationship("PowerBIReport", back_populates="workspace", cascade="all, delete-orphan")
    datasets = relationship("PowerBIDataset", back_populates="workspace", cascade="all, delete-orphan")

class PowerBIReport(Base):
    """PowerBI report model"""
    __tablename__ = "powerbi_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    embed_url = Column(String(1024), nullable=True)
    dataset_id = Column(String(255), nullable=True)
    workspace_id = Column(String(255), ForeignKey("powerbi_workspaces.workspace_id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    refresh_schedule = Column(String(255), nullable=True)  # Cron expression
    last_refreshed_at = Column(DateTime, nullable=True)
    last_refresh_status = Column(String(255), nullable=True)
    
    # Relationships
    created_by = relationship("User", back_populates="powerbi_reports")
    workspace = relationship("PowerBIWorkspace", back_populates="reports")

class PowerBIDataset(Base):
    """PowerBI dataset model"""
    __tablename__ = "powerbi_datasets"
    
    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    workspace_id = Column(String(255), ForeignKey("powerbi_workspaces.workspace_id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    refresh_schedule = Column(String(255), nullable=True)  # Cron expression
    last_refreshed_at = Column(DateTime, nullable=True)
    last_refresh_status = Column(String(255), nullable=True)
    
    # Relationships
    created_by = relationship("User", back_populates="powerbi_datasets")
    workspace = relationship("PowerBIWorkspace", back_populates="datasets")

# Add relationships to User model (in app/models/user.py)
# User.powerbi_workspaces = relationship("PowerBIWorkspace", back_populates="created_by")
# User.powerbi_reports = relationship("PowerBIReport", back_populates="created_by")
# User.powerbi_datasets = relationship("PowerBIDataset", back_populates="created_by")

# Son güncelleme: 2025-05-21 05:44:49
# Güncelleyen: Teeksss