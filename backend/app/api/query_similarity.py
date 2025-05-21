"""
Query similarity and pattern matching API endpoints for SQL Proxy.

These endpoints provide functionality to find similar queries, suggest whitelist
entries, and analyze query patterns.

Last updated: 2025-05-20 06:53:16
Updated by: Teeksss
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Body, Path
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

from app.db.session import get_db
from app.auth.jwt import get_current_user, TokenData
from app.models.query import QueryWhitelist, AuditLog, PendingApproval
from app.services.query_similarity import query_similarity_service
from app.services.sql_parser import SQLParser

router = APIRouter()
logger = logging.getLogger(__name__)
sql_parser = SQLParser()

@router.post("/compare", response_model=Dict[str, Any])
async def compare_queries(
    data: Dict[str, Any] = Body(...),
    normalization_level: Optional[str] = Query("medium", description="Normalization level (basic, medium, high)"),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Compare two SQL queries for similarity
    
    Returns similarity score and normalized queries
    """
    # Validate request data
    if "query1" not in data or "query2" not in data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Both query1 and query2 are required"
        )
    
    query1 = data["query1"]
    query2 = data["query2"]
    
    # Normalize queries
    normalized1 = query_similarity_service.normalize_query(query1, normalization_level)
    normalized2 = query_similarity_service.normalize_query(query2, normalization_level)
    
    # Calculate similarity
    similarity = query_similarity_service.compare_queries(query1, query2, normalization_level)
    
    # Get similarity level
    similarity_level = query_similarity_service._get_similarity_level(similarity)
    
    return {
        "similarity": similarity,
        "similarity_level": similarity_level,
        "normalized_query1": normalized1,
        "normalized_query2": normalized2,
        "normalization_level": normalization_level
    }

@router.post("/whitelist-matches", response_model=Dict[str, Any])
async def find_whitelist_matches(
    data: Dict[str, Any] = Body(...),
    min_similarity: float = Query(0.6, description="Minimum similarity threshold"),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Find matches in the whitelist for a given query
    
    Returns list of similar whitelist entries
    """
    # Validate request
    if "query" not in data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query is required"
        )
    
    query = data["query"]
    server_alias = data.get("server_alias")
    
    # Find similar whitelist entries
    similar_entries = query_similarity_service.find_similar_whitelisted_queries(
        query,
        server_alias,
        min_similarity,
        db
    )
    
    return {
        "query": query[:100] + ("..." if len(query) > 100 else ""),
        "server_alias": server_alias,
        "min_similarity": min_similarity,
        "matches_found": len(similar_entries),
        "matches": similar_entries
    }

@router.post("/history-matches", response_model=Dict[str, Any])
async def find_history_matches(
    data: Dict[str, Any] = Body(...),
    min_similarity: float = Query(0.6, description="Minimum similarity threshold"),
    days_back: int = Query(30, description="Days to look back in history"),
    limit: int = Query(10, description="Maximum number of results"),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Find matches in the query history for a given query
    
    Returns list of similar historical queries
    """
    # Validate request
    if "query" not in data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query is required"
        )
    
    query = data["query"]
    server_alias = data.get("server_alias")
    username = data.get("username")
    
    # Admin users can search anyone's history, non-admin only their own
    if current_user.role != "admin" and username and username != current_user.username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only search your own query history"
        )
    
    # If not specified, default to current user for non-admins
    if not username and current_user.role != "admin":
        username = current_user.username
    
    # Find similar historical queries
    similar_entries = query_similarity_service.find_similar_historical_queries(
        query,
        server_alias,
        username,
        days_back,
        limit,
        min_similarity,
        db
    )
    
    return {
        "query": query[:100] + ("..." if len(query) > 100 else ""),
        "server_alias": server_alias,
        "username": username,
        "days_back": days_back,
        "min_similarity": min_similarity,
        "matches_found": len(similar_entries),
        "matches": similar_entries
    }

@router.post("/analyze", response_model=Dict[str, Any])
async def analyze_query(
    data: Dict[str, Any] = Body(...),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Analyze a SQL query and provide structure, tables, columns, etc.
    
    Returns detailed analysis of the query
    """
    # Validate request
    if "query" not in data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query is required"
        )
    
    query = data["query"]
    
    # Parse and analyze the query
    try:
        analysis = sql_parser.parse_query(query)
        
        if not analysis:
            return {
                "success": False,
                "message": "Failed to parse query",
                "query": query[:100] + ("..." if len(query) > 100 else "")
            }
        
        # Check for tables that might be updated or deleted
        risk_level = "low"
        risk_reasons = []
        
        if analysis.get("query_type") in ["UPDATE", "DELETE", "TRUNCATE", "DROP", "ALTER"]:
            risk_level = "high"
            risk_reasons.append(f"{analysis.get('query_type')} operation detected")
        
        if not analysis.get("where") and analysis.get("query_type") in ["UPDATE", "DELETE"]:
            risk_level = "critical"
            risk_reasons.append("Mass update/delete without WHERE clause")
        
        if analysis.get("query_type") == "SELECT" and analysis.get("limit") is None:
            risk_level = "medium"
            risk_reasons.append("SELECT without LIMIT clause")
        
        # Add the risk assessment to the analysis
        analysis["risk_assessment"] = {
            "risk_level": risk_level,
            "risk_reasons": risk_reasons
        }
        
        return {
            "success": True,
            "query": query[:100] + ("..." if len(query) > 100 else ""),
            "analysis": analysis
        }
    except Exception as e:
        logger.error(f"Error analyzing query: {str(e)}")
        return {
            "success": False,
            "message": f"Error analyzing query: {str(e)}",
            "query": query[:100] + ("..." if len(query) > 100 else "")
        }

@router.post("/suggest-whitelist", response_model=Dict[str, Any])
async def suggest_whitelist_entry(
    data: Dict[str, Any] = Body(...),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Suggest a whitelist entry for a given query
    
    Analyzes the query and provides suggested whitelist entries
    """
    # Validate request
    if "query" not in data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query is required"
        )
    
    query = data["query"]
    server_alias = data.get("server_alias")
    
    # Get suggestion
    suggestion = query_similarity_service.suggest_whitelist_entry(
        query,
        server_alias,
        current_user.username,
        db
    )
    
    return {
        "query": query[:100] + ("..." if len(query) > 100 else ""),
        "server_alias": server_alias,
        "suggestion": suggestion
    }

@router.post("/auto-approve/{pending_id}", response_model=Dict[str, Any])
async def auto_approve_query(
    pending_id: int = Path(..., title="Pending approval ID"),
    min_similarity: float = Query(0.9, description="Minimum similarity threshold for auto-approval"),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Try to automatically approve a pending query based on similarity
    
    Checks if the query is similar to existing whitelist entries and auto-approves if similar enough
    """
    # Only admin users can trigger auto-approval
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can auto-approve queries"
        )
    
    # Check if the pending approval exists
    pending_approval = db.query(PendingApproval).filter(
        PendingApproval.id == pending_id,
        PendingApproval.status == 'pending'
    ).first()
    
    if not pending_approval:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pending approval with ID {pending_id} not found or not pending"
        )
    
    # Try to auto-approve the query
    auto_approval_result = query_similarity_service.auto_approve_similar(
        pending_id,
        current_user.username,
        min_similarity,
        db
    )
    
    if auto_approval_result:
        return {
            "success": True,
            "message": "Query auto-approved based on similarity",
            "approval_id": pending_id,
            "similarity": auto_approval_result["match"]["similarity"],
            "matched_whitelist_id": auto_approval_result["match"]["id"]
        }
    else:
        return {
            "success": False,
            "message": "No similar whitelist entries found for auto-approval",
            "approval_id": pending_id
        }

@router.post("/batch-auto-approve", response_model=Dict[str, Any])
async def batch_auto_approve(
    data: Dict[str, Any] = Body(...),
    min_similarity: float = Query(0.9, description="Minimum similarity threshold for auto-approval"),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Try to automatically approve multiple pending queries based on similarity
    
    Batch processes pending approval queue for auto-approval
    """
    # Only admin users can trigger auto-approval
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can auto-approve queries"
        )
    
    # Get the maximum number of queries to process
    max_queries = data.get("max_queries", 50)
    
    # Get pending approvals
    pending_approvals = db.query(PendingApproval).filter(
        PendingApproval.status == 'pending'
    ).order_by(PendingApproval.created_at).limit(max_queries).all()
    
    # Process each pending approval
    results = {
        "total_processed": len(pending_approvals),
        "auto_approved": 0,
        "not_approved": 0,
        "approved_details": []
    }
    
    for approval in pending_approvals:
        auto_approval_result = query_similarity_service.auto_approve_similar(
            approval.id,
            current_user.username,
            min_similarity,
            db
        )
        
        if auto_approval_result:
            results["auto_approved"] += 1
            results["approved_details"].append({
                "approval_id": approval.id,
                "query": approval.query_text[:100] + ("..." if len(approval.query_text) > 100 else ""),
                "similarity": auto_approval_result["match"]["similarity"],
                "matched_whitelist_id": auto_approval_result["match"]["id"]
            })
        else:
            results["not_approved"] += 1
    
    return results

# Son güncelleme: 2025-05-20 06:53:16
# Güncelleyen: Teeksss