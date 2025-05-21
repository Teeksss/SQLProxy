"""
SQL Proxy API Integration Example

This script demonstrates how to integrate with the SQL Proxy API
using API keys for authentication and accessing data for external systems.

Last updated: 2025-05-20 10:00:16
Updated by: Teeksss
"""

import requests
import json
import pandas as pd
import time
import logging
from typing import Dict, List, Any, Optional, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('sql_proxy_client')

class SQLProxyClient:
    """
    Client for interacting with the SQL Proxy API
    
    Provides methods for authentication, query execution, and data retrieval
    for external systems like PowerBI, Tableau, or custom applications.
    """
    
    def __init__(self, base_url: str, api_key: Optional[str] = None):
        """
        Initialize the SQL Proxy client
        
        Args:
            base_url: Base URL of the SQL Proxy API
            api_key: Optional API key for authentication
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.token = None
        self.token_expiry = 0
        
        # Verify API URL is accessible
        try:
            response = requests.get(f"{self.base_url}/health")
            if response.status_code != 200:
                logger.warning(f"API health check failed: {response.status_code}")
        except Exception as e:
            logger.error(f"Error connecting to SQL Proxy API: {str(e)}")
    
    def authenticate(self, username: str, password: str) -> bool:
        """
        Authenticate with the SQL Proxy API using username and password
        
        Args:
            username: Username for authentication
            password: Password for authentication
            
        Returns:
            True if authentication successful, False otherwise
        """
        try:
            response = requests.post(
                f"{self.base_url}/api/auth/login",
                json={"username": username, "password": password}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                
                # Calculate token expiry time (subtract 5 minutes for safety)
                expires_in = data.get("expires_in", 3600)
                self.token_expiry = time.time() + expires_in - 300
                
                logger.info(f"Authentication successful for user {username}")
                return True
            else:
                logger.error(f"Authentication failed: {response.status_code} - {response.text}")
                return False
        
        except Exception as e:
            logger.error(f"Error during authentication: {str(e)}")
            return False
    
    def _get_auth_header(self) -> Dict[str, str]:
        """
        Get authorization header for API requests
        
        Returns:
            Dictionary with authorization header
        """
        if self.api_key:
            return {"X-API-Key": self.api_key}
        elif self.token:
            return {"Authorization": f"Bearer {self.token}"}
        else:
            return {}
    
    def _check_auth(self) -> bool:
        """
        Check if client is authenticated
        
        Returns:
            True if authenticated, False otherwise
        """
        if self.api_key:
            return True
        
        if not self.token or time.time() > self.token_expiry:
            logger.error("Not authenticated or token expired")
            return False
        
        return True
    
    def execute_query(
        self,
        query: str,
        server_alias: str,
        params: Optional[Dict[str, Any]] = None,
        timeout: int = 60
    ) -> Dict[str, Any]:
        """
        Execute a SQL query directly
        
        Args:
            query: SQL query to execute
            server_alias: Server alias to execute query on
            params: Optional parameters for the query
            timeout: Request timeout in seconds
            
        Returns:
            Dictionary with query results
        """
        if not self._check_auth():
            raise Exception("Not authenticated")
        
        try:
            response = requests.post(
                f"{self.base_url}/api/query/execute",
                headers=self._get_auth_header(),
                json={
                    "query": query,
                    "server_alias": server_alias,
                    "params": params or {}
                },
                timeout=timeout
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 202:
                # Query requires approval
                data = response.json()
                approval_id = data.get("approval_id")
                logger.info(f"Query requires approval: {approval_id}")
                return {"status": "approval_required", "approval_id": approval_id}
            else:
                logger.error(f"Query execution failed: {response.status_code} - {response.text}")
                raise Exception(f"Query execution failed: {response.text}")
        
        except Exception as e:
            logger.error(f"Error executing query: {str(e)}")
            raise
    
    def get_powerbi_query(
        self,
        query_id: str,
        format: str = "json",
        refresh_cache: bool = False,
        timeout: int = 60
    ) -> Union[Dict[str, Any], pd.DataFrame, bytes]:
        """
        Execute a pre-defined PowerBI query
        
        Args:
            query_id: ID of the pre-defined PowerBI query
            format: Response format (json, csv, excel)
            refresh_cache: Whether to force a cache refresh
            timeout: Request timeout in seconds
            
        Returns:
            Query results in the requested format
        """
        if not self._check_auth():
            raise Exception("Not authenticated")
        
        try:
            # Build URL with query parameters
            url = f"{self.base_url}/api/powerbi/query/{query_id}"
            params = {
                "format": format,
                "refresh_cache": "true" if refresh_cache else "false"
            }
            
            response = requests.get(
                url,
                headers=self._get_auth_header(),
                params=params,
                timeout=timeout
            )
            
            if response.status_code == 200:
                # Return data in appropriate format
                if format == "json":
                    return response.json()
                elif format == "csv":
                    return pd.read_csv(pd.StringIO(response.text))
                elif format == "excel":
                    return response.content
                else:
                    return response.content
            else:
                logger.error(f"PowerBI query execution failed: {response.status_code} - {response.text}")
                raise Exception(f"PowerBI query execution failed: {response.text}")
        
        except Exception as e:
            logger.error(f"Error executing PowerBI query: {str(e)}")
            raise
    
    def export_powerbi_dataset(
        self,
        dataset_id: str,
        filters: Dict[str, Any] = None,
        format: str = "json",
        timeout: int = 120
    ) -> Union[Dict[str, Any], pd.DataFrame, bytes]:
        """
        Export a pre-defined PowerBI dataset with optional filters
        
        Args:
            dataset_id: ID of the pre-defined PowerBI dataset
            filters: Optional filters to apply to the dataset
            format: Response format (json, csv, excel, parquet)
            timeout: Request timeout in seconds
            
        Returns:
            Dataset in the requested format
        """
        if not self._check_auth():
            raise Exception("Not authenticated")
        
        try:
            # Build URL with query parameters
            url = f"{self.base_url}/api/powerbi/dataset/{dataset_id}"
            params = {"format": format}
            
            response = requests.post(
                url,
                headers=self._get_auth_header(),
                params=params,
                json={"filters": filters or {}},
                timeout=timeout
            )
            
            if response.status_code == 200:
                # Return data in appropriate format
                if format == "json":
                    return response.json()
                elif format == "csv":
                    return pd.read_csv(pd.StringIO(response.text))
                elif format == "excel":
                    return pd.read_excel(pd.io.BytesIO(response.content))
                elif format == "parquet":
                    import pyarrow.parquet as pq
                    import io
                    buf = io.BytesIO(response.content)
                    return pq.read_table(buf).to_pandas()
                else:
                    return response.content
            else:
                logger.error(f"PowerBI dataset export failed: {response.status_code} - {response.text}")
                raise Exception(f"PowerBI dataset export failed: {response.text}")
        
        except Exception as e:
            logger.error(f"Error exporting PowerBI dataset: {str(e)}")
            raise
    
    def get_query_status(self, approval_id: int) -> Dict[str, Any]:
        """
        Check the status of a pending query approval
        
        Args:
            approval_id: ID of the pending approval
            
        Returns:
            Dictionary with approval status information
        """
        if not self._check_auth():
            raise Exception("Not authenticated")
        
        try:
            response = requests.get(
                f"{self.base_url}/api/query/approval/{approval_id}",
                headers=self._get_auth_header()
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get query status: {response.status_code} - {response.text}")
                raise Exception(f"Failed to get query status: {response.text}")
        
        except Exception as e:
            logger.error(f"Error getting query status: {str(e)}")
            raise
    
    def get_available_queries(self) -> Dict[str, Any]:
        """
        Get available PowerBI queries and datasets
        
        Returns:
            Dictionary with information about available queries and datasets
        """
        if not self._check_auth():
            raise Exception("Not authenticated")
        
        try:
            response = requests.get(
                f"{self.base_url}/api/powerbi/metadata",
                headers=self._get_auth_header()
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get available queries: {response.status_code} - {response.text}")
                raise Exception(f"Failed to get available queries: {response.text}")
        
        except Exception as e:
            logger.error(f"Error getting available queries: {str(e)}")
            raise

# Example usage
if __name__ == "__main__":
    # Initialize client
    client = SQLProxyClient(
        base_url="https://sql-proxy.example.com",
        api_key="your_api_key_here"  # or authenticate with username/password below
    )
    
    # Authenticate (alternative to API key)
    # client.authenticate("username", "password")
    
    try:
        # Example 1: Execute a direct query
        results = client.execute_query(
            query="SELECT * FROM customers WHERE region = 'Europe' LIMIT 100",
            server_alias="sales_db"
        )
        print(f"Query returned {results.get('rowcount', 0)} rows")
        
        # Example 2: Use a pre-defined PowerBI query
        powerbi_results = client.get_powerbi_query(
            query_id="monthly-sales-report",
            format="json",
            refresh_cache=True
        )
        print(f"PowerBI query returned {powerbi_results.get('rowcount', 0)} rows")
        
        # Example 3: Export a dataset with filters
        dataset_results = client.export_powerbi_dataset(
            dataset_id="customer-analysis",
            filters={"region": "Europe", "year": 2025},
            format="excel"
        )
        # Save Excel file
        with open("customer_analysis.xlsx", "wb") as f:
            f.write(dataset_results)
        print("Exported dataset to customer_analysis.xlsx")
        
        # Example 4: Get available queries and datasets
        metadata = client.get_available_queries()
        print(f"Available queries: {len(metadata.get('queries', []))}")
        print(f"Available datasets: {len(metadata.get('datasets', []))}")
        
    except Exception as e:
        print(f"Error: {e}")

# Son güncelleme: 2025-05-20 10:00:16
# Güncelleyen: Teeksss