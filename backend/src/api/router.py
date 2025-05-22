from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from datetime import datetime
from .models import (
    QueryRequest,
    QueryResponse,
    ServerConfig,
    SessionInfo,
    AnalyticsData
)
from .dependencies import (
    get_current_user,
    get_query_manager,
    get_server_manager,
    get_analytics_manager
)

router = APIRouter()

@router.post("/query/execute")
async def execute_query(
    request: QueryRequest,
    current_user = Depends(get_current_user),
    query_manager = Depends(get_query_manager)
):
    """Query execution endpoint."""
    try:
        # Permission check
        if not await query_manager.check_permissions(
            current_user, request
        ):
            raise HTTPException(403, "Permission denied")
            
        # Execute query
        result = await query_manager.execute_query(
            request.query,
            request.server_id,
            current_user
        )
        
        return QueryResponse(
            success=True,
            results=result.data,
            execution_time=result.execution_time,
            affected_rows=result.affected_rows
        )
        
    except Exception as e:
        return QueryResponse(
            success=False,
            error=str(e)
        )

@router.post("/server/add")
async def add_server(
    config: ServerConfig,
    current_user = Depends(get_current_user),
    server_manager = Depends(get_server_manager)
):
    """Add new server endpoint."""
    if not current_user.is_admin:
        raise HTTPException(403, "Admin access required")
        
    result = await server_manager.add_server(config)
    return result

@router.get("/analytics/performance")
async def get_performance_analytics(
    timeframe: str = "24h",
    server_id: Optional[str] = None,
    current_user = Depends(get_current_user),
    analytics_manager = Depends(get_analytics_manager)
):
    """Get performance analytics endpoint."""
    try:
        analytics = await analytics_manager.get_performance_data(
            timeframe=timeframe,
            server_id=server_id,
            user_id=current_user.id
        )
        
        return AnalyticsData(
            metrics=analytics.metrics,
            trends=analytics.trends,
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        raise HTTPException(500, str(e))