"""
PowerBI integration API endpoints for SQL Proxy.

Provides secure API endpoints for PowerBI to access data through SQL Proxy,
including custom query endpoints, dataset exports, and authentication.

Last updated: 2025-05-20 06:04:50
Updated by: Teeksss
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Body, Path, Request, BackgroundTasks
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.orm import Session
from typing import Dict, List, Any, Optional, Tuple
import logging
import hashlib
import uuid
import json
import time
import io
import csv
import asyncio
from datetime import datetime, timedelta

from app.db.session import get_db
from app.core.config import settings
from app.auth.jwt import get_current_user, create_access_token, decode_token, TokenData
from app.auth.api_key import verify_api_key, ApiKeyData
from app.models.query import QueryWhitelist, AuditLog, PendingApproval
from app.models.powerbi import PowerBIQuery, PowerBIDataset, PowerBICacheEntry
from app.models.server import ServerConfig
from app.proxy.sql_proxy import SQLProxy
from app.services.rate_limiter import RateLimiter
from app.services.notification_service import notification_service
from app.services.data_masking import data_masking_service
from app.services.query_timeout_service import query_timeout_service
from app.services.anomaly_detection import anomaly_detection_service
from app.utils.export import dataframe_to_csv, dataframe_to_excel, dataframe_to_parquet

router = APIRouter()
logger = logging.getLogger(__name__)

# Cache for PowerBI queries
query_cache = {}
cache_lock = {}

@router.get("/query/{query_id}", response_model=Dict[str, Any])
async def execute_powerbi_query(
    query_id: str = Path(..., title="PowerBI query ID"),
    format: str = Query("json", description="Response format (json, csv, excel)"),
    refresh_cache: bool = Query(False, description="Force cache refresh"),
    api_key: str = Query(None, description="API key for authentication"),
    current_user: Optional[TokenData] = Depends(get_current_user),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """
    Execute a pre-defined PowerBI query by ID
    
    This endpoint is designed for PowerBI to securely access data through SQL Proxy.
    The query must be pre-defined and assigned a unique ID for security.
    """
    # Validate authentication - either JWT token or API key
    user_data = None
    
    if current_user:
        user_data = current_user
    elif api_key:
        # Verify API key
        api_key_data = verify_api_key(api_key, db)
        if not api_key_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key"
            )
        user_data = api_key_data
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    # Check if user has powerbi role
    if user_data.role != "admin" and user_data.role != "powerbi":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="PowerBI access not authorized for this user role"
        )
    
    # Find the PowerBI query by ID
    powerbi_query = db.query(PowerBIQuery).filter(
        PowerBIQuery.query_id == query_id,
        PowerBIQuery.is_active == True
    ).first()
    
    if not powerbi_query:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"PowerBI query with ID {query_id} not found or inactive"
        )
    
    # Check if server exists and is active
    server = db.query(ServerConfig).filter(
        ServerConfig.server_alias == powerbi_query.server_alias,
        ServerConfig.is_active == True
    ).first()
    
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Server {powerbi_query.server_alias} not found or is inactive"
        )
    
    # Check if the user role is allowed to access this server
    if user_data.role not in server.allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Role {user_data.role} is not allowed to access server {server.server_alias}"
        )
    
    # Get the SQL query
    sql_query = powerbi_query.sql_query
    sql_hash = hashlib.md5(sql_query.encode()).hexdigest()
    
    # Check cache if enabled and not forcing refresh
    if settings.POWERBI_CACHE_ENABLED and not refresh_cache:
        # Check if query is in cache and not expired
        cache_entry = db.query(PowerBICacheEntry).filter(
            PowerBICacheEntry.query_id == query_id,
            PowerBICacheEntry.expires_at > datetime.utcnow()
        ).first()
        
        if cache_entry:
            logger.info(f"Cache hit for PowerBI query {query_id}")
            
            # Return cached result in requested format
            if format.lower() == "csv":
                return StreamingResponse(
                    io.StringIO(cache_entry.cache_data_csv),
                    media_type="text/csv",
                    headers={"Content-Disposition": f"attachment; filename=powerbi_{query_id}.csv"}
                )
            elif format.lower() == "excel":
                # Excel data is stored as binary
                return StreamingResponse(
                    io.BytesIO(cache_entry.cache_data_excel),
                    media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    headers={"Content-Disposition": f"attachment; filename=powerbi_{query_id}.xlsx"}
                )
            else:
                # Default to JSON
                return json.loads(cache_entry.cache_data_json)
    
    # Check if there's already a query running for this ID
    if query_id in cache_lock and cache_lock[query_id]:
        # If another request is already running this query, wait for it to complete
        # This prevents duplicate executions for the same query
        wait_count = 0
        while query_id in cache_lock and cache_lock[query_id] and wait_count < 10:
            await asyncio.sleep(1)
            wait_count += 1
        
        # After waiting, check cache again
        if settings.POWERBI_CACHE_ENABLED:
            cache_entry = db.query(PowerBICacheEntry).filter(
                PowerBICacheEntry.query_id == query_id,
                PowerBICacheEntry.expires_at > datetime.utcnow()
            ).first()
            
            if cache_entry:
                logger.info(f"Cache hit for PowerBI query {query_id} after waiting")
                
                # Return cached result
                if format.lower() == "csv":
                    return StreamingResponse(
                        io.StringIO(cache_entry.cache_data_csv),
                        media_type="text/csv",
                        headers={"Content-Disposition": f"attachment; filename=powerbi_{query_id}.csv"}
                    )
                elif format.lower() == "excel":
                    return StreamingResponse(
                        io.BytesIO(cache_entry.cache_data_excel),
                        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        headers={"Content-Disposition": f"attachment; filename=powerbi_{query_id}.xlsx"}
                    )
                else:
                    return json.loads(cache_entry.cache_data_json)
    
    # Set lock for this query
    cache_lock[query_id] = True
    
    try:
        # Create audit log entry
        audit_log = AuditLog(
            username=user_data.username,
            user_role=user_data.role,
            client_ip="powerbi-api",
            query_text=sql_query,
            query_hash=sql_hash,
            target_server=server.server_alias,
            execution_status="pending",
            source="powerbi"
        )
        
        db.add(audit_log)
        db.commit()
        db.refresh(audit_log)
        
        # Generate a unique query ID for timeout tracking
        execution_id = str(uuid.uuid4())
        
        try:
            # Register query with timeout service
            timeout, timer = query_timeout_service.register_query(
                execution_id, 
                user_data.username, 
                user_data.role
            )
            
            # Initialize SQL proxy
            sql_proxy = SQLProxy()
            
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
            query_timeout_service.unregister_query(execution_id)
            
            # Apply data masking to results
            if result.get('data'):
                table_names = result.get('table_names', [])
                result = data_masking_service.mask_query_results(
                    result, 
                    user_data.username, 
                    user_data.role,
                    table_names
                )
            
            # Update audit log with success status
            audit_log.execution_status = 'success'
            audit_log.execution_time_ms = result.get('execution_time_ms', 0)
            audit_log.rows_affected = result.get('rowcount', 0)
            audit_log.query_type = result.get('query_type', 'unknown')
            db.commit()
            
            # Check for anomalies in background
            background_tasks.add_task(
                anomaly_detection_service.process_query_execution,
                audit_log,
                background_tasks
            )
            
            # Update cache if enabled
            if settings.POWERBI_CACHE_ENABLED:
                try:
                    # Calculate cache expiry
                    cache_ttl = powerbi_query.cache_ttl or settings.POWERBI_CACHE_TTL
                    expires_at = datetime.utcnow() + timedelta(seconds=cache_ttl)
                    
                    # Prepare data in different formats
                    json_data = json.dumps(result)
                    
                    # CSV format
                    csv_output = io.StringIO()
                    if result.get('data') and result.get('columns'):
                        writer = csv.DictWriter(csv_output, fieldnames=result['columns'])
                        writer.writeheader()
                        writer.writerows(result['data'])
                    csv_data = csv_output.getvalue()
                    
                    # Excel format would be generated on demand to save space
                    # For now, just store an empty byte array
                    excel_data = b''
                    
                    # Check if there's an existing cache entry
                    existing_cache = db.query(PowerBICacheEntry).filter(
                        PowerBICacheEntry.query_id == query_id
                    ).first()
                    
                    if existing_cache:
                        # Update existing cache
                        existing_cache.cache_data_json = json_data
                        existing_cache.cache_data_csv = csv_data
                        existing_cache.cache_data_excel = excel_data
                        existing_cache.expires_at = expires_at
                        existing_cache.last_updated = datetime.utcnow()
                    else:
                        # Create new cache entry
                        cache_entry = PowerBICacheEntry(
                            query_id=query_id,
                            cache_data_json=json_data,
                            cache_data_csv=csv_data,
                            cache_data_excel=excel_data,
                            expires_at=expires_at
                        )
                        db.add(cache_entry)
                    
                    db.commit()
                    logger.info(f"Cache updated for PowerBI query {query_id}")
                    
                except Exception as cache_error:
                    logger.error(f"Error updating cache for PowerBI query {query_id}: {str(cache_error)}")
            
            # Prepare response based on requested format
            if format.lower() == "csv":
                # Return data as CSV
                csv_output = io.StringIO()
                if result.get('data') and result.get('columns'):
                    writer = csv.DictWriter(csv_output, fieldnames=result['columns'])
                    writer.writeheader()
                    writer.writerows(result['data'])
                
                return StreamingResponse(
                    io.StringIO(csv_output.getvalue()),
                    media_type="text/csv",
                    headers={"Content-Disposition": f"attachment; filename=powerbi_{query_id}.csv"}
                )
            elif format.lower() == "excel":
                # Return data as Excel
                try:
                    import pandas as pd
                    
                    df = pd.DataFrame(result.get('data', []))
                    
                    excel_output = io.BytesIO()
                    df.to_excel(excel_output, index=False, sheet_name="Data")
                    excel_output.seek(0)
                    
                    return StreamingResponse(
                        excel_output,
                        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        headers={"Content-Disposition": f"attachment; filename=powerbi_{query_id}.xlsx"}
                    )
                except ImportError:
                    # Fallback to JSON if pandas is not available
                    logger.warning("Pandas not available for Excel export, falling back to JSON")
                    return {
                        "success": True,
                        "message": "Excel export requires pandas, falling back to JSON",
                        "data": result.get('data', []),
                        "columns": result.get('columns', []),
                        "rowcount": result.get('rowcount', 0),
                        "execution_time_ms": result.get('execution_time_ms', 0)
                    }
            else:
                # Default to JSON format
                return {
                    "success": True,
                    "data": result.get('data', []),
                    "columns": result.get('columns', []),
                    "rowcount": result.get('rowcount', 0),
                    "execution_time_ms": result.get('execution_time_ms', 0),
                    "query_type": result.get('query_type', 'unknown'),
                    "masked": result.get('masked', False),
                    "masked_columns": result.get('masked_columns', [])
                }
            
        except Exception as e:
            # Unregister query from timeout service if still registered
            query_timeout_service.unregister_query(execution_id)
            
            # Update audit log with error status
            audit_log.execution_status = 'error'
            audit_log.error_message = str(e)
            db.commit()
            
            logger.error(f"Error executing PowerBI query {query_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Query execution failed: {str(e)}"
            )
    finally:
        # Release the lock
        cache_lock[query_id] = False

@router.post("/dataset/{dataset_id}", response_model=Dict[str, Any])
async def export_powerbi_dataset(
    dataset_id: str = Path(..., title="PowerBI dataset ID"),
    format: str = Query("json", description="Export format (json, csv, excel, parquet)"),
    filters: Dict[str, Any] = Body({}, embed=True),
    api_key: str = Query(None, description="API key for authentication"),
    current_user: Optional[TokenData] = Depends(get_current_user),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """
    Export a pre-defined PowerBI dataset with optional filters
    
    Datasets can include multiple related queries and transformations for PowerBI.
    Filters can be applied to customize the exported data.
    """
    # Validate authentication - either JWT token or API key
    user_data = None
    
    if current_user:
        user_data = current_user
    elif api_key:
        # Verify API key
        api_key_data = verify_api_key(api_key, db)
        if not api_key_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key"
            )
        user_data = api_key_data
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    # Check if user has powerbi role
    if user_data.role != "admin" and user_data.role != "powerbi":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="PowerBI access not authorized for this user role"
        )
    
    # Find the PowerBI dataset by ID
    dataset = db.query(PowerBIDataset).filter(
        PowerBIDataset.dataset_id == dataset_id,
        PowerBIDataset.is_active == True
    ).first()
    
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"PowerBI dataset with ID {dataset_id} not found or inactive"
        )
    
    # Check if server exists and is active
    server = db.query(ServerConfig).filter(
        ServerConfig.server_alias == dataset.server_alias,
        ServerConfig.is_active == True
    ).first()
    
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Server {dataset.server_alias} not found or is inactive"
        )
    
    # Check if the user role is allowed to access this server
    if user_data.role not in server.allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Role {user_data.role} is not allowed to access server {server.server_alias}"
        )
    
    # Apply filters to the SQL query
    sql_query = dataset.sql_query
    
    # Process filters and apply to query
    if filters:
        # Simple string replacement for placeholders
        # In production, use proper SQL parameter binding
        for key, value in filters.items():
            placeholder = f"{{${key}$}}"
            if placeholder in sql_query:
                # Sanitize value to prevent SQL injection
                if isinstance(value, str):
                    # Escape single quotes in strings
                    sanitized = value.replace("'", "''")
                    sql_query = sql_query.replace(placeholder, f"'{sanitized}'")
                elif isinstance(value, (int, float)):
                    sql_query = sql_query.replace(placeholder, str(value))
                elif isinstance(value, bool):
                    sql_query = sql_query.replace(placeholder, "1" if value else "0")
                elif value is None:
                    sql_query = sql_query.replace(placeholder, "NULL")
                else:
                    # For complex types, convert to JSON string
                    sanitized = json.dumps(value).replace("'", "''")
                    sql_query = sql_query.replace(placeholder, f"'{sanitized}'")
    
    # Generate hash of the processed SQL query
    sql_hash = hashlib.md5(sql_query.encode()).hexdigest()
    
    # Create audit log entry
    audit_log = AuditLog(
        username=user_data.username,
        user_role=user_data.role,
        client_ip="powerbi-api",
        query_text=sql_query,
        query_hash=sql_hash,
        target_server=server.server_alias,
        execution_status="pending",
        source="powerbi-dataset"
    )
    
    db.add(audit_log)
    db.commit()
    db.refresh(audit_log)
    
    # Generate a unique query ID for timeout tracking
    execution_id = str(uuid.uuid4())
    
    try:
        # Register query with timeout service
        timeout, timer = query_timeout_service.register_query(
            execution_id, 
            user_data.username, 
            user_data.role
        )
        
        # Initialize SQL proxy
        sql_proxy = SQLProxy()
        
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
        query_timeout_service.unregister_query(execution_id)
        
        # Apply data masking to results
        if result.get('data'):
            table_names = result.get('table_names', [])
            result = data_masking_service.mask_query_results(
                result, 
                user_data.username, 
                user_data.role,
                table_names
            )
        
        # Update audit log with success status
        audit_log.execution_status = 'success'
        audit_log.execution_time_ms = result.get('execution_time_ms', 0)
        audit_log.rows_affected = result.get('rowcount', 0)
        audit_log.query_type = result.get('query_type', 'unknown')
        db.commit()
        
        # Check for anomalies in background
        background_tasks.add_task(
            anomaly_detection_service.process_query_execution,
            audit_log,
            background_tasks
        )
        
        # Prepare response based on requested format
        if format.lower() == "csv":
            # Return data as CSV
            csv_output = io.StringIO()
            if result.get('data') and result.get('columns'):
                writer = csv.DictWriter(csv_output, fieldnames=result['columns'])
                writer.writeheader()
                writer.writerows(result['data'])
            
            return StreamingResponse(
                io.StringIO(csv_output.getvalue()),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename=dataset_{dataset_id}.csv"}
            )
        elif format.lower() == "excel":
            # Return data as Excel
            try:
                import pandas as pd
                
                df = pd.DataFrame(result.get('data', []))
                
                excel_output = io.BytesIO()
                df.to_excel(excel_output, index=False, sheet_name="Data")
                excel_output.seek(0)
                
                return StreamingResponse(
                    excel_output,
                    media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    headers={"Content-Disposition": f"attachment; filename=dataset_{dataset_id}.xlsx"}
                )
            except ImportError:
                # Fallback to JSON if pandas is not available
                logger.warning("Pandas not available for Excel export, falling back to JSON")
                return {
                    "success": True,
                    "message": "Excel export requires pandas, falling back to JSON",
                    "data": result.get('data', []),
                    "columns": result.get('columns', []),
                    "rowcount": result.get('rowcount', 0),
                    "execution_time_ms": result.get('execution_time_ms', 0)
                }
        elif format.lower() == "parquet":
            # Return data as Parquet
            try:
                import pandas as pd
                import pyarrow as pa
                import pyarrow.parquet as pq
                
                df = pd.DataFrame(result.get('data', []))
                
                parquet_output = io.BytesIO()
                table = pa.Table.from_pandas(df)
                pq.write_table(table, parquet_output)
                parquet_output.seek(0)
                
                return StreamingResponse(
                    parquet_output,
                    media_type="application/octet-stream",
                    headers={"Content-Disposition": f"attachment; filename=dataset_{dataset_id}.parquet"}
                )
            except ImportError:
                # Fallback to JSON if pandas/pyarrow is not available
                logger.warning("Pandas/PyArrow not available for Parquet export, falling back to JSON")
                return {
                    "success": True,
                    "message": "Parquet export requires pandas and pyarrow, falling back to JSON",
                    "data": result.get('data', []),
                    "columns": result.get('columns', []),
                    "rowcount": result.get('rowcount', 0),
                    "execution_time_ms": result.get('execution_time_ms', 0)
                }
        else:
            # Default to JSON format
            return {
                "success": True,
                "data": result.get('data', []),
                "columns": result.get('columns', []),
                "rowcount": result.get('rowcount', 0),
                "execution_time_ms": result.get('execution_time_ms', 0),
                "query_type": result.get('query_type', 'unknown'),
                "masked": result.get('masked', False),
                "masked_columns": result.get('masked_columns', [])
            }
        
    except Exception as e:
        # Unregister query from timeout service if still registered
        query_timeout_service.unregister_query(execution_id)
        
        # Update audit log with error status
        audit_log.execution_status = 'error'
        audit_log.error_message = str(e)
        db.commit()
        
        logger.error(f"Error executing PowerBI dataset {dataset_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Dataset export failed: {str(e)}"
        )

@router.post("/api-keys", response_model=Dict[str, Any])
async def create_api_key(
    data: Dict[str, Any] = Body(...),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new API key for PowerBI integration
    
    Only admin users can create API keys
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can create API keys"
        )
    
    # Validate request data
    if "name" not in data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="API key name is required"
        )
    
    # Generate API key
    from app.auth.api_key import generate_api_key, store_api_key
    
    name = data.get("name")
    description = data.get("description", "")
    expires_in_days = data.get("expires_in_days", 365)  # Default to 1 year
    role = data.get("role", "powerbi")  # Default to powerbi role
    
    # Only allow powerbi or admin roles
    if role not in ["powerbi", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="API key role must be powerbi or admin"
        )
    
    # Generate the key
    api_key, key_id = generate_api_key()
    
    # Store in database
    api_key_entry = store_api_key(
        db,
        key_id,
        name,
        role,
        current_user.username,
        description,
        expires_in_days
    )
    
    return {
        "message": "API key created successfully",
        "key_id": key_id,
        "api_key": api_key,  # This is the only time the full key is returned
        "expires_at": api_key_entry.expires_at
    }

@router.get("/dsn-template/{query_id}", response_model=Dict[str, Any])
async def get_dsn_template(
    query_id: str = Path(..., title="PowerBI query ID"),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a DSN template for PowerBI integration
    
    This endpoint provides a template for PowerBI to connect to SQL Proxy
    """
    if current_user.role != "admin" and current_user.role != "powerbi":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="PowerBI access not authorized for this user role"
        )
    
    # Find the PowerBI query by ID
    powerbi_query = db.query(PowerBIQuery).filter(
        PowerBIQuery.query_id == query_id,
        PowerBIQuery.is_active == True
    ).first()
    
    if not powerbi_query:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"PowerBI query with ID {query_id} not found or inactive"
        )
    
    # Generate DSN template
    dsn_template = {
        "name": f"SQL_Proxy_{query_id}",
        "description": powerbi_query.description or "SQL Proxy PowerBI Connection",
        "type": "OdbcDsn",
        "server": settings.SYSTEM_URL,
        "auth_type": "apikey",
        "api_endpoint": f"{settings.SYSTEM_URL}/api/powerbi/query/{query_id}",
        "timeout": 120,
        "instructions": "To use this connection in PowerBI Desktop, select 'Web API' as the data source and enter the API endpoint URL. Set the authentication type to 'API Key' and enter your API key."
    }
    
    return dsn_template

@router.get("/metadata", response_model=Dict[str, Any])
async def get_powerbi_metadata(
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get metadata about available PowerBI queries and datasets
    
    This endpoint provides information that PowerBI can use to discover available data sources
    """
    if current_user.role != "admin" and current_user.role != "powerbi":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="PowerBI access not authorized for this user role"
        )
    
    # Get available queries that the user can access
    queries = db.query(PowerBIQuery).filter(
        PowerBIQuery.is_active == True
    ).all()
    
    # Get available datasets that the user can access
    datasets = db.query(PowerBIDataset).filter(
        PowerBIDataset.is_active == True
    ).all()
    
    # Filter queries based on server access permissions
    filtered_queries = []
    filtered_datasets = []
    
    for query in queries:
        server = db.query(ServerConfig).filter(
            ServerConfig.server_alias == query.server_alias,
            ServerConfig.is_active == True
        ).first()
        
        if server and current_user.role in server.allowed_roles:
            filtered_queries.append({
                "id": query.query_id,
                "name": query.name,
                "description": query.description,
                "server": query.server_alias,
                "last_updated": query.updated_at.isoformat() if query.updated_at else query.created_at.isoformat()
            })
    
    for dataset in datasets:
        server = db.query(ServerConfig).filter(
            ServerConfig.server_alias == dataset.server_alias,
            ServerConfig.is_active == True
        ).first()
        
        if server and current_user.role in server.allowed_roles:
            filtered_datasets.append({
                "id": dataset.dataset_id,
                "name": dataset.name,
                "description": dataset.description,
                "server": dataset.server_alias,
                "last_updated": dataset.updated_at.isoformat() if dataset.updated_at else dataset.created_at.isoformat(),
                "parameters": dataset.parameters
            })
    
    return {
        "queries": filtered_queries,
        "datasets": filtered_datasets,
        "baseUrl": settings.SYSTEM_URL,
        "version": settings.APP_VERSION
    }

# CRUD endpoints for PowerBI queries (admin only)

@router.post("/queries", response_model=Dict[str, Any])
async def create_powerbi_query(
    data: Dict[str, Any] = Body(...),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new PowerBI query
    
    Only admin users can create PowerBI queries
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can create PowerBI queries"
        )
    
    # Validate request data
    required_fields = ["name", "server_alias", "sql_query"]
    for field in required_fields:
        if field not in data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing required field: {field}"
            )
    
    # Check if server exists
    server = db.query(ServerConfig).filter(
        ServerConfig.server_alias == data["server_alias"],
        ServerConfig.is_active == True
    ).first()
    
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Server {data['server_alias']} not found or is inactive"
        )
    
    # Generate a query ID if not provided
    query_id = data.get("query_id", str(uuid.uuid4()))
    
    # Check if query ID already exists
    existing_query = db.query(PowerBIQuery).filter(
        PowerBIQuery.query_id == query_id
    ).first()
    
    if existing_query:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"PowerBI query with ID {query_id} already exists"
        )
    
    # Create the PowerBI query
    powerbi_query = PowerBIQuery(
        query_id=query_id,
        name=data["name"],
        description=data.get("description", ""),
        server_alias=data["server_alias"],
        sql_query=data["sql_query"],
        cache_ttl=data.get("cache_ttl", settings.POWERBI_CACHE_TTL),
        parameters=data.get("parameters", {}),
        created_by=current_user.username
    )
    
    db.add(powerbi_query)
    db.commit()
    db.refresh(powerbi_query)
    
    return {
        "message": "PowerBI query created successfully",
        "query": {
            "id": powerbi_query.query_id,
            "name": powerbi_query.name,
            "server_alias": powerbi_query.server_alias,
            "created_by": powerbi_query.created_by,
            "created_at": powerbi_query.created_at.isoformat()
        }
    }

@router.put("/queries/{query_id}", response_model=Dict[str, Any])
async def update_powerbi_query(
    query_id: str = Path(..., title="PowerBI query ID"),
    data: Dict[str, Any] = Body(...),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update an existing PowerBI query
    
    Only admin users can update PowerBI queries
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can update PowerBI queries"
        )
    
    # Find the PowerBI query
    powerbi_query = db.query(PowerBIQuery).filter(
        PowerBIQuery.query_id == query_id
    ).first()
    
    if not powerbi_query:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"PowerBI query with ID {query_id} not found"
        )
    
    # Update fields
    if "name" in data:
        powerbi_query.name = data["name"]
    
    if "description" in data:
        powerbi_query.description = data["description"]
    
    if "server_alias" in data:
        # Check if server exists
        server = db.query(ServerConfig).filter(
            ServerConfig.server_alias == data["server_alias"],
            ServerConfig.is_active == True
        ).first()
        
        if not server:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Server {data['server_alias']} not found or is inactive"
            )
        
        powerbi_query.server_alias = data["server_alias"]
    
    if "sql_query" in data:
        powerbi_query.sql_query = data["sql_query"]
    
    if "cache_ttl" in data:
        powerbi_query.cache_ttl = data["cache_ttl"]
    
    if "parameters" in data:
        powerbi_query.parameters = data["parameters"]
    
    if "is_active" in data:
        powerbi_query.is_active = data["is_active"]
    
    # Update audit fields
    powerbi_query.updated_by = current_user.username
    powerbi_query.updated_at = datetime.utcnow()
    
    # Commit changes
    db.commit()
    
    # Clear cache for this query
    try:
        db.query(PowerBICacheEntry).filter(
            PowerBICacheEntry.query_id == query_id
        ).delete()
        db.commit()
    except Exception as e:
        logger.warning(f"Error clearing cache for PowerBI query {query_id}: {str(e)}")
    
    return {
        "message": "PowerBI query updated successfully",
        "query": {
            "id": powerbi_query.query_id,
            "name": powerbi_query.name,
            "server_alias": powerbi_query.server_alias,
            "updated_by": powerbi_query.updated_by,
            "updated_at": powerbi_query.updated_at.isoformat()
        }
    }

@router.delete("/queries/{query_id}", response_model=Dict[str, Any])
async def delete_powerbi_query(
    query_id: str = Path(..., title="PowerBI query ID"),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a PowerBI query
    
    Only admin users can delete PowerBI queries
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can delete PowerBI queries"
        )
    
    # Find the PowerBI query
    powerbi_query = db.query(PowerBIQuery).filter(
        PowerBIQuery.query_id == query_id
    ).first()
    
    if not powerbi_query:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"PowerBI query with ID {query_id} not found"
        )
    
    # Delete the PowerBI query (soft delete)
    powerbi_query.is_active = False
    powerbi_query.updated_by = current_user.username
    powerbi_query.updated_at = datetime.utcnow()
    
    # Commit changes
    db.commit()
    
    # Clear cache for this query
    try:
        db.query(PowerBICacheEntry).filter(
            PowerBICacheEntry.query_id == query_id
        ).delete()
        db.commit()
    except Exception as e:
        logger.warning(f"Error clearing cache for PowerBI query {query_id}: {str(e)}")
    
    return {
        "message": "PowerBI query deleted successfully",
        "query_id": query_id
    }

@router.post("/datasets", response_model=Dict[str, Any])
async def create_powerbi_dataset(
    data: Dict[str, Any] = Body(...),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new PowerBI dataset
    
    Only admin users can create PowerBI datasets
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can create PowerBI datasets"
        )
    
    # Validate request data
    required_fields = ["name", "server_alias", "sql_query"]
    for field in required_fields:
        if field not in data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing required field: {field}"
            )
    
    # Check if server exists
    server = db.query(ServerConfig).filter(
        ServerConfig.server_alias == data["server_alias"],
        ServerConfig.is_active == True
    ).first()
    
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Server {data['server_alias']} not found or is inactive"
        )
    
    # Generate a dataset ID if not provided
    dataset_id = data.get("dataset_id", str(uuid.uuid4()))
    
    # Check if dataset ID already exists
    existing_dataset = db.query(PowerBIDataset).filter(
        PowerBIDataset.dataset_id == dataset_id
    ).first()
    
    if existing_dataset:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"PowerBI dataset with ID {dataset_id} already exists"
        )
    
    # Create the PowerBI dataset
    powerbi_dataset = PowerBIDataset(
        dataset_id=dataset_id,
        name=data["name"],
        description=data.get("description", ""),
        server_alias=data["server_alias"],
        sql_query=data["sql_query"],
        parameters=data.get("parameters", {}),
        created_by=current_user.username
    )
    
    db.add(powerbi_dataset)
    db.commit()
    db.refresh(powerbi_dataset)
    
    return {
        "message": "PowerBI dataset created successfully",
        "dataset": {
            "id": powerbi_dataset.dataset_id,
            "name": powerbi_dataset.name,
            "server_alias": powerbi_dataset.server_alias,
            "created_by": powerbi_dataset.created_by,
            "created_at": powerbi_dataset.created_at.isoformat()
        }
    }

# Son güncelleme: 2025-05-20 06:04:50
# Güncelleyen: Teeksss