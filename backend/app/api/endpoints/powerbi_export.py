"""
PowerBI Export API endpoints for SQL Proxy

This module provides API endpoints for exporting data and reports
from PowerBI to various formats.

Last updated: 2025-05-21 05:58:00
Updated by: Teeksss
"""

import logging
import tempfile
import os
import json
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Path, BackgroundTasks
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_current_user_admin, get_db
from app.models.user import User
from app.models.powerbi import PowerBIWorkspace, PowerBIReport, PowerBIDataset
from app.services.powerbi_service import powerbi_service

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/reports/{report_id}/export/pdf")
async def export_report_to_pdf(
    report_id: str = Path(..., description="Report ID"),
    workspace_id: Optional[str] = Query(None, description="Workspace ID"),
    pages: Optional[str] = Query(None, description="Comma-separated page names to export"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Export a PowerBI report to PDF
    
    Args:
        report_id: Report ID
        workspace_id: Optional workspace ID
        pages: Optional comma-separated page names to export
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        PDF file as a download
    """
    try:
        # Get report from database
        report = db.query(PowerBIReport).filter(PowerBIReport.report_id == report_id).first()
        
        if report:
            workspace_id = workspace_id or report.workspace_id
        
        # Convert pages parameter to list
        page_names = None
        if pages:
            page_names = [page.strip() for page in pages.split(',')]
        
        # Export to PDF
        temp_pdf_path = await powerbi_service.export_report_to_pdf(report_id, workspace_id, page_names)
        
        # Return PDF file
        return FileResponse(
            path=temp_pdf_path,
            media_type='application/pdf',
            filename=f"{report.name if report else 'report'}.pdf",
            background=BackgroundTasks.add_task(lambda: os.unlink(temp_pdf_path) if os.path.exists(temp_pdf_path) else None)
        )
    except Exception as e:
        logger.error(f"Error exporting PowerBI report to PDF: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error exporting PowerBI report to PDF: {str(e)}")

@router.get("/reports/{report_id}/export/pptx")
async def export_report_to_pptx(
    report_id: str = Path(..., description="Report ID"),
    workspace_id: Optional[str] = Query(None, description="Workspace ID"),
    pages: Optional[str] = Query(None, description="Comma-separated page names to export"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Export a PowerBI report to PowerPoint
    
    Args:
        report_id: Report ID
        workspace_id: Optional workspace ID
        pages: Optional comma-separated page names to export
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        PowerPoint file as a download
    """
    try:
        # Get report from database
        report = db.query(PowerBIReport).filter(PowerBIReport.report_id == report_id).first()
        
        if report:
            workspace_id = workspace_id or report.workspace_id
        
        # Convert pages parameter to list
        page_names = None
        if pages:
            page_names = [page.strip() for page in pages.split(',')]
        
        # Export to PowerPoint
        temp_pptx_path = await powerbi_service.export_report_to_pptx(report_id, workspace_id, page_names)
        
        # Return PowerPoint file
        return FileResponse(
            path=temp_pptx_path,
            media_type='application/vnd.openxmlformats-officedocument.presentationml.presentation',
            filename=f"{report.name if report else 'report'}.pptx",
            background=BackgroundTasks.add_task(lambda: os.unlink(temp_pptx_path) if os.path.exists(temp_pptx_path) else None)
        )
    except Exception as e:
        logger.error(f"Error exporting PowerBI report to PowerPoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error exporting PowerBI report to PowerPoint: {str(e)}")

@router.get("/reports/{report_id}/export/png")
async def export_report_page_to_png(
    report_id: str = Path(..., description="Report ID"),
    page_name: str = Query(..., description="Page name to export"),
    workspace_id: Optional[str] = Query(None, description="Workspace ID"),
    width: int = Query(1920, description="Image width in pixels"),
    height: int = Query(1080, description="Image height in pixels"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Export a PowerBI report page to PNG
    
    Args:
        report_id: Report ID
        page_name: Page name to export
        workspace_id: Optional workspace ID
        width: Image width in pixels
        height: Image height in pixels
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        PNG image file as a download
    """
    try:
        # Get report from database
        report = db.query(PowerBIReport).filter(PowerBIReport.report_id == report_id).first()
        
        if report:
            workspace_id = workspace_id or report.workspace_id
        
        # Export to PNG
        temp_png_path = await powerbi_service.export_report_page_to_png(
            report_id, 
            page_name, 
            workspace_id, 
            width, 
            height
        )
        
        # Return PNG file
        return FileResponse(
            path=temp_png_path,
            media_type='image/png',
            filename=f"{report.name if report else 'report'}_{page_name}.png",
            background=BackgroundTasks.add_task(lambda: os.unlink(temp_png_path) if os.path.exists(temp_png_path) else None)
        )
    except Exception as e:
        logger.error(f"Error exporting PowerBI report page to PNG: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error exporting PowerBI report page to PNG: {str(e)}")

@router.get("/datasets/{dataset_id}/export/data")
async def export_dataset_data(
    dataset_id: str = Path(..., description="Dataset ID"),
    table_name: str = Query(..., description="Table name"),
    format: str = Query("csv", description="Export format (csv, json, excel)"),
    workspace_id: Optional[str] = Query(None, description="Workspace ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Export data from a PowerBI dataset table
    
    Args:
        dataset_id: Dataset ID
        table_name: Table name
        format: Export format (csv, json, excel)
        workspace_id: Optional workspace ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Data file as a download
    """
    try:
        # Get dataset from database
        dataset = db.query(PowerBIDataset).filter(PowerBIDataset.dataset_id == dataset_id).first()
        
        if dataset:
            workspace_id = workspace_id or dataset.workspace_id
        
        # Get data from PowerBI
        data = await powerbi_service.get_dataset_table_data(dataset_id, table_name, workspace_id)
        
        if not data:
            raise HTTPException(status_code=404, detail=f"No data found in dataset {dataset_id}, table {table_name}")
        
        # Export according to format
        if format.lower() == "json":
            # Return as JSON
            json_data = json.dumps(data, indent=2)
            return StreamingResponse(
                iter([json_data]), 
                media_type="application/json",
                headers={"Content-Disposition": f"attachment; filename={table_name}.json"}
            )
        elif format.lower() == "excel":
            # Export to Excel
            import pandas as pd
            import io
            
            # Create a pandas DataFrame
            df = pd.DataFrame(data)
            
            # Create Excel file in memory
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name=table_name, index=False)
            
            output.seek(0)
            
            return StreamingResponse(
                output, 
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": f"attachment; filename={table_name}.xlsx"}
            )
        else:
            # Default: export to CSV
            import pandas as pd
            import io
            
            # Create a pandas DataFrame
            df = pd.DataFrame(data)
            
            # Create CSV string
            output = io.StringIO()
            df.to_csv(output, index=False)
            
            return StreamingResponse(
                iter([output.getvalue()]), 
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename={table_name}.csv"}
            )
    except Exception as e:
        logger.error(f"Error exporting PowerBI dataset data: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error exporting PowerBI dataset data: {str(e)}")

@router.get("/reports/{report_id}/paginated-export")
async def schedule_paginated_report_export(
    report_id: str = Path(..., description="Report ID"),
    workspace_id: Optional[str] = Query(None, description="Workspace ID"),
    format: str = Query("PDF", description="Export format (PDF, DOCX, XLSX, PPTX, PNG, CSV)"),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Schedule a paginated report export
    
    Args:
        report_id: Report ID
        workspace_id: Optional workspace ID
        format: Export format
        background_tasks: Background tasks
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Export status information
    """
    try:
        # Get report from database
        report = db.query(PowerBIReport).filter(PowerBIReport.report_id == report_id).first()
        
        if report:
            workspace_id = workspace_id or report.workspace_id
        
        # Schedule export in PowerBI
        export_info = await powerbi_service.schedule_paginated_report_export(
            report_id=report_id,
            workspace_id=workspace_id,
            format=format
        )
        
        # Check export status in background
        if background_tasks:
            background_tasks.add_task(
                powerbi_service.check_export_status,
                export_id=export_info.get("id"),
                report_id=report_id,
                workspace_id=workspace_id
            )
        
        return export_info
    except Exception as e:
        logger.error(f"Error scheduling paginated report export: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error scheduling paginated report export: {str(e)}")

@router.get("/reports/exports/{export_id}")
async def get_export_status(
    export_id: str = Path(..., description="Export ID"),
    report_id: str = Query(..., description="Report ID"),
    workspace_id: Optional[str] = Query(None, description="Workspace ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get the status of a report export
    
    Args:
        export_id: Export ID
        report_id: Report ID
        workspace_id: Optional workspace ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Export status information
    """
    try:
        # Get report from database
        report = db.query(PowerBIReport).filter(PowerBIReport.report_id == report_id).first()
        
        if report:
            workspace_id = workspace_id or report.workspace_id
        
        # Get export status
        status = await powerbi_service.check_export_status(export_id, report_id, workspace_id)
        
        return status
    except Exception as e:
        logger.error(f"Error getting export status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting export status: {str(e)}")

@router.get("/reports/exports/{export_id}/file")
async def download_export(
    export_id: str = Path(..., description="Export ID"),
    report_id: str = Query(..., description="Report ID"),
    workspace_id: Optional[str] = Query(None, description="Workspace ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Download an exported report file
    
    Args:
        export_id: Export ID
        report_id: Report ID
        workspace_id: Optional workspace ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Exported file as a download
    """
    try:
        # Get report from database
        report = db.query(PowerBIReport).filter(PowerBIReport.report_id == report_id).first()
        
        if report:
            workspace_id = workspace_id or report.workspace_id
        
        # Get export status first to check if it's completed
        status = await powerbi_service.check_export_status(export_id, report_id, workspace_id)
        
        if status.get("status") != "Succeeded":
            raise HTTPException(
                status_code=400, 
                detail=f"Export is not ready for download. Current status: {status.get('status')}"
            )
        
        # Download the export
        temp_file_path, content_type, file_extension = await powerbi_service.download_export(
            export_id, 
            report_id, 
            workspace_id
        )
        
        # Determine filename
        filename = f"{report.name if report else 'report'}.{file_extension}"
        
        # Return the file
        return FileResponse(
            path=temp_file_path,
            media_type=content_type,
            filename=filename,
            background=BackgroundTasks.add_task(lambda: os.unlink(temp_file_path) if os.path.exists(temp_file_path) else None)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading export: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error downloading export: {str(e)}")

# Son güncelleme: 2025-05-21 05:58:00
# Güncelleyen: Teeksss