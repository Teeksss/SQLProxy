"""
Data Masking schemas for SQL Proxy

This module provides Pydantic schemas for validating and serializing
data masking rules and associated data.

Last updated: 2025-05-20 14:59:32
Updated by: Teeksss
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

from app.models.masking import MaskingType

class MaskingRuleBase(BaseModel):
    """Base schema for masking rules"""
    name: str = Field(..., description="Name of the masking rule")
    rule_type: MaskingType = Field(..., description="Type of masking rule (GLOBAL or COLUMN)")
    description: Optional[str] = Field(None, description="Description of the masking rule")
    masking_method: str = Field(..., description="Method used for masking (redact, hash, partial, tokenize)")

class MaskingRuleCreate(MaskingRuleBase):
    """Schema for creating a masking rule"""
    pattern: Optional[str] = Field(None, description="Regex pattern for matching data (for GLOBAL rules)")
    column_name: Optional[str] = Field(None, description="Column name to mask (for COLUMN rules)")

class MaskingRuleUpdate(BaseModel):
    """Schema for updating a masking rule"""
    name: Optional[str] = Field(None, description="Name of the masking rule")
    description: Optional[str] = Field(None, description="Description of the masking rule")
    masking_method: Optional[str] = Field(None, description="Method used for masking")
    pattern: Optional[str] = Field(None, description="Regex pattern for matching data (for GLOBAL rules)")
    column_name: Optional[str] = Field(None, description="Column name to mask (for COLUMN rules)")
    enabled: Optional[bool] = Field(None, description="Whether the rule is enabled")

class MaskingRuleResponse(MaskingRuleBase):
    """Schema for masking rule response"""
    id: int = Field(..., description="Unique identifier for the masking rule")
    pattern: Optional[str] = Field(None, description="Regex pattern for matching data (for GLOBAL rules)")
    column_name: Optional[str] = Field(None, description="Column name to mask (for COLUMN rules)")
    enabled: bool = Field(..., description="Whether the rule is enabled")
    created_at: Optional[datetime] = Field(None, description="When the rule was created")
    updated_at: Optional[datetime] = Field(None, description="When the rule was last updated")

    class Config:
        orm_mode = True

class MaskingRuleInDB(MaskingRuleResponse):
    """Schema for masking rule in database (internal use)"""
    pass

class MaskingRulesResponse(BaseModel):
    """Schema for response containing all masking rules"""
    global_rules: List[Dict[str, Any]] = Field(..., description="List of global masking rules")
    column_rules: List[Dict[str, Any]] = Field(..., description="List of column-specific masking rules")

class MaskingRuleTest(BaseModel):
    """Schema for testing a masking rule"""
    rule_type: MaskingType = Field(..., description="Type of masking rule (GLOBAL or COLUMN)")
    masking_method: str = Field(..., description="Method used for masking")
    pattern: Optional[str] = Field(None, description="Regex pattern for matching data (for GLOBAL rules)")
    column_name: Optional[str] = Field(None, description="Column name to mask (for COLUMN rules)")
    test_data: Optional[List[str]] = Field(None, description="Sample data to test against")

class MaskingRuleTestResponse(BaseModel):
    """Schema for masking rule test response"""
    rule_type: MaskingType = Field(..., description="Type of masking rule")
    masking_method: str = Field(..., description="Method used for masking")
    pattern: Optional[str] = Field(None, description="Regex pattern for matching data")
    column_name: Optional[str] = Field(None, description="Column name to mask")
    results: List[Dict[str, Any]] = Field(..., description="Test results")

# Son güncelleme: 2025-05-20 14:59:32
# Güncelleyen: Teeksss