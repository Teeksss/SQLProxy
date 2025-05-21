"""
Dashboard API endpoints for SQL Proxy

This module provides API endpoints for managing user dashboards.

Last updated: 2025-05-21 06:42:20
Updated by: Teeksss
"""

import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body
from sqlalchemy.orm import Session
from datetime import datetime

from app.api.deps import get_current_user, get_current_user_admin, get_db
from app.models.user import User
from app.models.dashboard import Dashboard
from app.schemas.dashboard import (
    DashboardCreate,
    DashboardUpdate,
    DashboardResponse,
    DashboardsResponse
)

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("", response_model=DashboardsResponse)
async def get_dashboards(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get user dashboards
    
    Args:
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        List of dashboards
    """
    try:
        # Get dashboards for current user
        dashboards = db.query(Dashboard).filter(
            Dashboard.user_id == current_user.id
        ).order_by(Dashboard.name).all()
        
        return {
            "items": dashboards,
            "total": len(dashboards)
        }
    except Exception as e:
        logger.error(f"Error getting dashboards: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting dashboards: {str(e)}")

@router.get("/{dashboard_id}", response_model=DashboardResponse)
async def get_dashboard(
    dashboard_id: str = Path(..., description="Dashboard ID or 'default'"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get dashboard details
    
    Args:
        dashboard_id: Dashboard ID or 'default'
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Dashboard details
    """
    try:
        # Handle default dashboard
        if dashboard_id == 'default':
            # Get default dashboard
            dashboard = db.query(Dashboard).filter(
                Dashboard.user_id == current_user.id,
                Dashboard.is_default == True
            ).first()
            
            if not dashboard:
                # Create a default dashboard if it doesn't exist
                dashboard = Dashboard(
                    name="Default Dashboard",
                    user_id=current_user.id,
                    is_default=True,
                    config={
                        "widgets": []
                    },
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                
                db.add(dashboard)
                db.commit()
                db.refresh(dashboard)
        else:
            # Get specific dashboard
            dashboard = db.query(Dashboard).filter(
                Dashboard.id == dashboard_id,
                Dashboard.user_id == current_user.id
            ).first()
            
            if not dashboard:
                raise HTTPException(status_code=404, detail="Dashboard not found")
        
        return dashboard
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error getting dashboard: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting dashboard: {str(e)}")

@router.post("", response_model=DashboardResponse)
async def create_dashboard(
    dashboard: DashboardCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Create a new dashboard
    
    Args:
        dashboard: Dashboard creation data
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Created dashboard
    """
    try:
        # Check if making default and update any existing default
        if dashboard.is_default:
            existing_default = db.query(Dashboard).filter(
                Dashboard.user_id == current_user.id,
                Dashboard.is_default == True
            ).first()
            
            if existing_default:
                existing_default.is_default = False
        
        # Create new dashboard
        new_dashboard = Dashboard(
            name=dashboard.name,
            description=dashboard.description,
            user_id=current_user.id,
            is_default=dashboard.is_default,
            config=dashboard.config,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(new_dashboard)
        db.commit()
        db.refresh(new_dashboard)
        
        return new_dashboard
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating dashboard: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error creating dashboard: {str(e)}")

@router.patch("/{dashboard_id}", response_model=DashboardResponse)
async def update_dashboard(
    dashboard_data: DashboardUpdate,
    dashboard_id: str = Path(..., description="Dashboard ID or 'default'"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Update dashboard
    
    Args:
        dashboard_data: Dashboard update data
        dashboard_id: Dashboard ID or 'default'
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Updated dashboard
    """
    try:
        # Get dashboard
        if dashboard_id == 'default':
            dashboard = db.query(Dashboard).filter(
                Dashboard.user_id == current_user.id,
                Dashboard.is_default == True
            ).first()
            
            if not dashboard:
                raise HTTPException(status_code=404, detail="Default dashboard not found")
        else:
            dashboard = db.query(Dashboard).filter(
                Dashboard.id == dashboard_id,
                Dashboard.user_id == current_user.id
            ).first()
            
            if not dashboard:
                raise HTTPException(status_code=404, detail="Dashboard not found")
        
        # Update dashboard fields
        if dashboard_data.name is not None:
            dashboard.name = dashboard_data.name
        
        if dashboard_data.description is not None:
            dashboard.description = dashboard_data.description
        
        if dashboard_data.is_default is not None and dashboard_data.is_default and not dashboard.is_default:
            # Handle making this dashboard default
            existing_default = db.query(Dashboard).filter(
                Dashboard.user_id == current_user.id,
                Dashboard.is_default == True
            ).first()
            
            if existing_default and existing_default.id != dashboard.id:
                existing_default.is_default = False
            
            dashboard.is_default = True
        
        if dashboard_data.config is not None:
            dashboard.config = dashboard_data.config
        
        dashboard.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(dashboard)
        
        return dashboard
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating dashboard: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error updating dashboard: {str(e)}")

@router.delete("/{dashboard_id}")
async def delete_dashboard(
    dashboard_id: str = Path(..., description="Dashboard ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Delete dashboard
    
    Args:
        dashboard_id: Dashboard ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Success message
    """
    try:
        # Cannot delete default dashboard
        if dashboard_id == 'default':
            raise HTTPException(status_code=400, detail="Cannot delete default dashboard")
        
        # Get dashboard
        dashboard = db.query(Dashboard).filter(
            Dashboard.id == dashboard_id,
            Dashboard.user_id == current_user.id
        ).first()
        
        if not dashboard:
            raise HTTPException(status_code=404, detail="Dashboard not found")
        
        # Cannot delete default dashboard
        if dashboard.is_default:
            raise HTTPException(status_code=400, detail="Cannot delete default dashboard")
        
        # Delete dashboard
        db.delete(dashboard)
        db.commit()
        
        return {"message": "Dashboard deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting dashboard: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error deleting dashboard: {str(e)}")

@router.post("/{dashboard_id}/set-default")
async def set_default_dashboard(
    dashboard_id: str = Path(..., description="Dashboard ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Set dashboard as default
    
    Args:
        dashboard_id: Dashboard ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Success message
    """
    try:
        # Get dashboard
        dashboard = db.query(Dashboard).filter(
            Dashboard.id == dashboard_id,
            Dashboard.user_id == current_user.id
        ).first()
        
        if not dashboard:
            raise HTTPException(status_code=404, detail="Dashboard not found")
        
        # Clear existing default
        existing_default = db.query(Dashboard).filter(
            Dashboard.user_id == current_user.id,
            Dashboard.is_default == True
        ).first()
        
        if existing_default and existing_default.id != dashboard.id:
            existing_default.is_default = False
        
        # Set new default
        dashboard.is_default = True
        dashboard.updated_at = datetime.utcnow()
        
        db.commit()
        
        return {"message": f"Dashboard '{dashboard.name}' set as default"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error setting default dashboard: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error setting default dashboard: {str(e)}")

# Son güncelleme: 2025-05-21 06:42:20
# Güncelleyen: Teeksss