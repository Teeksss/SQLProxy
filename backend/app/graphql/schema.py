"""
GraphQL Schema for SQL Proxy

This module defines the GraphQL schema for the SQL Proxy API,
providing a flexible API layer for advanced client integrations.

Last updated: 2025-05-20 10:34:03
Updated by: Teeksss
"""

import graphene
from graphene import relay
from graphene_sqlalchemy import SQLAlchemyObjectType, SQLAlchemyConnectionField
from graphql import GraphQLError
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.db.base_class import Base
from app.models.query import AuditLog, WhitelistedQuery, PendingApproval
from app.models.server import ServerConfig, ServerGroup
from app.models.user import User
from app.models.anomaly import AnomalyAlert
from app.db.session import db_session
from app.auth.jwt import get_current_user_from_token
from app.services.db_connector import db_connector_service

logger = logging.getLogger(__name__)

# Define SQLAlchemy Object Types

class ServerType(SQLAlchemyObjectType):
    class Meta:
        model = ServerConfig
        interfaces = (relay.Node, )
        exclude_fields = ('password',)

class ServerGroupType(SQLAlchemyObjectType):
    class Meta:
        model = ServerGroup
        interfaces = (relay.Node, )

class UserType(SQLAlchemyObjectType):
    class Meta:
        model = User
        interfaces = (relay.Node, )
        exclude_fields = ('password_hash',)

class AuditLogType(SQLAlchemyObjectType):
    class Meta:
        model = AuditLog
        interfaces = (relay.Node, )

class WhitelistedQueryType(SQLAlchemyObjectType):
    class Meta:
        model = WhitelistedQuery
        interfaces = (relay.Node, )

class PendingApprovalType(SQLAlchemyObjectType):
    class Meta:
        model = PendingApproval
        interfaces = (relay.Node, )

class AnomalyAlertType(SQLAlchemyObjectType):
    class Meta:
        model = AnomalyAlert
        interfaces = (relay.Node, )

# Define Input Types

class ServerInput(graphene.InputObjectType):
    server_alias = graphene.String(required=True)
    server_name = graphene.String(required=True)
    server_host = graphene.String(required=True)
    server_port = graphene.Int(required=True)
    database_name = graphene.String(required=True)
    username = graphene.String(required=True)
    password = graphene.String(required=True)
    db_type = graphene.String(required=True)
    max_connections = graphene.Int()
    connection_timeout = graphene.Int()
    query_timeout = graphene.Int()
    allowed_roles = graphene.List(graphene.String)
    description = graphene.String()
    is_active = graphene.Boolean()
    is_read_only = graphene.Boolean()
    enable_masking = graphene.Boolean()
    group_id = graphene.Int()

class WhitelistedQueryInput(graphene.InputObjectType):
    query_text = graphene.String(required=True)
    description = graphene.String()
    server_restrictions = graphene.List(graphene.String)
    role_restrictions = graphene.List(graphene.String)
    is_active = graphene.Boolean()

class UserInput(graphene.InputObjectType):
    username = graphene.String(required=True)
    email = graphene.String(required=True)
    password = graphene.String()
    role = graphene.String(required=True)
    is_active = graphene.Boolean()
    first_name = graphene.String()
    last_name = graphene.String()

class QueryExecutionInput(graphene.InputObjectType):
    query = graphene.String(required=True)
    server_alias = graphene.String(required=True)
    params = graphene.JSONString()
    timeout = graphene.Int()

class ApprovalInput(graphene.InputObjectType):
    id = graphene.Int(required=True)
    approve = graphene.Boolean(required=True)
    comment = graphene.String()

# Define custom types for query results

class QueryResultRow(graphene.ObjectType):
    """Represents a single row in a query result set"""
    values = graphene.JSONString()

class QueryResult(graphene.ObjectType):
    """Represents the result of a SQL query execution"""
    success = graphene.Boolean()
    error = graphene.String()
    rowcount = graphene.Int()
    columns = graphene.List(graphene.String)
    data = graphene.List(graphene.JSONString)
    execution_time = graphene.Float()
    execution_status = graphene.String()
    query_type = graphene.String()
    is_cached = graphene.Boolean()
    is_approved = graphene.Boolean()
    requires_approval = graphene.Boolean()
    approval_id = graphene.Int()

class ServerHealth(graphene.ObjectType):
    """Represents server health status"""
    server_alias = graphene.String()
    status = graphene.String()
    response_time_ms = graphene.Float()
    last_checked = graphene.DateTime()
    message = graphene.String()
    connection_count = graphene.Int()
    db_version = graphene.String()

class SystemMetrics(graphene.ObjectType):
    """Represents system metrics"""
    active_queries = graphene.Int()
    active_connections = graphene.Int()
    queries_per_minute = graphene.Float()
    error_rate = graphene.Float()
    avg_execution_time = graphene.Float()
    cache_hit_rate = graphene.Float()
    cpu_usage = graphene.Float()
    memory_usage = graphene.Float()
    timestamp = graphene.DateTime()

# Mutations

class CreateServer(graphene.Mutation):
    class Arguments:
        input = ServerInput(required=True)
    
    server = graphene.Field(lambda: ServerType)
    
    @staticmethod
    def mutate(root, info, input):
        user = get_current_user_from_token(info.context)
        if not user or user.role != 'admin':
            raise GraphQLError("Not authorized to create servers")
        
        server = ServerConfig(
            server_alias=input.server_alias,
            server_name=input.server_name,
            server_host=input.server_host,
            server_port=input.server_port,
            database_name=input.database_name,
            username=input.username,
            password=input.password,
            db_type=input.db_type,
            max_connections=input.max_connections or 10,
            connection_timeout=input.connection_timeout or 30,
            query_timeout=input.query_timeout or 60,
            allowed_roles=input.allowed_roles,
            description=input.description,
            is_active=input.is_active if input.is_active is not None else True,
            is_read_only=input.is_read_only if input.is_read_only is not None else False,
            enable_masking=input.enable_masking if input.enable_masking is not None else True,
            group_id=input.group_id,
            created_by=user.username,
            created_at=datetime.utcnow()
        )
        
        db_session.add(server)
        db_session.commit()
        
        return CreateServer(server=server)

class UpdateServer(graphene.Mutation):
    class Arguments:
        id = graphene.Int(required=True)
        input = ServerInput(required=True)
    
    server = graphene.Field(lambda: ServerType)
    
    @staticmethod
    def mutate(root, info, id, input):
        user = get_current_user_from_token(info.context)
        if not user or user.role != 'admin':
            raise GraphQLError("Not authorized to update servers")
        
        server = db_session.query(ServerConfig).filter(ServerConfig.id == id).first()
        if not server:
            raise GraphQLError(f"Server with ID {id} not found")
        
        # Update fields
        for key, value in input.items():
            if value is not None and key != 'id':
                setattr(server, key, value)
        
        server.updated_by = user.username
        server.updated_at = datetime.utcnow()
        
        db_session.commit()
        
        return UpdateServer(server=server)

class DeleteServer(graphene.Mutation):
    class Arguments:
        id = graphene.Int(required=True)
    
    success = graphene.Boolean()
    message = graphene.String()
    
    @staticmethod
    def mutate(root, info, id):
        user = get_current_user_from_token(info.context)
        if not user or user.role != 'admin':
            raise GraphQLError("Not authorized to delete servers")
        
        server = db_session.query(ServerConfig).filter(ServerConfig.id == id).first()
        if not server:
            raise GraphQLError(f"Server with ID {id} not found")
        
        # Soft delete (mark as inactive)
        server.is_active = False
        server.updated_by = user.username
        server.updated_at = datetime.utcnow()
        
        db_session.commit()
        
        return DeleteServer(success=True, message=f"Server {server.server_alias} deactivated")

class CreateWhitelistEntry(graphene.Mutation):
    class Arguments:
        input = WhitelistedQueryInput(required=True)
    
    whitelist_entry = graphene.Field(lambda: WhitelistedQueryType)
    
    @staticmethod
    def mutate(root, info, input):
        user = get_current_user_from_token(info.context)
        if not user or user.role not in ['admin', 'analyst']:
            raise GraphQLError("Not authorized to create whitelist entries")
        
        entry = WhitelistedQuery(
            query_text=input.query_text,
            description=input.description,
            server_restrictions=input.server_restrictions,
            role_restrictions=input.role_restrictions,
            is_active=input.is_active if input.is_active is not None else True,
            created_by=user.username,
            created_at=datetime.utcnow()
        )
        
        db_session.add(entry)
        db_session.commit()
        
        return CreateWhitelistEntry(whitelist_entry=entry)

class UpdateWhitelistEntry(graphene.Mutation):
    class Arguments:
        id = graphene.Int(required=True)
        input = WhitelistedQueryInput(required=True)
    
    whitelist_entry = graphene.Field(lambda: WhitelistedQueryType)
    
    @staticmethod
    def mutate(root, info, id, input):
        user = get_current_user_from_token(info.context)
        if not user or user.role not in ['admin', 'analyst']:
            raise GraphQLError("Not authorized to update whitelist entries")
        
        entry = db_session.query(WhitelistedQuery).filter(WhitelistedQuery.id == id).first()
        if not entry:
            raise GraphQLError(f"Whitelist entry with ID {id} not found")
        
        # Update fields
        for key, value in input.items():
            if value is not None and key != 'id':
                setattr(entry, key, value)
        
        entry.updated_by = user.username
        entry.updated_at = datetime.utcnow()
        
        db_session.commit()
        
        return UpdateWhitelistEntry(whitelist_entry=entry)

class ExecuteQuery(graphene.Mutation):
    class Arguments:
        input = QueryExecutionInput(required=True)
    
    result = graphene.Field(QueryResult)
    
    @staticmethod
    def mutate(root, info, input):
        user = get_current_user_from_token(info.context)
        if not user:
            raise GraphQLError("Authentication required")
        
        # Execute query
        try:
            import asyncio
            result = asyncio.run(db_connector_service.execute_query(
                query=input.query,
                server_alias=input.server_alias,
                params=input.params or {},
                username=user.username,
                user_role=user.role,
                timeout=input.timeout or 60
            ))
            
            # Format the result
            return ExecuteQuery(result=QueryResult(
                success=not result.get("error"),
                error=result.get("error"),
                rowcount=result.get("rowcount", 0),
                columns=result.get("columns", []),
                data=[json.dumps(row) for row in result.get("data", [])],
                execution_time=result.get("execution_time"),
                execution_status=result.get("execution_status"),
                query_type=result.get("query_type"),
                is_cached=result.get("is_cached", False),
                is_approved=result.get("is_approved", False),
                requires_approval=result.get("requires_approval", False),
                approval_id=result.get("approval_id")
            ))
        
        except Exception as e:
            logger.error(f"Error executing query: {str(e)}")
            return ExecuteQuery(result=QueryResult(
                success=False,
                error=str(e),
                rowcount=0,
                columns=[],
                data=[],
                execution_time=0,
                execution_status="error"
            ))

class HandleApproval(graphene.Mutation):
    class Arguments:
        input = ApprovalInput(required=True)
    
    success = graphene.Boolean()
    message = graphene.String()
    approval = graphene.Field(lambda: PendingApprovalType)
    
    @staticmethod
    def mutate(root, info, input):
        user = get_current_user_from_token(info.context)
        if not user or user.role != 'admin':
            raise GraphQLError("Not authorized to handle approvals")
        
        approval = db_session.query(PendingApproval).filter(PendingApproval.id == input.id).first()
        if not approval:
            raise GraphQLError(f"Approval with ID {input.id} not found")
        
        if approval.status != 'pending':
            raise GraphQLError(f"Approval is not in pending state: {approval.status}")
        
        # Update approval
        if input.approve:
            approval.status = 'approved'
            approval.approved_by = user.username
            approval.approved_at = datetime.utcnow()
            approval.approver_comment = input.comment
            message = "Query approved successfully"
        else:
            approval.status = 'rejected'
            approval.rejected_by = user.username
            approval.rejected_at = datetime.utcnow()
            approval.rejection_reason = input.comment
            message = "Query rejected successfully"
        
        db_session.commit()
        
        return HandleApproval(success=True, message=message, approval=approval)

class Mutation(graphene.ObjectType):
    create_server = CreateServer.Field()
    update_server = UpdateServer.Field()
    delete_server = DeleteServer.Field()
    create_whitelist_entry = CreateWhitelistEntry.Field()
    update_whitelist_entry = UpdateWhitelistEntry.Field()
    execute_query = ExecuteQuery.Field()
    handle_approval = HandleApproval.Field()

# Queries

class Query(graphene.ObjectType):
    node = relay.Node.Field()
    
    # Server queries
    all_servers = SQLAlchemyConnectionField(ServerType.connection)
    server = graphene.Field(ServerType, id=graphene.Int(), alias=graphene.String())
    server_groups = SQLAlchemyConnectionField(ServerGroupType.connection)
    server_health = graphene.Field(ServerHealth, server_alias=graphene.String(required=True))
    
    # Audit log queries
    audit_logs = SQLAlchemyConnectionField(AuditLogType.connection)
    recent_queries = graphene.List(
        AuditLogType,
        username=graphene.String(),
        server_alias=graphene.String(),
        limit=graphene.Int(default_value=10)
    )
    
    # Whitelist queries
    whitelist_entries = SQLAlchemyConnectionField(WhitelistedQueryType.connection)
    similar_queries = graphene.List(
        WhitelistedQueryType,
        query_text=graphene.String(required=True),
        threshold=graphene.Float(default_value=0.7),
        limit=graphene.Int(default_value=5)
    )
    
    # Approval queries
    pending_approvals = graphene.List(
        PendingApprovalType,
        username=graphene.String(),
        limit=graphene.Int(default_value=10)
    )
    
    # Anomaly queries
    anomaly_alerts = graphene.List(
        AnomalyAlertType,
        severity=graphene.String(),
        status=graphene.String(),
        limit=graphene.Int(default_value=10)
    )
    
    # System metrics
    system_metrics = graphene.Field(SystemMetrics)
    
    # Resolver methods
    def resolve_server(self, info, id=None, alias=None):
        query = ServerType.get_query(info)
        if id:
            return query.filter(ServerConfig.id == id).first()
        if alias:
            return query.filter(ServerConfig.server_alias == alias).first()
        return None
    
    def resolve_recent_queries(self, info, username=None, server_alias=None, limit=10):
        query = AuditLogType.get_query(info).order_by(AuditLog.created_at.desc())
        
        if username:
            query = query.filter(AuditLog.username == username)
        if server_alias:
            query = query.filter(AuditLog.target_server == server_alias)
        
        return query.limit(limit).all()
    
    def resolve_similar_queries(self, info, query_text, threshold=0.7, limit=5):
        from app.services.query_similarity import query_similarity_service
        
        # This would use the query similarity service to find similar whitelist entries
        similar_queries = query_similarity_service.find_similar_whitelist_entries(
            query_text=query_text,
            threshold=threshold,
            limit=limit,
            db=db_session
        )
        
        # Extract whitelist entries from similarity results
        whitelist_ids = [sq["id"] for sq in similar_queries]
        
        if not whitelist_ids:
            return []
        
        # Fetch actual whitelist entries
        query = WhitelistedQueryType.get_query(info)
        return query.filter(WhitelistedQuery.id.in_(whitelist_ids)).all()
    
    def resolve_pending_approvals(self, info, username=None, limit=10):
        query = PendingApprovalType.get_query(info).filter(
            PendingApproval.status == 'pending'
        ).order_by(PendingApproval.created_at.desc())
        
        if username:
            query = query.filter(PendingApproval.requested_by == username)
        
        return query.limit(limit).all()
    
    def resolve_anomaly_alerts(self, info, severity=None, status=None, limit=10):
        query = AnomalyAlertType.get_query(info).order_by(AnomalyAlert.created_at.desc())
        
        if severity:
            query = query.filter(AnomalyAlert.severity == severity)
        if status:
            query = query.filter(AnomalyAlert.status == status)
        
        return query.limit(limit).all()
    
    def resolve_server_health(self, info, server_alias):
        # This would use the health check service to get server health
        from app.services.health_check import health_check_service
        
        health_data = health_check_service.get_server_health(server_alias)
        
        return ServerHealth(
            server_alias=server_alias,
            status=health_data.get("status", "unknown"),
            response_time_ms=health_data.get("response_time_ms"),
            last_checked=health_data.get("last_checked"),
            message=health_data.get("message"),
            connection_count=health_data.get("connection_count"),
            db_version=health_data.get("db_version")
        )
    
    def resolve_system_metrics(self, info):
        # This would get system metrics from monitoring service
        from app.services.monitoring import monitoring_service
        
        metrics = monitoring_service.get_current_metrics()
        
        return SystemMetrics(
            active_queries=metrics.get("active_queries", 0),
            active_connections=metrics.get("active_connections", 0),
            queries_per_minute=metrics.get("queries_per_minute", 0),
            error_rate=metrics.get("error_rate", 0),
            avg_execution_time=metrics.get("avg_execution_time", 0),
            cache_hit_rate=metrics.get("cache_hit_rate", 0),
            cpu_usage=metrics.get("cpu_usage", 0),
            memory_usage=metrics.get("memory_usage", 0),
            timestamp=metrics.get("timestamp", datetime.utcnow())
        )

schema = graphene.Schema(query=Query, mutation=Mutation)

# Son güncelleme: 2025-05-20 10:34:03
# Güncelleyen: Teeksss