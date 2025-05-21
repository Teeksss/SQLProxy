"""
Admin API endpoints for SQL Proxy.

Last updated: 2025-05-16 13:44:50
Updated by: Teeksss
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Body, Path
from sqlalchemy.orm import Session
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime

from app.db.session import get_db
from app.auth.jwt import get_current_user, TokenData
from app.models.query import PendingApproval, QueryWhitelist, AuditLog
from app.models.server import ServerConfig
from app.models.user import User
from app.services.rate_limiter import RateLimiter
from app.services.notification_service import notification_service

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/approvals", response_model=Dict[str, Any])
async def get_pending_approvals(
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get list of queries pending approval
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view pending approvals"
        )
    
    # Get all pending approvals
    pending_approvals = db.query(PendingApproval).order_by(
        PendingApproval.created_at.desc()
    ).all()
    
    return {
        "total": len(pending_approvals),
        "pending_queries": pending_approvals
    }

@router.post("/approvals/{query_id}/approve", response_model=Dict[str, Any])
async def approve_query(
    query_id: int = Path(..., title="The ID of the query to approve"),
    data: Dict[str, Any] = Body(...),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Approve a pending query
    
    Optionally add it to whitelist for future automatic approval
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to approve queries"
        )
    
    # Get the pending approval
    approval = db.query(PendingApproval).filter(PendingApproval.id == query_id).first()
    if not approval:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pending query with ID {query_id} not found"
        )
    
    # Add to whitelist if requested
    whitelist_id = None
    if data.get("add_to_whitelist", False):
        # Create a new whitelist entry
        whitelist_entry = QueryWhitelist(
            sql_query=approval.sql_query,
            query_hash=approval.query_hash,
            query_type=approval.query_type if hasattr(approval, 'query_type') else "unknown",
            description=data.get("description", ""),
            server_restrictions=data.get("server_restrictions"),
            approved_by=current_user.username,
            approved_at=datetime.utcnow()
        )
        
        db.add(whitelist_entry)
        db.commit()
        db.refresh(whitelist_entry)
        
        whitelist_id = whitelist_entry.id
    
    # Update audit log for this query
    audit_log = db.query(AuditLog).filter(
        AuditLog.query_hash == approval.query_hash,
        AuditLog.username == approval.username,
        AuditLog.target_server == approval.target_server,
        AuditLog.execution_status == "pending"
    ).first()
    
    if audit_log:
        audit_log.execution_status = "approved"
        audit_log.whitelist_id = whitelist_id
        db.commit()
    
    # Delete the pending approval
    db.delete(approval)
    db.commit()
    
    # Send notification to the user
    user = db.query(User).filter(User.username == approval.username).first()
    if user:
        try:
            notification_service.send_approval_result(approval, True)
            logger.info(f"Approval notification sent to user {approval.username}")
        except Exception as e:
            logger.error(f"Failed to send approval notification: {str(e)}")
    
    return {
        "success": True,
        "message": "Query has been approved" + (" and added to whitelist" if whitelist_id else ""),
        "whitelist_id": whitelist_id
    }

@router.post("/approvals/{query_id}/reject", response_model=Dict[str, Any])
async def reject_query(
    query_id: int = Path(..., title="The ID of the query to reject"),
    data: Dict[str, Any] = Body(...),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Reject a pending query
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to reject queries"
        )
    
    # Get the pending approval
    approval = db.query(PendingApproval).filter(PendingApproval.id == query_id).first()
    if not approval:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pending query with ID {query_id} not found"
        )
    
    # Update audit log for this query
    audit_log = db.query(AuditLog).filter(
        AuditLog.query_hash == approval.query_hash,
        AuditLog.username == approval.username,
        AuditLog.target_server == approval.target_server,
        AuditLog.execution_status == "pending"
    ).first()
    
    if audit_log:
        audit_log.execution_status = "rejected"
        audit_log.error_message = data.get("reason", "Query rejected by administrator")
        db.commit()
    
    # Delete the pending approval
    db.delete(approval)
    db.commit()
    
    # Send notification to the user
    try:
        notification_service.send_approval_result(
            approval, 
            False, 
            data.get("reason", "No reason provided")
        )
        logger.info(f"Rejection notification sent to user {approval.username}")
    except Exception as e:
        logger.error(f"Failed to send rejection notification: {str(e)}")
    
    return {
        "success": True,
        "message": "Query has been rejected"
    }

# Additional Admin endpoints would go here