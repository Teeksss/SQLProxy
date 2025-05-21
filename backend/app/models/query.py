from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base

class QueryWhitelist(Base):
    """Model for whitelisted SQL queries."""
    __tablename__ = "query_whitelist"
    
    id = Column(Integer, primary_key=True, index=True)
    query_hash = Column(String(64), unique=True, index=True, nullable=False)
    sql_query = Column(Text, nullable=False)
    query_type = Column(String(20), nullable=False)  # read, write, ddl, procedure
    approved_by = Column(String(100), nullable=False)
    approved_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    server_restrictions = Column(JSON, nullable=True)  # List of server aliases where query can run
    powerbi_only = Column(Boolean, default=False, nullable=False)
    tags = Column(JSON, nullable=True)  # Optional tags for categorization
    description = Column(Text, nullable=True)  # Optional description
    
    # Relations
    audit_logs = relationship("AuditLog", back_populates="whitelist_query")

class AuditLog(Base):
    """Model for SQL query execution audit logs."""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), nullable=False, index=True)
    user_role = Column(String(20), nullable=False)
    client_ip = Column(String(45), nullable=False)  # IPv6 compatible
    query_text = Column(Text, nullable=False)
    query_hash = Column(String(64), nullable=False, index=True)
    whitelist_id = Column(Integer, ForeignKey("query_whitelist.id"), nullable=True)
    target_server = Column(String(100), nullable=False, index=True)
    execution_status = Column(String(20), nullable=False)  # success, error, rejected
    error_message = Column(Text, nullable=True)
    execution_time_ms = Column(Integer, nullable=True)
    rows_affected = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relations
    whitelist_query = relationship("QueryWhitelist", back_populates="audit_logs")

class ServerConfig(Base):
    """Model for database server configurations."""
    __tablename__ = "server_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    server_alias = Column(String(100), unique=True, nullable=False, index=True)
    server_host = Column(String(255), nullable=False)
    server_port = Column(Integer, nullable=False)
    database_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    allowed_roles = Column(JSON, nullable=False)  # List of roles allowed to access server
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class RateLimitRule(Base):
    """Model for rate limiting rules."""
    __tablename__ = "rate_limit_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    rule_type = Column(String(20), nullable=False)  # user, role, ip
    identifier = Column(String(100), nullable=False, index=True)  # username, role name, or IP
    max_requests = Column(Integer, nullable=False)
    window_seconds = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    __table_args__ = (
        # Combination of rule_type and identifier must be unique
        # (e.g., one rule per user, per role, etc.)
        {'unique_constraint': ('rule_type', 'identifier')}
    )