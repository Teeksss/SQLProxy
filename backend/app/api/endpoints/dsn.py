"""
DSN (Data Source Name) API endpoints for SQL Proxy

This module provides API endpoints for creating and managing DSN
configurations for PowerBI and other data connectors.

Last updated: 2025-05-21 06:45:04
Updated by: Teeksss
"""

import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Path, File, UploadFile, Form
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session
import os
from pathlib import Path

from app.api.deps import get_current_user, get_current_user_admin, get_db
from app.models.user import User
from app.services.dsn_service import dsn_service
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/templates")
async def get_dsn_templates(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get available DSN templates
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        List of available templates
    """
    try:
        templates = await dsn_service.get_dsn_templates()
        return {"templates": templates}
    except Exception as e:
        logger.error(f"Error getting DSN templates: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting DSN templates: {str(e)}")

@router.post("/generate")
async def generate_dsn(
    template_id: str = Form(..., description="Template ID"),
    server_id: Optional[str] = Form(None, description="Server ID"),
    dsn_name: Optional[str] = Form(None, description="DSN name"),
    additional_params: Optional[str] = Form(None, description="Additional parameters as JSON"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Generate a DSN configuration file
    
    Args:
        template_id: Template identifier
        server_id: Server ID
        dsn_name: Optional DSN name
        additional_params: Optional additional parameters as JSON
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        DSN generation result with file path and download URL
    """
    try:
        # Parse additional parameters
        parsed_additional_params = {}
        if additional_params:
            import json
            try:
                parsed_additional_params = json.loads(additional_params)
            except:
                raise HTTPException(status_code=400, detail="Invalid additional_params JSON format")
        
        if not server_id:
            raise HTTPException(status_code=400, detail="server_id is required")
        
        # Generate DSN
        result = await dsn_service.generate_dsn(
            template_id=template_id,
            server_id=server_id,
            dsn_name=dsn_name,
            additional_params=parsed_additional_params,
            user_id=current_user.id,
            db=db
        )
        
        return result
    except ValueError as e:
        logger.error(f"Value error generating DSN: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating DSN: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error generating DSN: {str(e)}")

@router.get("/user-configs")
async def get_user_dsn_configs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get DSN configurations for the current user
    
    Args:
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        List of user's DSN configurations
    """
    try:
        dsn_configs = await dsn_service.get_user_dsn_configs(current_user.id, db)
        return {"configs": dsn_configs}
    except ValueError as e:
        logger.error(f"Value error getting user DSN configs: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting user DSN configs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting user DSN configs: {str(e)}")

@router.delete("/user-configs/{dsn_name}")
async def delete_user_dsn_config(
    dsn_name: str = Path(..., description="DSN name to delete"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Delete a DSN configuration for the current user
    
    Args:
        dsn_name: DSN name
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Success status
    """
    try:
        success = await dsn_service.delete_user_dsn_config(current_user.id, dsn_name, db)
        if success:
            return {"message": f"DSN configuration '{dsn_name}' deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail=f"DSN configuration '{dsn_name}' not found")
    except ValueError as e:
        logger.error(f"Value error deleting user DSN config: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting user DSN config: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error deleting user DSN config: {str(e)}")

@router.get("/download/{file_name}")
async def download_dsn(
    file_name: str = Path(..., description="DSN file name to download"),
    current_user: User = Depends(get_current_user)
) -> FileResponse:
    """
    Download a DSN file
    
    Args:
        file_name: DSN file name
        current_user: Current authenticated user
        
    Returns:
        DSN file
    """
    try:
        # Security check: if it's a user-specific DSN, verify ownership
        if file_name.startswith("user_"):
            try:
                parts = file_name.split("_", 2)
                if len(parts) >= 2:
                    user_id = int(parts[1])
                    if user_id != current_user.id and not current_user.is_admin:
                        raise HTTPException(status_code=403, detail="You do not have permission to access this DSN file")
            except:
                raise HTTPException(status_code=400, detail="Invalid DSN file name format")
        
        # Build file path
        dsn_output_dir = Path(settings.DSN_OUTPUT_DIR) if hasattr(settings, 'DSN_OUTPUT_DIR') else Path("./dsn_output")
        file_path = dsn_output_dir / file_name
        
        # Check if file exists
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"DSN file '{file_name}' not found")
        
        # Determine media type based on extension
        media_type = "application/octet-stream"
        if file_name.endswith(".dsn"):
            media_type = "application/octet-stream"
        elif file_name.endswith(".pbids"):
            media_type = "application/json"
        
        # Return file
        return FileResponse(
            path=str(file_path),
            filename=file_name,
            media_type=media_type
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading DSN file: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error downloading DSN file: {str(e)}")

@router.post("/upload-template")
async def upload_dsn_template(
    template_file: UploadFile = File(..., description="Template JSON file"),
    current_user: User = Depends(get_current_user_admin)
) -> Dict[str, Any]:
    """
    Upload a custom DSN template (admin only)
    
    Args:
        template_file: Template JSON file
        current_user: Current authenticated admin user
        
    Returns:
        Upload result
    """
    try:
        # Verify file extension
        if not template_file.filename.endswith(".json"):
            raise HTTPException(status_code=400, detail="Template file must be a JSON file")
        
        # Read template content
        content = await template_file.read()
        
        # Parse JSON to validate
        import json
        try:
            template_data = json.loads(content)
            
            # Verify template structure
            if "template" not in template_data or "file_extension" not in template_data:
                raise ValueError("Template must contain 'template' and 'file_extension' fields")
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON format")
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        
        # Get template directory
        dsn_template_dir = Path(settings.DSN_TEMPLATE_DIR) if hasattr(settings, 'DSN_TEMPLATE_DIR') else Path("./dsn_templates")
        
        # Create directory if it doesn't exist
        if not dsn_template_dir.exists():
            dsn_template_dir.mkdir(parents=True, exist_ok=True)
        
        # Save template file
        file_path = dsn_template_dir / template_file.filename
        with open(file_path, "wb") as f:
            f.write(content)
        
        return {
            "message": f"Template '{template_file.filename}' uploaded successfully",
            "template_id": os.path.splitext(template_file.filename)[0]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading DSN template: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error uploading DSN template: {str(e)}")

@router.get("/powerbi-connection/{server_id}")
async def get_powerbi_connection_string(
    server_id: str = Path(..., description="Server ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get a PowerBI connection string for a server
    
    Args:
        server_id: Server ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Connection string details
    """
    try:
        connection_details = await dsn_service.generate_powerbi_connection_string(server_id, db)
        return connection_details
    except ValueError as e:
        logger.error(f"Value error getting PowerBI connection string: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting PowerBI connection string: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting PowerBI connection string: {str(e)}")

# Son güncelleme: 2025-05-21 06:45:04
# Güncelleyen: Teeksss