"""
Auto-scaling models for SQL Proxy

This module defines the database models for auto-scaling policies,
metrics, and events.

Last updated: 2025-05-20 10:30:03
Updated by: Teeksss
"""

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, Float,
    ForeignKey, JSON, Enum, func
)
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base_class import Base

class ScalingPolicy(Base):
    """
    Auto-scaling policy
    
    Defines when and how to scale database server resources
    """
    __tablename__ = "scaling_policies"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    server_alias = Column(String(100), nullable=False, index=True)
    
    # Scaling trigger
    metric_type = Column(
        Enum(
            'query_rate',        # Queries per minute
            'error_rate',        # Error percentage
            'cpu_usage',         # CPU usage percentage
            'memory_usage',      # Memory usage percentage
            'connection_count',  # Active connections
            name='scaling_metric_type'
        ),
        nullable=False
    )
    
    # Scaling direction
    scale_direction = Column(
        Enum(
            'up',    # Scale up resources
            'down',  # Scale down resources
            name='scale_direction'
        ),
        nullable=False
    )
    
    # Threshold to trigger scaling
    threshold_value = Column(Float, nullable=False)
    threshold_duration_seconds = Column(Integer, default=60)  # How long the threshold must be exceeded
    
    # Scaling action
    action_type = Column(
        Enum(
            'connection_pool',   # Adjust connection pool size
            'server_resource',   # Adjust server resources (CPU, memory)
            'load_balancing',    # Adjust load balancing weight
            name='scaling_action'
        ),
        nullable=False
    )
    
    # Action configuration (JSON)
    action_config = Column(Text, nullable=True)
    
    # Cooldown period to prevent rapid scaling
    cooldown_seconds = Column(Integer, default=300)
    
    # Status
    is_active = Column(Boolean, default=True, index=True)
    
    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(100), nullable=True)
    updated_by = Column(String(100), nullable=True)
    
    def __repr__(self):
        return f"<ScalingPolicy(id={self.id}, server='{self.server_alias}', metric='{self.metric_type}')>"

class ScalingEvent(Base):
    """
    Auto-scaling event
    
    Records scaling actions that were taken
    """
    __tablename__ = "scaling_events"
    
    id = Column(Integer, primary_key=True, index=True)
    server_alias = Column(String(100), nullable=False, index=True)
    policy_id = Column(Integer, ForeignKey("scaling_policies.id"), nullable=False)
    
    # Event details
    action_type = Column(String(50), nullable=False)
    scale_direction = Column(String(10), nullable=False)
    status = Column(
        Enum(
            'in_progress',  # Scaling action is in progress
            'success',      # Scaling action succeeded
            'failed',       # Scaling action failed
            name='scaling_status'
        ),
        nullable=False,
        default='in_progress'
    )
    
    # Metric that triggered the scaling
    metric_type = Column(String(50), nullable=False)
    metric_value = Column(Float, nullable=True)
    threshold_value = Column(Float, nullable=True)
    
    # Action configuration (JSON)
    action_config = Column(Text, nullable=True)
    
    # Result
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    completed_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<ScalingEvent(id={self.id}, server='{self.server_alias}', status='{self.status}')>"

class ScalingMetric(Base):
    """
    Scaling metric
    
    Records metric values for scaling decisions and historical analysis
    """
    __tablename__ = "scaling_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    server_alias = Column(String(100), nullable=False, index=True)
    metric_type = Column(String(50), nullable=False, index=True)
    value = Column(Float, nullable=False)
    timestamp = Column(DateTime, nullable=False, index=True)
    
    def __repr__(self):
        return f"<ScalingMetric(id={self.id}, server='{self.server_alias}', metric='{self.metric_type}')>"

# Son güncelleme: 2025-05-20 10:30:03
# Güncelleyen: Teeksss