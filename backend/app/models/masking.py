"""
Data Masking models for SQL Proxy

This module provides database models for data masking functionality.

Last updated: 2025-05-20 14:59:32
Updated by: Teeksss
"""

import enum
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base_class import Base

class MaskingType(str, enum.Enum):
    """Type of masking rule"""
    GLOBAL = "global"
    COLUMN = "column"

class MaskingRule(Base):
    """
    Masking rule model
    
    Represents a rule for masking sensitive data in query results.
    """
    __tablename__ = "masking_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    rule_type = Column(Enum(MaskingType), nullable=False, index=True)
    description = Column(Text, nullable=True)
    masking_method = Column(String(50), nullable=False)
    pattern = Column(Text, nullable=True)  # For GLOBAL rules
    column_name = Column(String(100), nullable=True, index=True)  # For COLUMN rules
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    created_by = relationship("User", back_populates="masking_rules")
    
    def __repr__(self):
        return f"<MaskingRule(id={self.id}, name='{self.name}', type='{self.rule_type}')>"

# Son güncelleme: 2025-05-20 14:59:32
# Güncelleyen: Teeksss