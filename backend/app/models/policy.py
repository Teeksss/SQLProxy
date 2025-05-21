"""
Authorization policy models for SQL Proxy

This module defines the database models for the authorization
policy engine, including policies, rules, and conditions.

Last updated: 2025-05-20 10:44:00
Updated by: Teeksss
"""

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, 
    ForeignKey, JSON, Enum, func, Index
)
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base_class import Base

class AuthPolicy(Base):
    """
    Authorization policy
    
    Defines a set of rules for making authorization decisions
    """
    __tablename__ = "auth_policies"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    
    # Type of resource this policy applies to (e.g., "query", "server", etc.)
    resource_type = Column(String(50), nullable=False, index=True)
    
    # Priority (higher takes precedence)
    priority = Column(Integer, default=0, index=True)
    
    # Default effect if no rules match (null means policy doesn't apply)
    default_effect = Column(Enum('allow', 'deny', name='policy_effect'), nullable=True)
    
    # Metadata (JSON)
    metadata = Column(Text, nullable=True)
    
    # Active status
    is_active = Column(Boolean, default=True, index=True)
    
    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(100), nullable=True)
    updated_by = Column(String(100), nullable=True)
    
    # Relationships
    rules = relationship("PolicyRule", back_populates="policy", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<AuthPolicy(id={self.id}, name='{self.name}', resource_type='{self.resource_type}')>"

class PolicyRule(Base):
    """
    Authorization policy rule
    
    Defines a rule within a policy that produces an allow/deny decision
    if its conditions match
    """
    __tablename__ = "policy_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    policy_id = Column(Integer, ForeignKey("auth_policies.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    
    # Priority (higher takes precedence)
    priority = Column(Integer, default=0, index=True)
    
    # Effect when rule matches
    effect = Column(Enum('allow', 'deny', name='rule_effect'), nullable=False)
    
    # Rule logic
    all_conditions_required = Column(Boolean, default=True)  # AND vs OR for conditions
    
    # Message to display when rule matches
    message = Column(Text, nullable=True)
    
    # Metadata (JSON)
    metadata = Column(Text, nullable=True)
    
    # Active status
    is_active = Column(Boolean, default=True, index=True)
    
    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(100), nullable=True)
    updated_by = Column(String(100), nullable=True)
    
    # Relationships
    policy = relationship("AuthPolicy", back_populates="rules")
    conditions = relationship("PolicyCondition", back_populates="rule", cascade="all, delete-orphan")
    
    __table_args__ = (
        # Ensure rule names are unique within a policy
        Index('ix_policy_rules_policy_id_name', policy_id, name, unique=True),
    )
    
    def __repr__(self):
        return f"<PolicyRule(id={self.id}, name='{self.name}', effect='{self.effect}')>"

class PolicyCondition(Base):
    """
    Authorization policy condition
    
    Defines a condition that must be met for a rule to match
    """
    __tablename__ = "policy_conditions"
    
    id = Column(Integer, primary_key=True, index=True)
    rule_id = Column(Integer, ForeignKey("policy_rules.id"), nullable=False, index=True)
    
    # Condition details
    field = Column(String(100), nullable=False)  # Field to compare
    operator = Column(String(20), nullable=False)  # e.g., eq, neq, in, gt, lt, etc.
    value = Column(Text, nullable=True)  # Value to compare against
    
    # For function-based conditions
    function = Column(String(100), nullable=True)  # Function name to call
    parameters = Column(Text, nullable=True)  # JSON parameters to pass to function
    
    # Description
    description = Column(Text, nullable=True)
    
    # Active status
    is_active = Column(Boolean, default=True, index=True)
    
    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    rule = relationship("PolicyRule", back_populates="conditions")
    
    def __repr__(self):
        if self.function:
            return f"<PolicyCondition(id={self.id}, function='{self.function}')>"
        else:
            return f"<PolicyCondition(id={self.id}, field='{self.field}', operator='{self.operator}')>"

# Son güncelleme: 2025-05-20 10:44:00
# Güncelleyen: Teeksss