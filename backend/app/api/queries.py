"""
Query API endpoints for SQL Proxy.

Last updated: 2025-05-16 13:44:50
Updated by: Teeksss
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Body, Path
from sqlalchemy.orm import Session
from typing import Dict, List, Any, Optional
import logging
import hashlib
import uuid
from datetime import datetime

from app.db.session import get_db
from app.auth.jwt import get_current_user, TokenData
from app.models.query import PendingApproval, QueryWhitelist, AuditLog
from app.models.server import ServerConfig
from app.proxy.sql_proxy import SQLProxy
from app.services.rate_limiter import RateLimiter
from app.services.notification_service import notification_service
from app.services.data_masking import data_masking_service
from app.services.query_timeout_service import query_timeout_service

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/execute", response_model=Dict[str, Any])
async def execute_query(
    query_data: Dict[str, Any] = Body(...),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Execute SQL query on target server
    
    If query is not in whitelist, it will be sent for approval first
    """
    # Check for required fields
    if "server_alias" not in query_data or "sql_query" not in query_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="server_alias and sql_query are required"
        )
    
    server_alias = query_data["server_alias"]
    sql_query = query_data["sql_query"]
    
    # Check if server exists and is active
    server = db.query(ServerConfig).filter(
        ServerConfig.server_alias == server_alias,
        ServerConfig.is_active == True
    ).first()
    
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Server {server_alias} not found or is inactive"
        )
    
    # Check if user role is allowed to access this server
    if current_user.role not in server.allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Role {current_user.role} is not allowed to access server {server_alias}"
        )
    
    # Generate query hash for identification
    query_hash = hashlib.md5(sql_query.encode()).hexdigest()
    
    # Check if query is in whitelist
    whitelist_query = db.query(QueryWhitelist).filter(
        QueryWhitelist.query_hash == query_hash
    ).first()
    
    # Check if query is already pending approval
    pending_approval = db.query(PendingApproval).filter(
        PendingApproval.query_hash == query_hash,
        PendingApproval.username == current_user.username,
        PendingApproval.target_server == server_alias
    ).first()
    
    if pending_approval:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This query is pending approval"
        )
    
    # Initialize SQL proxy
    sql_proxy = SQLProxy()
    
    if whitelist_query:
        # Check if this server is allowed for this whitelist query
        if whitelist_query.server_restrictions and server_alias not in whitelist_query.server_restrictions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This query is not allowed on server {server_alias}"
            )
        
        # Query is in whitelist, execute it
        # Create audit log entry
        audit_log = AuditLog(
            username=current_user.username,
            user_role=current_user.role,
            client_ip=query_data.get("client_ip", "unknown"),
            query_text=sql_query,
            query_hash=query_hash,
            whitelist_id=whitelist_query.id,
            target_server=server_alias,
            execution_status="pending"
        )
        
        db.add(audit_log)
        db.commit()
        db.refresh(audit_log)
        
        # Generate a unique query ID for timeout tracking
        query_id = str(uuid.uuid4())
        
        try:
            # Register query with timeout service
            timeout, timer = query_timeout_service.register_query(
                query_id, 
                current_user.username, 
                current_user.role
            )
            
            # Connect to the server
            connection = sql_proxy.connect_to_server(
                host=server.server_host,
                port=server.server_port,
                database=server.database_name,
                user=server.db_username or "proxy_user",
                password=server.db_password or "proxy_password",
                db_type=server.db_type or "mssql"
            )
            
            # Execute the query
            result = sql_proxy.execute_query(connection, sql_query)
            
            # Unregister query from timeout service
            query_timeout_service.unregister_query(query_id)
            
            # Apply data masking to results
            if result.get('data'):
                table_names = result.get('table_names', [])  # This would be extracted during query execution
                result = data_masking_service.mask_query_results(
                    result, 
                    current_user.username, 
                    current_user.role,
                    table_names
                )
            
            # Update audit log with success status
            audit_log.execution_status = 'success'
            audit_log.execution_time_ms = result.get('execution_time_ms', 0)
            audit_log.rows_affected = result.get('rowcount', 0)
            audit_log.query_type = result.get('query_type', 'unknown')
            db.commit()
            
            return {
                "success": True,
                "message": "Query executed successfully",
                "data": result.get('data', []),
                "columns": result.get('columns', []),
                "rowcount": result.get('rowcount', 0),
                "execution_time_ms": result.get('execution_time_ms', 0),
                "query_type": result.get('query_type', 'unknown'),
                "audit_id": audit_log.id,
                "masked": result.get('masked', False),
                "masked_columns": result.get('masked_columns', [])
            }
            
        except Exception as e:
            # Unregister query from timeout service if still registered
            query_timeout_service.unregister_query(query_id)
            
            # Update audit log with error status
            audit_log.execution_status = 'error'
            audit_log.error_message = str(e)
            db.commit()
            
            logger.error(f"Query execution error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Query execution failed: {str(e)}"
            )
    else:
        # Query is not in whitelist, create pending approval
        if current_user.role != "admin":
            # Analyze query for risk
            try:
                # Parse query using SQL Proxy SQL analyzer
                query_metadata = sql_proxy.analyze_query(sql_query)
                query_type = query_metadata.get('query_type', 'unknown')
                risk_level = query_metadata.get('risk_level', 'high')
                sensitive_operations = query_metadata.get('sensitive_operations', [])
            except Exception as e:
                logger.error(f"Error analyzing query: {str(e)}")
                query_type = "unknown"
                risk_level = "high"
                sensitive_operations = ["Unknown - analysis failed"]
            
            # Create pending approval
            approval = PendingApproval(
                username=current_user.username,
                user_role=current_user.role,
                client_ip=query_data.get("client_ip", "unknown"),
                sql_query=sql_query,
                query_hash=query_hash,
                target_server=server_alias,
                created_at=datetime.utcnow(),
                risk_level=risk_level,
                sensitive_operations=sensitive_operations,
                query_type=query_type
            )
            
            db.add(approval)
            db.commit()
            db.refresh(approval)
            
            # Create audit log entry
            audit_log = AuditLog(
                username=current_user.username,
                user_role=current_user.role,
                client_ip=query_data.get("client_ip", "unknown"),
                query_text=sql_query,
                query_hash=query_hash,
                target_server=server_alias,
                execution_status="pending",
                query_type=query_type
            )
            
            db.add(audit_log)
            db.commit()
            
            # Notify admins about the pending approval
            try:
                # Get all admin users
                admins = db.query(User).filter(User.role == "admin").all()
                if admins:
                    notification_service.send_approval_request(approval, admins)
            except Exception as e:
                logger.error(f"Failed to send approval notifications: {str(e)}")
            
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Query requires approval from administrator"
            )
        else:
            # Admin users can auto-approve their queries
            # Create audit log entry
            audit_log = AuditLog(
                username=current_user.username,
                user_role=current_user.role,
                client_ip=query_data.get("client_ip", "unknown"),
                query_text=sql_query,
                query_hash=query_hash,
                target_server=server_alias,
                execution_status="pending"
            )
            
            db.add(audit_log)
            db.commit()
            db.refresh(audit_log)
            
            # Generate a unique query ID for timeout tracking
            query_id = str(uuid.uuid4())
            
            try:
                # Register query with timeout service
                timeout, timer = query_timeout_service.register_query(
                    query_id, 
                    current_user.username, 
                    current_user.role
                )
                
                # Connect to the server
                connection = sql_proxy.connect_to_server(
                    host=server.server_host,
                    port=server.server_port,
                    database=server.database_name,
                    user=server.db_username or "proxy_user",
                    password=server.db_password or "proxy_password",
                    db_type=server.db_type or "mssql"
                )
                
                # Execute the query
                result = sql_proxy.execute_query(connection, sql_query)
                
                # Unregister query from timeout service
                query_timeout_service.unregister_query(query_id)
                
                # Apply data masking to results (admins are typically exempt, but included for completeness)
                if result.get('data'):
                    table_names = result.get('table_names', [])
                    result = data_masking_service.mask_query_results(
                        result, 
                        current_user.username, 
                        current_user.role,
                        table_names
                    )
                
                # Add to whitelist automatically for admin users
                whitelist_entry = QueryWhitelist(
                    sql_query=sql_query,
                    query_hash=query_hash,
                    query_type=result.get('query_type', 'unknown'),
                    approved_by=current_user.username,
                    approved_at=datetime.utcnow()
                )
                
                db.add(whitelist_entry)
                db.commit()
                db.refresh(whitelist_entry)
                
                # Update audit log with success status
                audit_log.execution_status = 'success'
                audit_log.execution_time_ms = result.get('execution_time_ms', 0)
                audit_log.rows_affected = result.get('rowcount', 0)
                audit_log.query_type = result.get('query_type', 'unknown')
                audit_log.whitelist_id = whitelist_entry.id
                db.commit()
                
                return {
                    "success": True,
                    "message": "Query executed successfully and added to whitelist",
                    "data": result.get('data', []),
                    "columns": result.get('columns', []),
                    "rowcount": result.get('rowcount', 0),
                    "execution_time_ms": result.get('execution_time_ms', 0),
                    "query_type": result.get('query_type', 'unknown'),
                    "audit_id": audit_log.id,
                    "whitelist_id": whitelist_entry.id,
                    "masked": result.get('masked', False),
                    "masked_columns": result.get('masked_columns', [])
                }
                
            except Exception as e:
                # Unregister query from timeout service if still registered
                query_timeout_service.unregister_query(query_id)
                
                # Update audit log with error status
                audit_log.execution_status = 'error'
                audit_log.error_message = str(e)
                db.commit()
                
                logger.error(f"Query execution error: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Query execution failed: {str(e)}"
                )

@router.get("/history", response_model=Dict[str, Any])
async def get_query_history(
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    server: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get query execution history for the current user
    
    Can be filtered by server, status, and date range
    """
    query = db.query(AuditLog).filter(AuditLog.username == current_user.username)
    
    # Apply filters
    if server:
        query = query.filter(AuditLog.target_server == server)
    
    if status:
        query = query.filter(AuditLog.execution_status == status)
    
    if date_from:
        try:
            from_date = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
            query = query.filter(AuditLog.created_at >= from_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date_from format. Use ISO format (YYYY-MM-DDTHH:MM:SS)"
            )
    
    if date_to:
        try:
            to_date = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
            query = query.filter(AuditLog.created_at <= to_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date_to format. Use ISO format (YYYY-MM-DDTHH:MM:SS)"
            )
    
    # Count total items for pagination
    total = query.count()
    
    # Apply pagination
    query = query.order_by(AuditLog.created_at.desc()).offset((page - 1) * limit).limit(limit)
    
    # Execute query
    history = query.all()
    
    return {
        "total": total,
        "page": page,
        "limit": limit,
        "queries": history
    }

# Son güncelleme: 2025-05-16 13:44:50
# Güncelleyen: Teeksss