"""
Approval workflow models for SQL Proxy

This module defines the models for multi-step approval workflows, including workflow
definitions, steps, instances, and step instances.

Last updated: 2025-05-20 06:11:09
Updated by: Teeksss
"""

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, 
    ForeignKey, Enum, JSON, func
)
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base_class import Base

class ApprovalWorkflow(Base):
    """
    Approval workflow definition
    
    Defines a multi-step approval process for specific types of queries
    """
    __tablename__ = "approval_workflows"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Rule for when this workflow applies
    rule_type = Column(
        Enum(
            'table',      # Based on tables accessed
            'schema',     # Based on schema accessed
            'server',     # Based on target server
            'query_type', # Based on query type (SELECT, INSERT, etc.)
            'user',       # Based on requesting user
            'role',       # Based on user role
            'regex',      # Based on regex pattern
            'tables_modified', # Based on tables being modified
            name='workflow_rule_type'
        ),
        nullable=False
    )
    
    # Condition for the rule (e.g., table name, regex pattern, etc.)
    rule_condition = Column(String(255), nullable=False)
    
    # Priority (higher number = higher priority) for when multiple workflows match
    priority = Column(Integer, default=10)
    
    is_active = Column(Boolean, default=True)
    
    # Audit fields
    created_by = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_by = Column(String(100), nullable=True)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    
    # Relationships
    steps = relationship("ApprovalStep", back_populates="workflow", cascade="all, delete-orphan")
    instances = relationship("ApprovalInstance", back_populates="workflow")
    
    def __repr__(self):
        return f"<ApprovalWorkflow(id={self.id}, name='{self.name}')>"

class ApprovalStep(Base):
    """
    Step in an approval workflow
    
    Defines a single step in an approval workflow, including who can approve it
    """
    __tablename__ = "approval_steps"
    
    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("approval_workflows.id"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    
    # Who can approve this step
    approver_type = Column(
        Enum(
            'user',  # Specific users
            'role',  # Users with specific roles
            'group', # Users in specific LDAP groups
            'team',  # Users in specific teams
            name='approver_type'
        ),
        nullable=False
    )
    
    # Value for the approver type (comma-separated for multiple values)
    approver_value = Column(String(255), nullable=False)
    
    # Order of this step in the workflow
    step_order = Column(Integer, nullable=False)
    
    # Whether this step is required or optional
    is_required = Column(Boolean, default=True)
    
    # Relationships
    workflow = relationship("ApprovalWorkflow", back_populates="steps")
    
    def __repr__(self):
        return f"<ApprovalStep(id={self.id}, name='{self.name}', workflow_id={self.workflow_id})>"

class ApprovalInstance(Base):
    """
    Instance of an approval workflow
    
    Represents an approval workflow in progress for a specific query
    """
    __tablename__ = "approval_instances"
    
    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("approval_workflows.id"), nullable=False)
    workflow_name = Column(String(100), nullable=False)  # Denormalized for historical reference
    
    # Query that is being approved
    query_id = Column(Integer, ForeignKey("pending_approvals.id"), nullable=False)
    
    # Current step in the workflow
    current_step = Column(Integer, nullable=False, default=1)
    
    # Status of the workflow instance
    status = Column(
        Enum(
            'pending',     # Workflow just started
            'in_progress', # Workflow has at least one approval
            'approved',    # Workflow completed with approval
            'rejected',    # Workflow rejected at some step
            'cancelled',   # Workflow cancelled by submitter or admin
            name='approval_instance_status'
        ),
        nullable=False,
        default='pending'
    )
    
    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    
    # Relationships
    workflow = relationship("ApprovalWorkflow", back_populates="instances")
    steps = relationship("StepInstance", back_populates="instance", cascade="all, delete-orphan")
    query = relationship("PendingApproval", back_populates="approval_instances")
    
    def __repr__(self):
        return f"<ApprovalInstance(id={self.id}, workflow_id={self.workflow_id}, status='{self.status}')>"

class StepInstance(Base):
    """
    Instance of a step in an approval workflow
    
    Represents a specific step instance within an approval workflow instance
    """
    __tablename__ = "step_instances"
    
    id = Column(Integer, primary_key=True, index=True)
    instance_id = Column(Integer, ForeignKey("approval_instances.id"), nullable=False)
    
    # Step details (denormalized for historical reference)
    step_name = Column(String(100), nullable=False)
    step_description = Column(Text, nullable=True)
    approver_type = Column(String(20), nullable=False)
    approver_value = Column(String(255), nullable=False)
    step_order = Column(Integer, nullable=False)
    is_required = Column(Boolean, default=True)
    
    # Status of this step
    status = Column(
        Enum(
            'pending',  # Step not yet reviewed
            'approved', # Step approved
            'rejected', # Step rejected
            'skipped',  # Step skipped (optional step)
            name='step_instance_status'
        ),
        nullable=False,
        default='pending'
    )
    
    # Approval information
    approver_comment = Column(Text, nullable=True)
    approved_by = Column(String(100), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    
    # Relationships
    instance = relationship("ApprovalInstance", back_populates="steps")
    
    def __repr__(self):
        return f"<StepInstance(id={self.id}, instance_id={self.instance_id}, status='{self.status}')>"

# Son güncelleme: 2025-05-20 06:11:09
# Güncelleyen: Teeksss