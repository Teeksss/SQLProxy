"""
Models for data masking rules in SQL Proxy

Last updated: 2025-05-16 13:44:50
Updated by: Teeksss
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.base_class import Base

class MaskingRule(Base):
    """Masking rule model for sensitive data in query results"""
    __tablename__ = "masking_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Rule definition
    table_pattern = Column(String(255), nullable=False)
    column_mappings = Column(JSON, nullable=False)  # Maps column names to masking types
    
    # Rule control
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=100)  # Higher number = higher priority
    
    # Rule exemptions
    roles_exempted = Column(JSON, nullable=True)  # List of roles exempt from this rule
    users_exempted = Column(JSON, nullable=True)  # List of specific users exempt from this rule
    
    # Rule metadata
    created_by = Column(String(100), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    def __repr__(self):
        return f"<MaskingRule(name='{self.name}', table_pattern='{self.table_pattern}')>"