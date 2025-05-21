"""
Server Models for SQL Proxy

This module defines database models for database server connections.

Last updated: 2025-05-21 06:51:05
Updated by: Teeksss
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.db.base_class import Base

class Server(Base):
    """Server model"""
    __tablename__ = "servers"
    
    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    alias = Column(String(100), nullable=True)
    host = Column(String(255), nullable=False)
    port = Column(Integer, nullable=False)
    username = Column(String(100), nullable=False)
    password = Column(Text, nullable=True)  # Clear password or encrypted password
    database = Column(String(100), nullable=False)
    service_name = Column(String(100), nullable=True)  # For Oracle connections
    db_type = Column(String(20), nullable=False)  # postgresql, mysql, sqlserver, oracle, etc.
    ssl_enabled = Column(Boolean, default=False)
    ssl_ca = Column(Text, nullable=True)
    ssl_cert = Column(Text, nullable=True)
    ssl_key = Column(Text, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_encrypted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=True)
    connection_params = Column(JSON, nullable=True)
    use_vault = Column(Boolean, default=False)  # Added field to indicate use of Vault
    
    # Relationships
    user = relationship("User", back_populates="servers")
    
    def __repr__(self):
        return f"<Server {self.alias or self.host}>"

# Son güncelleme: 2025-05-21 06:51:05
# Güncelleyen: Teeksss