"""
Anomaly detection models for SQL Proxy

This module defines the database models for machine learning-based
anomaly detection and alert storage.

Last updated: 2025-05-20 10:25:32
Updated by: Teeksss
"""

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, Float,
    ForeignKey, JSON, Enum, func
)
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base_class import Base

class AnomalyModel(Base):
    """
    Machine learning model metadata
    
    Stores information about trained anomaly detection models
    """
    __tablename__ = "anomaly_models"
    
    id = Column(Integer, primary_key=True, index=True)
    model_type = Column(String(50), unique=True, nullable=False, index=True)
    parameters = Column(Text, nullable=True)  # JSON string of model parameters
    training_samples = Column(Integer, nullable=True)
    feature_count = Column(Integer, nullable=True)
    
    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    trained_by = Column(String(100), nullable=True)
    
    def __repr__(self):
        return f"<AnomalyModel(id={self.id}, type='{self.model_type}')>"

class AnomalyAlert(Base):
    """
    Anomaly alert record
    
    Stores information about detected anomalies
    """
    __tablename__ = "anomaly_alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Alert metadata
    anomaly_type = Column(
        Enum(
            'query_volume',      # Unusual number of queries
            'slow_query',        # Unusually slow query
            'unusual_time',      # Query at unusual time
            'unusual_behavior',  # Unusual user behavior
            'suspicious_query',  # Suspicious query content
            'unusual_access',    # Unusual table access
            name='anomaly_type'
        ),
        nullable=False,
        index=True
    )
    
    severity = Column(
        Enum(
            'low',       # Low priority alert
            'medium',    # Medium priority alert
            'high',      # High priority alert
            'critical',  # Critical priority alert
            name='alert_severity'
        ),
        nullable=False,
        default='medium',
        index=True
    )
    
    status = Column(
        Enum(
            'open',            # Newly detected anomaly
            'acknowledged',    # Anomaly has been acknowledged
            'resolved',        # Anomaly has been resolved
            'false_positive',  # Anomaly was a false positive
            name='alert_status'
        ),
        nullable=False,
        default='open',
        index=True
    )
    
    # Alert details
    query_id = Column(Integer, ForeignKey("audit_logs.id"), nullable=True)
    query_hash = Column(String(64), nullable=True, index=True)
    username = Column(String(100), nullable=True, index=True)
    user_role = Column(String(50), nullable=True)
    target_server = Column(String(100), nullable=True, index=True)
    client_ip = Column(String(45), nullable=True)
    details = Column(JSON, nullable=True)  # Details of the anomaly
    score = Column(Float, nullable=True)  # Anomaly score
    
    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    acknowledged_at = Column(DateTime, nullable=True)
    acknowledged_by = Column(String(100), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(String(100), nullable=True)
    resolution_notes = Column(Text, nullable=True)
    
    # Relationships
    query = relationship("AuditLog", foreign_keys=[query_id], backref="anomalies")
    
    def __repr__(self):
        return f"<AnomalyAlert(id={self.id}, type='{self.anomaly_type}', status='{self.status}')>"
    
    def to_dict(self):
        """Convert object to dictionary"""
        return {
            "id": self.id,
            "anomaly_type": self.anomaly_type,
            "severity": self.severity,
            "status": self.status,
            "query_id": self.query_id,
            "query_hash": self.query_hash,
            "username": self.username,
            "user_role": self.user_role,
            "target_server": self.target_server,
            "client_ip": self.client_ip,
            "details": self.details,
            "score": self.score,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            "acknowledged_by": self.acknowledged_by,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "resolved_by": self.resolved_by,
            "resolution_notes": self.resolution_notes
        }

class AnomalyTrainingJob(Base):
    """
    Anomaly model training job
    
    Tracks scheduled and completed model training jobs
    """
    __tablename__ = "anomaly_training_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    model_type = Column(String(50), nullable=False, index=True)
    
    status = Column(
        Enum(
            'scheduled',  # Job is scheduled
            'running',    # Job is running
            'completed',  # Job completed successfully
            'failed',     # Job failed
            name='job_status'
        ),
        nullable=False,
        default='scheduled',
        index=True
    )
    
    # Job details
    parameters = Column(JSON, nullable=True)  # Parameters for the training job
    result = Column(JSON, nullable=True)  # Results of the training
    error_message = Column(Text, nullable=True)  # Error message if failed
    
    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_by = Column(String(100), nullable=True)
    
    def __repr__(self):
        return f"<AnomalyTrainingJob(id={self.id}, type='{self.model_type}', status='{self.status}')>"

class AnomalyFeedback(Base):
    """
    User feedback on anomaly alerts
    
    Stores feedback for improving anomaly detection models
    """
    __tablename__ = "anomaly_feedback"
    
    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(Integer, ForeignKey("anomaly_alerts.id"), nullable=False)
    
    feedback_type = Column(
        Enum(
            'true_positive',   # This was a real anomaly
            'false_positive',  # This was not an anomaly
            'true_negative',   # System correctly did not alert
            'false_negative',  # System missed an anomaly
            name='feedback_type'
        ),
        nullable=False
    )
    
    # Feedback details
    comments = Column(Text, nullable=True)
    correct_severity = Column(
        Enum(
            'low',
            'medium',
            'high',
            'critical',
            'not_anomaly',
            name='feedback_severity'
        ),
        nullable=True
    )
    
    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100), nullable=False)
    
    # Relationships
    alert = relationship("AnomalyAlert", foreign_keys=[alert_id], backref="feedback")
    
    def __repr__(self):
        return f"<AnomalyFeedback(id={self.id}, type='{self.feedback_type}', alert_id={self.alert_id})>"

# Son güncelleme: 2025-05-20 10:25:32
# Güncelleyen: Teeksss