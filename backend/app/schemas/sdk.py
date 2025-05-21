"""
SDK schemas for SQL Proxy

This module provides Pydantic schemas for validating and serializing
SDK generation configurations and responses.

Last updated: 2025-05-21 05:35:49
Updated by: Teeksss
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum

class SDKLanguage(str, Enum):
    """SDK language options"""
    PYTHON = "python"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    # More languages can be added in the future

class APIEndpoint(BaseModel):
    """API endpoint configuration for SDK"""
    path_prefix: str = Field(..., description="API path prefix")
    class_name: str = Field(..., description="Class name for the endpoint")
    description: Optional[str] = Field(None, description="Description of the endpoint")

class SDKConfig(BaseModel):
    """SDK generation configuration"""
    language: SDKLanguage = Field(..., description="SDK language")
    version: str = Field(..., description="SDK version")
    name: str = Field("SQL Proxy Client", description="SDK name")
    description: str = Field("Client SDK for SQL Proxy API", description="SDK description")
    author: str = Field("SQL Proxy Team", description="SDK author")
    license: str = Field("MIT", description="SDK license")
    package_name: str = Field(..., description="Package name (e.g., 'sqlproxy' for Python)")
    base_url: str = Field("http://localhost:8000", description="Base URL for API")
    endpoints: List[APIEndpoint] = Field(default_factory=list, description="API endpoints to include")
    excluded_models: List[str] = Field(default_factory=list, description="Models to exclude")
    dependencies: Dict[str, str] = Field(default_factory=dict, description="Dependencies and versions")
    package_as_jar: bool = Field(False, description="Package Java SDK as JAR")

class SDKGenerationResponse(BaseModel):
    """SDK generation response"""
    message: str = Field(..., description="Response message")
    language: SDKLanguage = Field(..., description="SDK language")
    version: str = Field(..., description="SDK version")
    output_path: str = Field(..., description="Output path")
    status: str = Field(..., description="Generation status")

# Son güncelleme: 2025-05-21 05:35:49
# Güncelleyen: Teeksss