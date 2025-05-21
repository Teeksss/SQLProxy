"""
Audit API endpoints for SQL Proxy

This module provides API endpoints for retrieving and analyzing audit logs.

Last updated: 2025-05-21 07:07:17
Updated by: Teeksss
"""

import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Path, Response
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import csv
import io
import json
from fastapi.responses import StreamingResponse

from app.api.deps import get_current_user, get_current_user_admin, get_db
from app.models.user import User
from app.models.audit import AuditLog
from app.services.audit_service import audit_service
from app.schemas.audit import AuditLogResponse, AuditLogListResponse, AuditSummaryResponse

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/logs", response_model=AuditLogListResponse)
async def get_audit_logs(
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    resource_id: Optional[str] = Query(None, description="Filter by resource ID"),
    action: Optional[str] = Query(None, description="Filter by action"),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    start_date: Optional[datetime] = Query(None, description="Filter by start date"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(10, description="Maximum number of logs to return"),
    offset: int = Query(0, description="Number of logs to skip"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_admin)
) -> Dict[str, Any]:
    """
    Get audit logs with filtering
    
    Args:
        event_type: Optional event type filter
        resource_type: Optional resource type filter
        resource_id: Optional resource ID filter
        action: Optional action filter
        user_id: Optional user ID filter
        start_date: Optional start date filter
        end_date: Optional end date filter
        status: Optional status filter
        limit: Maximum number of logs to return
        offset: Number of logs to skip
        db: Database session
        current_user: Current authenticated admin user
        
    Returns:
        List of audit logs
    """
    try:
        # Get audit logs
        logs = await audit_service.get_audit_logs(
            event_type=event_type,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            status=status,
            limit=limit,
            offset=offset,
            db=db
        )
        
        # Count total logs with same filters
        total_count = db.query(AuditLog)
        
        if event_type:
            total_count = total_count.filter(AuditLog.event_type == event_type)
        
        if resource_type:
            total_count = total_count.filter(AuditLog.resource_type == resource_type)
        
        if resource_id:
            total_count = total_count.filter(AuditLog.resource_id == resource_id)
        
        if action:
            total_count = total_count.filter(AuditLog.action == action)
        
        if user_id:
            total_count = total_count.filter(AuditLog.user_id == user_id)
        
        if start_date:
            total_count = total_count.filter(AuditLog.timestamp >= start_date)
        
        if end_date:
            total_count = total_count.filter(AuditLog.timestamp <= end_date)
        
        if status:
            total_count = total_count.filter(AuditLog.status == status)
        
        total = total_count.count()
        
        return {
            "items": logs,
            "total": total
        }
    except Exception as e:
        logger.error(f"Error getting audit logs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting audit logs: {str(e)}")

@router.get("/logs/{log_id}", response_model=AuditLogResponse)
async def get_audit_log(
    log_id: str = Path(..., description="Audit log ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_admin)
) -> AuditLog:
    """
    Get a specific audit log
    
    Args:
        log_id: Audit log ID
        db: Database session
        current_user: Current authenticated admin user
        
    Returns:
        Audit log details
    """
    try:
        log = db.query(AuditLog).filter(AuditLog.id == log_id).first()
        
        if not log:
            raise HTTPException(status_code=404, detail="Audit log not found")
        
        return log
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting audit log: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting audit log: {str(e)}")

@router.get("/summary", response_model=AuditSummaryResponse)
async def get_audit_summary(
    days: int = Query(30, description="Number of days to include in summary"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_admin)
) -> Dict[str, Any]:
    """
    Get audit log summary
    
    Args:
        days: Number of days to include in summary
        db: Database session
        current_user: Current authenticated admin user
        
    Returns:
        Audit summary
    """
    try:
        # Get audit summary
        summary = await audit_service.get_audit_summary(days, db)
        return summary
    except Exception as e:
        logger.error(f"Error getting audit summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting audit summary: {str(e)}")

@router.get("/export")
async def export_audit_logs(
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    resource_id: Optional[str] = Query(None, description="Filter by resource ID"),
    action: Optional[str] = Query(None, description="Filter by action"),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    start_date: Optional[datetime] = Query(None, description="Filter by start date"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date"),
    status: Optional[str] = Query(None, description="Filter by status"),
    format: str = Query('csv', description="Export format (csv, json, excel)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_admin)
):
    """
    Export audit logs
    
    Args:
        event_type: Optional event type filter
        resource_type: Optional resource type filter
        resource_id: Optional resource ID filter
        action: Optional action filter
        user_id: Optional user ID filter
        start_date: Optional start date filter
        end_date: Optional end date filter
        status: Optional status filter
        format: Export format
        db: Database session
        current_user: Current authenticated admin user
        
    Returns:
        Exported audit logs
    """
    try:
        # Get audit logs (all matching the filters)
        logs = await audit_service.get_audit_logs(
            event_type=event_type,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            status=status,
            limit=10000,  # Set a reasonable limit
            offset=0,
            db=db
        )
        
        # Create filename
        date_str = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"audit_logs_{date_str}"
        
        # Export based on format
        if format.lower() == 'csv':
            return export_csv(logs, filename)
        elif format.lower() == 'json':
            return export_json(logs, filename)
        elif format.lower() == 'excel':
            return export_excel(logs, filename)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting audit logs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error exporting audit logs: {str(e)}")

def export_csv(logs: List[AuditLog], filename: str) -> StreamingResponse:
    """
    Export audit logs to CSV
    
    Args:
        logs: List of audit logs
        filename: Output filename
        
    Returns:
        CSV file
    """
    # Create StringIO object
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        'ID', 'Timestamp', 'Event Type', 'Resource Type', 'Resource ID',
        'Action', 'User ID', 'Username', 'Client IP', 'Status', 'Details'
    ])
    
    # Write data
    for log in logs:
        writer.writerow([
            log.id,
            log.timestamp.isoformat(),
            log.event_type,
            log.resource_type,
            log.resource_id,
            log.action,
            log.user_id,
            log.username,
            log.client_ip,
            log.status,
            json.dumps(log.details) if log.details else ''
        ])
    
    # Create response
    response = StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv"
    )
    
    response.headers["Content-Disposition"] = f"attachment; filename={filename}.csv"
    
    return response

def export_json(logs: List[AuditLog], filename: str) -> Response:
    """
    Export audit logs to JSON
    
    Args:
        logs: List of audit logs
        filename: Output filename
        
    Returns:
        JSON file
    """
    # Convert logs to dict
    logs_list = []
    for log in logs:
        log_dict = {
            'id': log.id,
            'timestamp': log.timestamp.isoformat(),
            'event_type': log.event_type,
            'resource_type': log.resource_type,
            'resource_id': log.resource_id,
            'action': log.action,
            'user_id': log.user_id,
            'username': log.username,
            'client_ip': log.client_ip,
            'status': log.status,
            'details': log.details
        }
        logs_list.append(log_dict)
    
    # Create response
    response = Response(
        content=json.dumps(logs_list, indent=2),
        media_type="application/json"
    )
    
    response.headers["Content-Disposition"] = f"attachment; filename={filename}.json"
    
    return response

def export_excel(logs: List[AuditLog], filename: str) -> StreamingResponse:
    """
    Export audit logs to Excel
    
    Args:
        logs: List of audit logs
        filename: Output filename
        
    Returns:
        Excel file
    """
    try:
        # Use pandas to create Excel file (requires pandas and openpyxl)
        import pandas as pd
        import io
        
        # Convert logs to dict for DataFrame
        logs_dicts = []
        for log in logs:
            log_dict = {
                'ID': log.id,
                'Timestamp': log.timestamp,
                'Event Type': log.event_type,
                'Resource Type': log.resource_type,
                'Resource ID': log.resource_id or '',
                'Action': log.action,
                'User ID': log.user_id or '',
                'Username': log.username or '',
                'Client IP': log.client_ip or '',
                'Status': log.status,
                'Details': json.dumps(log.details) if log.details else ''
            }
            logs_dicts.append(log_dict)
        
        # Create DataFrame
        df = pd.DataFrame(logs_dicts)
        
        # Create Excel file in memory
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Audit Logs')
        
        # Prepare response
        response = StreamingResponse(
            iter([output.getvalue()]),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        response.headers["Content-Disposition"] = f"attachment; filename={filename}.xlsx"
        
        return response
    except ImportError:
        # Fallback to CSV if pandas is not available
        logger.warning("Pandas or openpyxl not available, falling back to CSV export")
        response = export_csv(logs, filename)
        response.headers["Content-Disposition"] = f"attachment; filename={filename}.csv"
        return response

# Son güncelleme: 2025-05-21 07:07:17
# Güncelleyen: Teeksss