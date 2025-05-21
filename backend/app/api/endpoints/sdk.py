"""
SDK API endpoints for SQL Proxy

This module provides API endpoints for generating client SDKs
in various programming languages.

Last updated: 2025-05-21 05:35:49
Updated by: Teeksss
"""

import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Path, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse

from app.api.deps import get_current_user_admin
from app.models.user import User
from app.schemas.sdk import SDKConfig, SDKLanguage, SDKGenerationResponse
from app.sdk.python_generator import PythonSDKGenerator
from app.sdk.typescript_generator import TypeScriptSDKGenerator
from app.sdk.java_generator import JavaSDKGenerator
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/generate", response_model=SDKGenerationResponse)
async def generate_sdk(
    config: SDKConfig,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user_admin)
) -> Dict[str, Any]:
    """
    Generate an SDK for a specific language
    
    Args:
        config: SDK configuration
        background_tasks: Background tasks
        current_user: Current authenticated admin user
        
    Returns:
        SDK generation response
    """
    try:
        # Generate SDK in background for potentially large SDKs
        output_path = ""
        
        if config.language == SDKLanguage.PYTHON:
            generator = PythonSDKGenerator(config)
            background_tasks.add_task(generator.generate)
            output_path = f"{settings.SDK_OUTPUT_DIR}/python-{config.version}"
        elif config.language == SDKLanguage.TYPESCRIPT:
            generator = TypeScriptSDKGenerator(config)
            background_tasks.add_task(generator.generate)
            output_path = f"{settings.SDK_OUTPUT_DIR}/typescript-{config.version}"
        elif config.language == SDKLanguage.JAVA:
            generator = JavaSDKGenerator(config)
            background_tasks.add_task(generator.generate)
            output_path = f"{settings.SDK_OUTPUT_DIR}/java-{config.version}"
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported language: {config.language}")
        
        return {
            "message": f"SDK generation started for {config.language}",
            "language": config.language,
            "version": config.version,
            "output_path": output_path,
            "status": "in_progress"
        }
    except Exception as e:
        logger.error(f"Error generating SDK: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error generating SDK: {str(e)}")

@router.get("/download/{language}/{version}")
async def download_sdk(
    language: SDKLanguage = Path(..., description="SDK language"),
    version: str = Path(..., description="SDK version"),
    current_user: User = Depends(get_current_user_admin)
):
    """
    Download a generated SDK
    
    Args:
        language: SDK language
        version: SDK version
        current_user: Current authenticated admin user
        
    Returns:
        SDK as a downloadable file
    """
    try:
        import os
        from pathlib import Path
        import shutil
        
        # Determine SDK path
        sdk_dir = Path(f"{settings.SDK_OUTPUT_DIR}/{language.value}-{version}")
        
        if not sdk_dir.exists():
            raise HTTPException(status_code=404, detail=f"SDK not found: {language}-{version}")
        
        # Create a zip file with the SDK
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as temp_file:
            temp_path = temp_file.name
        
        # Create zip archive
        shutil.make_archive(
            base_name=temp_path.replace('.zip', ''),
            format='zip',
            root_dir=sdk_dir.parent,
            base_dir=sdk_dir.name
        )
        
        filename = f"sql-proxy-sdk-{language.value}-{version}.zip"
        
        # Return the file
        return FileResponse(
            path=temp_path,
            filename=filename,
            media_type="application/zip",
            background=BackgroundTasks.add_task(lambda: os.unlink(temp_path))
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading SDK: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error downloading SDK: {str(e)}")

@router.get("/available")
async def list_available_sdks(
    current_user: User = Depends(get_current_user_admin)
) -> Dict[str, Any]:
    """
    List available SDKs
    
    Args:
        current_user: Current authenticated admin user
        
    Returns:
        List of available SDKs
    """
    try:
        import os
        from pathlib import Path
        
        # Get list of SDK directories
        sdk_dir = Path(settings.SDK_OUTPUT_DIR)
        if not sdk_dir.exists():
            sdk_dir.mkdir(parents=True, exist_ok=True)
            return {"sdks": []}
        
        # List directory contents
        available_sdks = []
        
        for item in sdk_dir.iterdir():
            if item.is_dir():
                try:
                    # Parse directory name (e.g., "python-1.0.0")
                    parts = item.name.split('-')
                    if len(parts) >= 2:
                        language = parts[0]
                        version = '-'.join(parts[1:])
                        
                        available_sdks.append({
                            "language": language,
                            "version": version,
                            "path": str(item),
                            "created_at": os.path.getctime(item)
                        })
                except:
                    continue
        
        # Sort by creation time, newest first
        available_sdks.sort(key=lambda x: x["created_at"], reverse=True)
        
        # Remove creation time from response
        for sdk in available_sdks:
            sdk.pop("created_at")
        
        return {"sdks": available_sdks}
    except Exception as e:
        logger.error(f"Error listing SDKs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error listing SDKs: {str(e)}")

@router.delete("/{language}/{version}")
async def delete_sdk(
    language: SDKLanguage = Path(..., description="SDK language"),
    version: str = Path(..., description="SDK version"),
    current_user: User = Depends(get_current_user_admin)
) -> Dict[str, Any]:
    """
    Delete a generated SDK
    
    Args:
        language: SDK language
        version: SDK version
        current_user: Current authenticated admin user
        
    Returns:
        Success message
    """
    try:
        import shutil
        from pathlib import Path
        
        # Determine SDK path
        sdk_dir = Path(f"{settings.SDK_OUTPUT_DIR}/{language.value}-{version}")
        
        if not sdk_dir.exists():
            raise HTTPException(status_code=404, detail=f"SDK not found: {language}-{version}")
        
        # Delete directory
        shutil.rmtree(sdk_dir)
        
        return {"message": f"SDK deleted: {language}-{version}"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting SDK: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error deleting SDK: {str(e)}")

# Son güncelleme: 2025-05-21 05:35:49
# Güncelleyen: Teeksss