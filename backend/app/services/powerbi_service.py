"""
PowerBI Integration Service for SQL Proxy

This module provides functionality for integrating with Microsoft PowerBI,
including authentication, dataset creation, report generation and embedding.

Last updated: 2025-05-21 05:44:49
Updated by: Teeksss
"""

import os
import json
import logging
import requests
import datetime
import hashlib
import hmac
import base64
import time
from typing import Dict, List, Any, Optional, Tuple, Union
from pathlib import Path
import msal

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models.user import User
from app.models.powerbi import PowerBIWorkspace, PowerBIReport, PowerBIDataset
from app.schemas.powerbi import (
    PowerBICredentials,
    PowerBIEmbedToken,
    PowerBIDatasetCreate,
    PowerBIReportCreate
)

logger = logging.getLogger(__name__)

class PowerBIService:
    """
    Service for interacting with Microsoft PowerBI
    
    Provides functionality for creating datasets, publishing reports,
    generating embed tokens, and managing PowerBI workspaces.
    """
    
    def __init__(self):
        """Initialize PowerBI service"""
        self.tenant_id = settings.POWERBI_TENANT_ID
        self.client_id = settings.POWERBI_CLIENT_ID
        self.client_secret = settings.POWERBI_CLIENT_SECRET
        self.scope = ['https://analysis.windows.net/powerbi/api/.default']
        self.api_url = 'https://api.powerbi.com/v1.0/myorg'
        self.embed_url_base = 'https://app.powerbi.com/reportEmbed'
        self.token_cache = {}  # Simple in-memory token cache
        
        # Initialize MSAL application for authentication
        if self.tenant_id and self.client_id and self.client_secret:
            self.app = msal.ConfidentialClientApplication(
                client_id=self.client_id,
                authority=f"https://login.microsoftonline.com/{self.tenant_id}",
                client_credential=self.client_secret,
                token_cache=msal.SerializableTokenCache()
            )
            logger.info("PowerBI service initialized with valid credentials")
        else:
            self.app = None
            logger.warning("PowerBI service initialized without valid credentials")
    
    async def authenticate(self) -> str:
        """
        Authenticate with PowerBI service and get access token
        
        Returns:
            Access token string
        """
        # Check if there's a valid cached token
        if 'access_token' in self.token_cache and self.token_cache['expires_at'] > time.time():
            return self.token_cache['access_token']
        
        if not self.app:
            raise HTTPException(status_code=500, detail="PowerBI service not properly configured")
        
        try:
            # Acquire token by client credentials flow
            result = self.app.acquire_token_for_client(scopes=self.scope)
            
            if 'access_token' not in result:
                logger.error(f"Failed to acquire token: {result.get('error_description', '')}")
                raise HTTPException(status_code=500, detail="Failed to acquire PowerBI access token")
            
            # Cache the token
            self.token_cache = {
                'access_token': result['access_token'],
                'expires_at': time.time() + result.get('expires_in', 3600) - 300  # 5 minutes buffer
            }
            
            return result['access_token']
            
        except Exception as e:
            logger.error(f"Error authenticating with PowerBI: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"PowerBI authentication error: {str(e)}")
    
    async def list_workspaces(self) -> List[Dict[str, Any]]:
        """
        Get list of PowerBI workspaces
        
        Returns:
            List of workspace data
        """
        try:
            token = await self.authenticate()
            
            url = f"{self.api_url}/groups"
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            return response.json().get('value', [])
            
        except Exception as e:
            logger.error(f"Error listing PowerBI workspaces: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error listing PowerBI workspaces: {str(e)}")
    
    async def get_workspace(self, workspace_id: str) -> Dict[str, Any]:
        """
        Get details of a PowerBI workspace
        
        Args:
            workspace_id: PowerBI workspace ID
            
        Returns:
            Workspace details
        """
        try:
            token = await self.authenticate()
            
            url = f"{self.api_url}/groups/{workspace_id}"
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Error getting PowerBI workspace: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error getting PowerBI workspace: {str(e)}")
    
    async def create_workspace(self, name: str) -> Dict[str, Any]:
        """
        Create a new PowerBI workspace
        
        Args:
            name: Workspace name
            
        Returns:
            Created workspace details
        """
        try:
            token = await self.authenticate()
            
            url = f"{self.api_url}/groups"
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'name': name
            }
            
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Error creating PowerBI workspace: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error creating PowerBI workspace: {str(e)}")
    
    async def list_datasets(self, workspace_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get list of PowerBI datasets
        
        Args:
            workspace_id: Optional workspace ID (if None, uses 'My Workspace')
            
        Returns:
            List of dataset data
        """
        try:
            token = await self.authenticate()
            
            url = f"{self.api_url}/datasets" if not workspace_id else f"{self.api_url}/groups/{workspace_id}/datasets"
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            return response.json().get('value', [])
            
        except Exception as e:
            logger.error(f"Error listing PowerBI datasets: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error listing PowerBI datasets: {str(e)}")
    
    async def create_push_dataset(
        self, 
        dataset: PowerBIDatasetCreate,
        workspace_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new push dataset in PowerBI
        
        Args:
            dataset: Dataset creation parameters
            workspace_id: Optional workspace ID (if None, uses 'My Workspace')
            
        Returns:
            Created dataset details
        """
        try:
            token = await self.authenticate()
            
            url = f"{self.api_url}/datasets" if not workspace_id else f"{self.api_url}/groups/{workspace_id}/datasets"
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            # Build dataset schema
            schema = {
                "name": dataset.name,
                "defaultMode": dataset.default_mode,
                "tables": []
            }
            
            # Add tables to schema
            for table in dataset.tables:
                table_schema = {
                    "name": table.name,
                    "columns": []
                }
                
                # Add columns to table
                for column in table.columns:
                    table_schema["columns"].append({
                        "name": column.name,
                        "dataType": column.data_type
                    })
                
                schema["tables"].append(table_schema)
            
            response = requests.post(url, headers=headers, json=schema)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Error creating PowerBI dataset: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error creating PowerBI dataset: {str(e)}")
    
    async def push_rows(
        self, 
        dataset_id: str, 
        table_name: str, 
        rows: List[Dict[str, Any]],
        workspace_id: Optional[str] = None
    ) -> bool:
        """
        Push rows to a PowerBI dataset table
        
        Args:
            dataset_id: Dataset ID
            table_name: Table name
            rows: List of row data
            workspace_id: Optional workspace ID (if None, uses 'My Workspace')
            
        Returns:
            Success status
        """
        try:
            token = await self.authenticate()
            
            url = f"{self.api_url}/datasets/{dataset_id}/tables/{table_name}/rows" 
            if workspace_id:
                url = f"{self.api_url}/groups/{workspace_id}/datasets/{dataset_id}/tables/{table_name}/rows"
                
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            data = {
                "rows": rows
            }
            
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            
            return True
            
        except Exception as e:
            logger.error(f"Error pushing rows to PowerBI dataset: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error pushing rows to PowerBI dataset: {str(e)}")
    
    async def list_reports(self, workspace_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get list of PowerBI reports
        
        Args:
            workspace_id: Optional workspace ID (if None, uses 'My Workspace')
            
        Returns:
            List of report data
        """
        try:
            token = await self.authenticate()
            
            url = f"{self.api_url}/reports" if not workspace_id else f"{self.api_url}/groups/{workspace_id}/reports"
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            return response.json().get('value', [])
            
        except Exception as e:
            logger.error(f"Error listing PowerBI reports: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error listing PowerBI reports: {str(e)}")
    
    async def get_report(
        self, 
        report_id: str, 
        workspace_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get details of a PowerBI report
        
        Args:
            report_id: Report ID
            workspace_id: Optional workspace ID (if None, uses 'My Workspace')
            
        Returns:
            Report details
        """
        try:
            token = await self.authenticate()
            
            url = f"{self.api_url}/reports/{report_id}" 
            if workspace_id:
                url = f"{self.api_url}/groups/{workspace_id}/reports/{report_id}"
                
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Error getting PowerBI report: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error getting PowerBI report: {str(e)}")
    
    async def import_report(
        self,
        file_path: str,
        name: str,
        workspace_id: Optional[str] = None,
        dataset_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Import a PowerBI report (PBIX file)
        
        Args:
            file_path: Path to PBIX file
            name: Name for the imported report
            workspace_id: Optional workspace ID (if None, uses 'My Workspace')
            dataset_name: Optional dataset name
            
        Returns:
            Import result details
        """
        try:
            token = await self.authenticate()
            
            url = f"{self.api_url}/imports?datasetDisplayName={dataset_name or name}"
            if workspace_id:
                url = f"{self.api_url}/groups/{workspace_id}/imports?datasetDisplayName={dataset_name or name}"
                
            headers = {
                'Authorization': f'Bearer {token}'
            }
            
            with open(file_path, 'rb') as f:
                file_content = f.read()
            
            # Use nameSuffix to set the report name
            url += f"&nameConflict=Abort&nameSuffix={name}"
            
            response = requests.post(
                url,
                headers=headers,
                files={
                    'file': (os.path.basename(file_path), file_content, 'application/octet-stream')
                }
            )
            response.raise_for_status()
            
            # Get import result
            import_result = response.json()
            import_id = import_result.get('id')
            
            # Poll for import completion
            import_status = 'NotStarted'
            max_attempts = 30
            attempts = 0
            
            while import_status in ['NotStarted', 'Importing'] and attempts < max_attempts:
                time.sleep(1)
                attempts += 1
                
                status_url = f"{self.api_url}/imports/{import_id}"
                if workspace_id:
                    status_url = f"{self.api_url}/groups/{workspace_id}/imports/{import_id}"
                
                status_response = requests.get(status_url, headers={'Authorization': f'Bearer {token}'})
                status_response.raise_for_status()
                status_data = status_response.json()
                import_status = status_data.get('importState')
            
            return status_data
            
        except Exception as e:
            logger.error(f"Error importing PowerBI report: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error importing PowerBI report: {str(e)}")
    
    async def generate_embed_token(
        self,
        report_id: str,
        dataset_id: str,
        workspace_id: Optional[str] = None,
        username: Optional[str] = None
    ) -> PowerBIEmbedToken:
        """
        Generate an embed token for a PowerBI report
        
        Args:
            report_id: Report ID
            dataset_id: Dataset ID
            workspace_id: Optional workspace ID (if None, uses 'My Workspace')
            username: Optional username for RLS (Row Level Security)
            
        Returns:
            Embed token details
        """
        try:
            token = await self.authenticate()
            
            url = f"{self.api_url}/GenerateToken"
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            # Prepare token request
            token_request = {
                "datasets": [
                    {
                        "id": dataset_id
                    }
                ],
                "reports": [
                    {
                        "id": report_id
                    }
                ]
            }
            
            # Add workspace if specified
            if workspace_id:
                token_request["targetWorkspaces"] = [
                    {
                        "id": workspace_id
                    }
                ]
            
            # Add effective identity for Row Level Security if username is provided
            if username:
                token_request["identities"] = [
                    {
                        "username": username,
                        "datasets": [dataset_id]
                    }
                ]
            
            response = requests.post(url, headers=headers, json=token_request)
            response.raise_for_status()
            
            token_data = response.json()
            
            # Get report details for embed URL
            report_details = await self.get_report(report_id, workspace_id)
            
            return PowerBIEmbedToken(
                token=token_data.get('token'),
                token_id=token_data.get('tokenId'),
                expiration=token_data.get('expiration'),
                embed_url=report_details.get('embedUrl')
            )
            
        except Exception as e:
            logger.error(f"Error generating PowerBI embed token: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error generating PowerBI embed token: {str(e)}")
    
    async def create_report_from_query(
        self,
        report: PowerBIReportCreate,
        query_results: Dict[str, Any],
        db: Session,
        user: User
    ) -> Dict[str, Any]:
        """
        Create a PowerBI report from SQL query results
        
        Args:
            report: Report creation parameters
            query_results: SQL query results
            db: Database session
            user: Current user
            
        Returns:
            Created report details
        """
        try:
            # Create a dataset first
            dataset_create = PowerBIDatasetCreate(
                name=f"{report.name} Dataset",
                default_mode="Push",
                tables=[{
                    "name": "QueryResults",
                    "columns": []
                }]
            )
            
            # Extract column definitions from query results
            if query_results.get('columns') and query_results.get('data'):
                columns = query_results['columns']
                data = query_results['data']
                
                if data and len(data) > 0:
                    # Get column types from first row
                    first_row = data[0]
                    for i, col in enumerate(columns):
                        if i < len(first_row):
                            value = first_row[i]
                            col_type = "String"
                            
                            if isinstance(value, int):
                                col_type = "Int64"
                            elif isinstance(value, float):
                                col_type = "Double"
                            elif isinstance(value, bool):
                                col_type = "Boolean"
                            elif isinstance(value, datetime.datetime):
                                col_type = "DateTime"
                            
                            dataset_create.tables[0].columns.append({
                                "name": col,
                                "data_type": col_type
                            })
            
            # Create the dataset
            created_dataset = await self.create_push_dataset(dataset_create, report.workspace_id)
            dataset_id = created_dataset.get('id')
            
            # Push data to the dataset
            rows = []
            if query_results.get('data') and query_results.get('columns'):
                columns = query_results['columns']
                data = query_results['data']
                
                for row in data:
                    row_data = {}
                    for i, col in enumerate(columns):
                        if i < len(row):
                            # Handle date/time values
                            if isinstance(row[i], (datetime.datetime, datetime.date)):
                                row_data[col] = row[i].isoformat()
                            else:
                                row_data[col] = row[i]
                    rows.append(row_data)
            
            await self.push_rows(dataset_id, "QueryResults", rows, report.workspace_id)
            
            # Create a new report in PowerBI
            token = await self.authenticate()
            
            url = f"{self.api_url}/datasets/{dataset_id}/Default.GenerateReport"
            if report.workspace_id:
                url = f"{self.api_url}/groups/{report.workspace_id}/datasets/{dataset_id}/Default.GenerateReport"
                
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            create_report_data = {
                "name": report.name,
                "description": report.description
            }
            
            response = requests.post(url, headers=headers, json=create_report_data)
            response.raise_for_status()
            
            report_data = response.json()
            
            # Save report information to database
            new_report = PowerBIReport(
                report_id=report_data.get('id'),
                name=report.name,
                description=report.description,
                workspace_id=report.workspace_id,
                dataset_id=dataset_id,
                created_by_id=user.id,
                created_at=datetime.datetime.utcnow(),
                embed_url=report_data.get('embedUrl')
            )
            
            db.add(new_report)
            db.commit()
            db.refresh(new_report)
            
            return {
                "report_id": report_data.get('id'),
                "name": report.name,
                "embed_url": report_data.get('embedUrl'),
                "dataset_id": dataset_id,
                "workspace_id": report.workspace_id
            }
            
        except Exception as e:
            logger.error(f"Error creating PowerBI report from query: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error creating PowerBI report: {str(e)}")
    
    async def save_workspace(
        self,
        workspace_id: str,
        name: str,
        description: Optional[str] = None,
        db: Session = None,
        user: User = None
    ) -> PowerBIWorkspace:
        """
        Save PowerBI workspace to database
        
        Args:
            workspace_id: PowerBI workspace ID
            name: Workspace name
            description: Workspace description
            db: Database session
            user: Current user
            
        Returns:
            Created workspace record
        """
        try:
            # Check if workspace exists
            existing = db.query(PowerBIWorkspace).filter(PowerBIWorkspace.workspace_id == workspace_id).first()
            
            if existing:
                # Update existing workspace
                existing.name = name
                existing.description = description
                existing.updated_at = datetime.datetime.utcnow()
                
                db.commit()
                db.refresh(existing)
                
                return existing
            
            # Create new workspace record
            workspace = PowerBIWorkspace(
                workspace_id=workspace_id,
                name=name,
                description=description,
                created_by_id=user.id if user else None,
                created_at=datetime.datetime.utcnow()
            )
            
            db.add(workspace)
            db.commit()
            db.refresh(workspace)
            
            return workspace
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error saving PowerBI workspace: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error saving PowerBI workspace: {str(e)}")

# Initialize PowerBI service
powerbi_service = PowerBIService()

# Son güncelleme: 2025-05-21 05:44:49
# Güncelleyen: Teeksss