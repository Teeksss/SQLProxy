from fastapi import APIRouter, Depends, HTTPException, Request, status, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Dict, Optional, List
import time

from app.auth.jwt import get_current_user, TokenData
from app.core.config import settings
from app.db.session import get_db
from app.models.query import AuditLog, QueryWhitelist, ServerConfig
from app.query.validator import QueryValidator
from app.query.parser import SQLAnalyzer
from app.proxy.sql_proxy import SQLProxy
from app.services.rate_limiter import RateLimiter

router = APIRouter()

# Initialize dependencies
sql_analyzer = SQLAnalyzer()
query_validator = QueryValidator(sql_analyzer)

@router.post("/execute", response_model=Dict)
async def execute_query(
    request: Request,
    query_data: Dict,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Execute a SQL query through the proxy
    """
    server_alias = query_data.get("server_alias")
    sql_query = query_data.get("sql_query")
    
    if not server_alias or not sql_query:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Both server_alias and sql_query are required"
        )
    
    # Check if server exists and user has permission
    server = db.query(ServerConfig).filter(
        ServerConfig.server_alias == server_alias,
        ServerConfig.is_active == True
    ).first()
    
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Server {server_alias} not found or is inactive"
        )
    
    # Check if user role is allowed for this server
    if current_user.role not in server.allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Your role ({current_user.role}) does not have permission to query this server"
        )
    
    # Validate query against whitelist and permissions
    validation_result = query_validator.validate_query(
        sql=sql_query,
        user_role=current_user.role,
        target_server=server_alias,
        db=db,
        auto_approve=server.auto_approve_queries if hasattr(server, 'auto_approve_queries') else False
    )
    
    # Create audit log entry
    audit_log = AuditLog(
        username=current_user.username,
        user_role=current_user.role,
        client_ip=request.client.host,
        query_text=sql_query,
        query_hash=query_validator.hash_query(sql_query),
        whitelist_id=validation_result.get('whitelist_id'),
        target_server=server_alias,
        execution_status="pending"
    )
    
    db.add(audit_log)
    db.commit()
    db.refresh(audit_log)
    
    # If query is not approved, return early with error
    if not validation_result['is_approved']:
        audit_log.execution_status = 'rejected'
        audit_log.error_message = validation_result['error']
        db.commit()
        
        return {
            "success": False,
            "message": validation_result['error'],
            "status": validation_result['status'],
            "audit_id": audit_log.id,
            "analysis": validation_result['analysis']
        }
    
    # Execute the query through the SQL proxy
    start_time = time.time()
    try:
        # Initialize SQL proxy
        sql_proxy = SQLProxy()
        
        # Connect to the server
        connection = sql_proxy.connect_to_server(
            host=server.server_host,
            port=server.server_port,
            database=server.database_name,
            user=settings.SQL_PROXY_USERNAME,
            password=settings.SQL_PROXY_PASSWORD
        )
        
        # Execute the query
        result = sql_proxy.execute_query(connection, sql_query)
        
        # Calculate execution time
        execution_time_ms = int((time.time() - start_time) * 1000)
        
        # Update audit log with success status
        audit_log.execution_status = 'success'
        audit_log.execution_time_ms = execution_time_ms
        audit_log.rows_affected = result.get('rowcount', 0)
        db.commit()
        
        return {
            "success": True,
            "message": "Query executed successfully",
            "data": result.get('data'),
            "columns": result.get('columns'),
            "rowcount": result.get('rowcount'),
            "execution_time_ms": execution_time_ms,
            "audit_id": audit_log.id
        }
        
    except Exception as e:
        # Calculate execution time even on error
        execution_time_ms = int((time.time() - start_time) * 1000)
        
        # Update audit log with error status
        audit_log.execution_status = 'error'
        audit_log.execution_time_ms = execution_time_ms
        audit_log.error_message = str(e)
        db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query execution error: {str(e)}"
        )

@router.get("/servers", response_model=List[Dict])
async def get_available_servers(
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get list of available servers for the current user
    """
    servers = db.query(ServerConfig).filter(
        ServerConfig.is_active == True,
        ServerConfig.allowed_roles.contains([current_user.role])
    ).all()
    
    return [
        {
            "server_alias": server.server_alias,
            "description": server.description,
            "database_name": server.database_name
        }
        for server in servers
    ]

@router.post("/analyze", response_model=Dict)
async def analyze_query(
    query_data: Dict,
    current_user: TokenData = Depends(get_current_user)
):
    """
    Analyze a SQL query without executing it
    """
    sql_query = query_data.get("sql_query")
    
    if not sql_query:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="sql_query is required"
        )
    
    # Analyze the query
    analysis = sql_analyzer.parse_query(sql_query)
    
    return {
        "success": True,
        "analysis": analysis
    }