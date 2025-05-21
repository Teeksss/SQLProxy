"""
Data Masking API endpoints for SQL Proxy

This module provides API endpoints for managing data masking rules
and testing masking functionality.

Last updated: 2025-05-20 14:44:45
Updated by: Teeksss
"""

from typing import List, Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.data_masking import data_masking_service
from app.models.masking import MaskingRule, MaskingType
from app.schemas.masking import (
    MaskingRuleCreate,
    MaskingRuleUpdate,
    MaskingRuleResponse,
    MaskingRulesResponse,
    MaskingRuleTest,
    MaskingRuleTestResponse
)
from app.api.deps import get_current_user_admin
from app.models.user import User

router = APIRouter()

@router.get("", response_model=MaskingRulesResponse)
async def get_masking_rules(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_admin)
) -> Any:
    """
    Get all masking rules
    """
    rules = await data_masking_service.get_masking_rules(db)
    return rules

@router.post("", response_model=MaskingRuleResponse)
async def create_masking_rule(
    rule: MaskingRuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_admin)
) -> Any:
    """
    Create a new masking rule
    """
    try:
        created_rule = await data_masking_service.create_masking_rule(
            db=db,
            name=rule.name,
            rule_type=rule.rule_type,
            description=rule.description,
            masking_method=rule.masking_method,
            pattern=rule.pattern,
            column_name=rule.column_name
        )
        
        return {
            "id": created_rule.id,
            "name": created_rule.name,
            "rule_type": created_rule.rule_type,
            "description": created_rule.description,
            "masking_method": created_rule.masking_method,
            "pattern": created_rule.pattern,
            "column_name": created_rule.column_name,
            "enabled": created_rule.enabled,
            "created_at": created_rule.created_at,
            "updated_at": created_rule.updated_at
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@router.put("/{rule_id}", response_model=MaskingRuleResponse)
async def update_masking_rule(
    rule_id: int = Path(..., description="The ID of the masking rule to update"),
    rule: MaskingRuleUpdate = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_admin)
) -> Any:
    """
    Update an existing masking rule
    """
    try:
        updated_rule = await data_masking_service.update_masking_rule(
            db=db,
            rule_id=rule_id,
            name=rule.name if rule else None,
            description=rule.description if rule else None,
            masking_method=rule.masking_method if rule else None,
            pattern=rule.pattern if rule else None,
            column_name=rule.column_name if rule else None,
            enabled=rule.enabled if rule else None
        )
        
        if not updated_rule:
            raise HTTPException(status_code=404, detail=f"Masking rule with ID {rule_id} not found")
        
        return {
            "id": updated_rule.id,
            "name": updated_rule.name,
            "rule_type": updated_rule.rule_type,
            "description": updated_rule.description,
            "masking_method": updated_rule.masking_method,
            "pattern": updated_rule.pattern,
            "column_name": updated_rule.column_name,
            "enabled": updated_rule.enabled,
            "created_at": updated_rule.created_at,
            "updated_at": updated_rule.updated_at
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@router.delete("/{rule_id}")
async def delete_masking_rule(
    rule_id: int = Path(..., description="The ID of the masking rule to delete"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_admin)
) -> Dict[str, Any]:
    """
    Delete a masking rule
    """
    try:
        deleted = await data_masking_service.delete_masking_rule(db=db, rule_id=rule_id)
        
        if not deleted:
            raise HTTPException(status_code=404, detail=f"Masking rule with ID {rule_id} not found")
        
        return {"message": f"Masking rule with ID {rule_id} deleted successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@router.post("/test", response_model=MaskingRuleTestResponse)
async def test_masking_rule(
    test: MaskingRuleTest,
    current_user: User = Depends(get_current_user_admin)
) -> Any:
    """
    Test a masking rule
    """
    try:
        test_results = await data_masking_service.test_masking_rule(
            rule_type=test.rule_type,
            masking_method=test.masking_method,
            pattern=test.pattern,
            column_name=test.column_name,
            test_data=test.test_data
        )
        
        return test_results
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@router.get("/enabled")
async def get_masking_status(
    current_user: User = Depends(get_current_user_admin)
) -> Dict[str, Any]:
    """
    Get data masking status
    """
    return {
        "enabled": data_masking_service.enabled,
        "rules_count": {
            "global": len(data_masking_service.global_rules),
            "column": len(data_masking_service.column_rules)
        }
    }

# Son güncelleme: 2025-05-20 14:44:45
# Güncelleyen: Teeksss