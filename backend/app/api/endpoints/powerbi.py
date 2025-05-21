"""
PowerBI API endpoints for SQL Proxy

This module provides API endpoints for PowerBI integration, including
workspace management, report creation, and embed token generation.

Last updated: 2025-05-21 05:44:49
Updated by: Teeksss
"""

import logging
import json
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Path, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import tempfile
import os

from app.api.deps import get_current_user, get_current_user_admin, get_db
from app.models.user import User
from app.models.powerbi import PowerBIWorkspace, PowerBIReport, PowerBIDataset
from app.schemas.powerbi import (
    PowerBICredentials,
    PowerBIEmbedToken,
    PowerBIWorkspaceCreate,
    PowerBIReportCreate,
    PowerBIDatasetCreate,
    PowerBIWorkspaceResponse,
    PowerBIReportResponse,
    PowerBIDatasetResponse,
    PowerBIWorkspacesResponse,
    PowerBIReportsResponse,
    PowerBIDatasetsResponse
)
from app.services.powerbi_service import powerbi_service
from app.services.query_executor import query_executor

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/workspaces", response_model=PowerBIWorkspacesResponse)
async def list_workspaces(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    List PowerBI workspaces
    """
    try:
        # Get workspaces from database
        workspace_query = db.query(PowerBIWorkspace).filter(PowerBIWorkspace.is_active == True)
        workspaces = workspace_query.all()
        
        # Enrich with counts
        for workspace in workspaces:
            workspace.reports_count = db.query(PowerBIReport).filter(
                PowerBIReport.workspace_id == workspace.workspace_id
            ).count()
            
            workspace.datasets_count = db.query(PowerBIDataset).filter(
                PowerBIDataset.workspace_id == workspace.workspace_id
            ).count()
        
        return {
            "items": workspaces,
            "total": len(workspaces)
        }
    except Exception as e:
        logger.error(f"Error listing PowerBI workspaces: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error listing PowerBI workspaces: {str(e)}")

@router.post("/workspaces", response_model=PowerBIWorkspaceResponse)
async def create_workspace(
    workspace: PowerBIWorkspaceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_admin)
) -> Dict[str, Any]:
    """
    Create a new PowerBI workspace
    """
    try:
        # Create workspace in PowerBI
        created = await powerbi_service.create_workspace(workspace.name)
        
        # Save to database
        db_workspace = await powerbi_service.save_workspace(
            workspace_id=created.get('id'),
            name=workspace.name,
            description=workspace.description,
            db=db,
            user=current_user
        )
        
        return db_workspace
    except Exception as e:
        logger.error(f"Error creating PowerBI workspace: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error creating PowerBI workspace: {str(e)}")

@router.get("/workspaces/{workspace_id}", response_model=PowerBIWorkspaceResponse)
async def get_workspace(
    workspace_id: str = Path(..., description="PowerBI workspace ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get PowerBI workspace details
    """
    try:
        # Get workspace from database
        workspace = db.query(PowerBIWorkspace).filter(
            PowerBIWorkspace.workspace_id == workspace_id,
            PowerBIWorkspace.is_active == True
        ).first()
        
        if not workspace:
            raise HTTPException(status_code=404, detail=f"PowerBI workspace {workspace_id} not found")
        
        # Get counts
        workspace.reports_count = db.query(PowerBIReport).filter(
            PowerBIReport.workspace_id == workspace.workspace_id
        ).count()
        
        workspace.datasets_count = db.query(PowerBIDataset).filter(
            PowerBIDataset.workspace_id == workspace.workspace_id
        ).count()
        
        return workspace
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting PowerBI workspace: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting PowerBI workspace: {str(e)}")

@router.get("/workspaces/{workspace_id}/reports", response_model=PowerBIReportsResponse)
async def list_workspace_reports(
    workspace_id: str = Path(..., description="PowerBI workspace ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    List reports in a PowerBI workspace
    """
    try:
        # Get reports from database
        reports_query = db.query(PowerBIReport).filter(PowerBIReport.workspace_id == workspace_id)
        reports = reports_query.all()
        
        return {
            "items": reports,
            "total": len(reports)
        }
    except Exception as e:
        logger.error(f"Error listing PowerBI reports: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error listing PowerBI reports: {str(e)}")

@router.post("/reports", response_model=PowerBIReportResponse)
async def create_report_from_query(
    report: PowerBIReportCreate,
    query_id: Optional[str] = Query(None, description="Saved query ID"),
    query_text: Optional[str] = Query(None, description="SQL query text"),
    server_id: str = Query(..., description="Database server ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Create a PowerBI report from SQL query results
    """
    try:
        # Check if we have either a query ID or query text
        if not query_id and not query_text:
            raise HTTPException(status_code=400, detail="Either query_id or query_text must be provided")
        
        # Execute the query
        if query_id:
            # Execute saved query
            query_results = await query_executor.execute_saved_query(query_id, server_id, current_user, db)
        else:
            # Execute ad-hoc query
            query_results = await query_executor.execute_query(query_text, server_id, current_user, db)
        
        # Create report from query results
        report_data = await powerbi_service.create_report_from_query(
            report=report,
            query_results=query_results,
            db=db,
            user=current_user
        )
        
        # Get the created report from database
        created_report = db.query(PowerBIReport).filter(
            PowerBIReport.report_id == report_data.get('report_id')
        ).first()
        
        if not created_report:
            raise HTTPException(status_code=404, detail="Created report not found in database")
        
        return created_report
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating PowerBI report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error creating PowerBI report: {str(e)}")

@router.post("/reports/import")
async def import_report(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    name: str = Form(...),
    workspace_id: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_admin)
) -> Dict[str, Any]:
    """
    Import a PowerBI report (PBIX file)
    """
    try:
        # Save file to temp location
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pbix')
        temp_file_path = temp_file.name
        
        try:
            # Write uploaded file to temp file
            content = await file.read()
            with open(temp_file_path, 'wb') as f:
                f.write(content)
            
            # Import the report to PowerBI
            import_result = await powerbi_service.import_report(
                file_path=temp_file_path,
                name=name,
                workspace_id=workspace_id
            )
            
            # Check for successful import
            if import_result.get('importState') != 'Succeeded':
                raise HTTPException(
                    status_code=500, 
                    detail=f"Import failed: {import_result.get('error', {}).get('message', 'Unknown error')}"
                )
            
            # Get report information
            reports = import_result.get('reports', [])
            if not reports:
                raise HTTPException(status_code=500, detail="No reports found in import result")
            
            report = reports[0]
            report_id = report.get('id')
            embed_url = report.get('embedUrl')
            
            # Get dataset information
            datasets = import_result.get('datasets', [])
            dataset_id = datasets[0].get('id') if datasets else None
            
            # Save report to database
            new_report = PowerBIReport(
                report_id=report_id,
                name=name,
                description=description,
                workspace_id=workspace_id,
                dataset_id=dataset_id,
                embed_url=embed_url,
                created_by_id=current_user.id,
                created_at=datetime.utcnow()
            )
            
            db.add(new_report)
            db.commit()
            db.refresh(new_report)
            
            # Clean up temp file in background
            background_tasks.add_task(os.unlink, temp_file_path)
            
            return {
                "message": "Report imported successfully",
                "report_id": report_id,
                "name": name,
                "embed_url": embed_url,
                "dataset_id": dataset_id,
                "workspace_id": workspace_id
            }
            
        finally:
            # Ensure temp file is removed if exception occurs
            if os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                except:
                    pass
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error importing PowerBI report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error importing PowerBI report: {str(e)}")

@router.get("/reports", response_model=PowerBIReportsResponse)
async def list_reports(
    workspace_id: Optional[str] = Query(None, description="Filter by workspace ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    List PowerBI reports
    """
    try:
        # Build query
        query = db.query(PowerBIReport)
        
        # Apply filters
        if workspace_id:
            query = query.filter(PowerBIReport.workspace_id == workspace_id)
        
        # Get reports
        reports = query.all()
        
        return {
            "items": reports,
            "total": len(reports)
        }
    except Exception as e:
        logger.error(f"Error listing PowerBI reports: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error listing PowerBI reports: {str(e)}")

@router.get("/reports/{report_id}", response_model=PowerBIReportResponse)
async def get_report(
    report_id: str = Path(..., description="PowerBI report ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get PowerBI report details
    """
    try:
        # Get report from database
        report = db.query(PowerBIReport).filter(PowerBIReport.report_id == report_id).first()
        
        if not report:
            raise HTTPException(status_code=404, detail=f"PowerBI report {report_id} not found")
        
        return report
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting PowerBI report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting PowerBI report: {str(e)}")

@router.post("/reports/{report_id}/embed", response_model=PowerBIEmbedToken)
async def generate_embed_token(
    report_id: str = Path(..., description="PowerBI report ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Generate an embed token for a PowerBI report
    """
    try:
        # Get report from database
        report = db.query(PowerBIReport).filter(PowerBIReport.report_id == report_id).first()
        
        if not report:
            raise HTTPException(status_code=404, detail=f"PowerBI report {report_id} not found")
        
        # Check if we have the dataset ID
        if not report.dataset_id:
            raise HTTPException(status_code=400, detail="Report does not have an associated dataset ID")
        
        # Generate embed token
        embed_token = await powerbi_service.generate_embed_token(
            report_id=report_id,
            dataset_id=report.dataset_id,
            workspace_id=report.workspace_id,
            username=current_user.email  # Use email for Row Level Security
        )
        
        return embed_token
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating PowerBI embed token: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error generating PowerBI embed token: {str(e)}")

@router.post("/refresh-credentials")
async def refresh_powerbi_credentials(
    credentials: PowerBICredentials,
    current_user: User = Depends(get_current_user_admin)
) -> Dict[str, Any]:
    """
    Update PowerBI credentials (admin only)
    """
    try:
        # Update settings
        settings.POWERBI_TENANT_ID = credentials.tenant_id
        settings.POWERBI_CLIENT_ID = credentials.client_id
        settings.POWERBI_CLIENT_SECRET = credentials.client_secret
        
        # Reinitialize service with new credentials
        powerbi_service.tenant_id = credentials.tenant_id
        powerbi_service.client_id = credentials.client_id
        powerbi_service.client_secret = credentials.client_secret
        
        # Test authentication with new credentials
        token = await powerbi_service.authenticate()
        
        return {"message": "PowerBI credentials updated successfully"}
    except Exception as e:
        logger.error(f"Error updating PowerBI credentials: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error updating PowerBI credentials: {str(e)}")

# Son güncelleme: 2025-05-21 05:44:49
# Güncelleyen: Teeksss