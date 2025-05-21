"""
Query similarity and automatic matching service for SQL Proxy.

This service provides functionality to detect similar queries and
automatically suggest whitelist matches based on semantic similarity.

Last updated: 2025-05-20 06:11:09
Updated by: Teeksss
"""

import re
import logging
import hashlib
import difflib
import datetime
from typing import List, Dict, Any, Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, or_, and_

from app.models.query import QueryWhitelist, AuditLog, PendingApproval
from app.db.session import get_db
from app.core.config import settings
from app.services.sql_parser import SQLParser

logger = logging.getLogger(__name__)

class QuerySimilarityService:
    """
    Service for detecting and handling similar SQL queries
    
    Provides functionality to normalize, compare, and find similar SQL queries
    based on both lexical and semantic patterns.
    """
    
    def __init__(self):
        """Initialize the query similarity service"""
        self.sql_parser = SQLParser()
        
        # Regex patterns for normalization
        self.patterns = {
            # Replace literals with placeholders
            'string_literals': (r"'[^']*'", "'?'"),
            'number_literals': (r"\b\d+\b", "?"),
            'date_literals': (r"DATE\s*'[^']*'", "DATE '?'"),
            
            # Normalize whitespace
            'whitespace': (r"\s+", " "),
            
            # Remove comments
            'line_comments': (r"--.*?$", ""),
            'block_comments': (r"/\*.*?\*/", ""),
            
            # Handle common aliases
            'aliases': (r"\bAS\s+[a-zA-Z0-9_]+\b", " AS alias"),
            
            # Normalize IN clauses
            'in_clause': (r"IN\s*\([^)]+\)", "IN (?)"),
            
            # Normalize BETWEEN clauses
            'between_clause': (r"BETWEEN\s+[^AND]+\s+AND\s+[^WHERE|ORDER|GROUP|HAVING|LIMIT|$]+", "BETWEEN ? AND ?")
        }
        
        # Similarity thresholds
        self.exact_threshold = 0.98     # Consider queries identical above this similarity
        self.high_threshold = 0.90      # High similarity threshold
        self.medium_threshold = 0.75    # Medium similarity threshold
        self.low_threshold = 0.60       # Low similarity threshold
        
        # Normalization level
        self.normalization_level = settings.QUERY_NORMALIZATION_LEVEL if hasattr(settings, 'QUERY_NORMALIZATION_LEVEL') else 'medium'
        
        logger.info("Query similarity service initialized")
    
    def normalize_query(self, query: str, level: str = None) -> str:
        """
        Normalize a SQL query for comparison
        
        Args:
            query: SQL query to normalize
            level: Normalization level (basic, medium, high)
                  - basic: Normalize whitespace and comments only
                  - medium: Also normalize literals and simple clauses
                  - high: Maximum normalization including structure analysis
        
        Returns:
            Normalized query
        """
        if not query:
            return ""
        
        # Use service default if level not provided
        level = level or self.normalization_level
        
        # Start with basic normalization
        normalized = query.strip()
        
        # Remove comments
        normalized = re.sub(self.patterns['line_comments'][0], self.patterns['line_comments'][1], normalized, flags=re.MULTILINE)
        normalized = re.sub(self.patterns['block_comments'][0], self.patterns['block_comments'][1], normalized, flags=re.DOTALL)
        
        # Normalize whitespace
        normalized = re.sub(self.patterns['whitespace'][0], self.patterns['whitespace'][1], normalized)
        
        # Stop here if basic level
        if level == 'basic':
            return normalized
        
        # Medium level normalization
        if level in ('medium', 'high'):
            # Replace literals with placeholders
            normalized = re.sub(self.patterns['string_literals'][0], self.patterns['string_literals'][1], normalized)
            normalized = re.sub(self.patterns['number_literals'][0], self.patterns['number_literals'][1], normalized)
            normalized = re.sub(self.patterns['date_literals'][0], self.patterns['date_literals'][1], normalized)
            
            # Normalize IN and BETWEEN clauses
            normalized = re.sub(self.patterns['in_clause'][0], self.patterns['in_clause'][1], normalized)
            normalized = re.sub(self.patterns['between_clause'][0], self.patterns['between_clause'][1], normalized)
            
            # Normalize common aliases
            normalized = re.sub(self.patterns['aliases'][0], self.patterns['aliases'][1], normalized, flags=re.IGNORECASE)
        
        # High level normalization
        if level == 'high':
            try:
                # Parse the query and extract structural information
                parsed = self.sql_parser.parse_query(query)
                
                if parsed:
                    # Recreate a normalized query focusing on structure
                    structure = []
                    
                    # Query type
                    structure.append(parsed.get('query_type', 'SELECT').upper())
                    
                    # Selected columns or tables (for non-SELECT queries)
                    if 'columns' in parsed and parsed.get('query_type', '').upper() == 'SELECT':
                        structure.append("columns")  # Just indicate columns exist
                    
                    # FROM clause and tables
                    if 'tables' in parsed:
                        structure.append("FROM tables")
                    
                    # JOIN clauses if present
                    if 'joins' in parsed and parsed['joins']:
                        for join in parsed['joins']:
                            join_type = join.get('type', 'JOIN').upper()
                            structure.append(f"{join_type} table")
                    
                    # WHERE clause if present
                    if 'where' in parsed and parsed['where']:
                        structure.append("WHERE conditions")
                    
                    # GROUP BY, HAVING, ORDER BY, LIMIT clauses if present
                    for clause in ['group_by', 'having', 'order_by', 'limit']:
                        if clause in parsed and parsed[clause]:
                            structure.append(clause.replace('_', ' ').upper())
                    
                    # Build the structural representation
                    normalized = " ".join(structure)
            except Exception as e:
                logger.warning(f"Error during high-level query normalization: {str(e)}")
        
        return normalized
    
    def compare_queries(self, query1: str, query2: str, level: str = None) -> float:
        """
        Compare two SQL queries and return a similarity score
        
        Args:
            query1: First SQL query
            query2: Second SQL query
            level: Normalization level
        
        Returns:
            Similarity score between 0.0 and 1.0
        """
        if not query1 or not query2:
            return 0.0
        
        # Normalize both queries
        normalized1 = self.normalize_query(query1, level)
        normalized2 = self.normalize_query(query2, level)
        
        # Compare using difflib's SequenceMatcher
        similarity = difflib.SequenceMatcher(None, normalized1, normalized2).ratio()
        
        return similarity
    
    def find_similar_whitelisted_queries(
        self, 
        query: str, 
        server_alias: str = None,
        threshold: float = None, 
        db: Session = None
    ) -> List[Dict[str, Any]]:
        """
        Find similar queries in the whitelist
        
        Args:
            query: SQL query to match
            server_alias: Optional server alias to filter by
            threshold: Minimum similarity threshold (defaults to low_threshold)
            db: Database session
        
        Returns:
            List of similar whitelist entries with similarity scores
        """
        # Use default threshold if not provided
        threshold = threshold or self.low_threshold
        
        # Get database session
        close_db = False
        if db is None:
            db = next(get_db())
            close_db = True
        
        try:
            # Get all active whitelist entries
            query_builder = db.query(QueryWhitelist).filter(QueryWhitelist.is_active == True)
            
            # Filter by server if provided
            if server_alias:
                query_builder = query_builder.filter(
                    or_(
                        QueryWhitelist.server_restrictions.is_(None),
                        QueryWhitelist.server_restrictions == "[]",
                        QueryWhitelist.server_restrictions.contains(server_alias)
                    )
                )
            
            whitelist_entries = query_builder.all()
            
            # Calculate similarity for each entry
            similar_entries = []
            
            for entry in whitelist_entries:
                similarity = self.compare_queries(query, entry.query_text)
                
                if similarity >= threshold:
                    similar_entries.append({
                        "id": entry.id,
                        "whitelist_query": entry.query_text,
                        "similarity": similarity,
                        "similarity_level": self._get_similarity_level(similarity),
                        "created_by": entry.created_by,
                        "created_at": entry.created_at.isoformat(),
                        "server_restrictions": entry.server_restrictions,
                        "description": entry.description
                    })
            
            # Sort by similarity (highest first)
            similar_entries.sort(key=lambda x: x["similarity"], reverse=True)
            
            return similar_entries
        finally:
            if close_db:
                db.close()
    
    def find_similar_historical_queries(
        self, 
        query: str, 
        server_alias: str = None,
        username: str = None,
        days_back: int = 30,
        limit: int = 10,
        threshold: float = None,
        db: Session = None
    ) -> List[Dict[str, Any]]:
        """
        Find similar queries in the query history
        
        Args:
            query: SQL query to match
            server_alias: Optional server alias to filter by
            username: Optional username to filter by
            days_back: Number of days to look back in history
            limit: Maximum number of results
            threshold: Minimum similarity threshold
            db: Database session
        
        Returns:
            List of similar audit log entries with similarity scores
        """
        # Use default threshold if not provided
        threshold = threshold or self.low_threshold
        
        # Get database session
        close_db = False
        if db is None:
            db = next(get_db())
            close_db = True
        
        try:
            # Calculate cutoff date
            cutoff_date = datetime.datetime.utcnow() - datetime.timedelta(days=days_back)
            
            # Build query
            query_builder = db.query(AuditLog).filter(
                AuditLog.execution_status == 'success',
                AuditLog.created_at >= cutoff_date
            )
            
            # Apply filters
            if server_alias:
                query_builder = query_builder.filter(AuditLog.target_server == server_alias)
            
            if username:
                query_builder = query_builder.filter(AuditLog.username == username)
            
            # Get audit logs, ordered by most recent
            audit_logs = query_builder.order_by(desc(AuditLog.created_at)).limit(500).all()
            
            # Calculate similarity for each entry
            similar_entries = []
            
            for log in audit_logs:
                similarity = self.compare_queries(query, log.query_text)
                
                if similarity >= threshold:
                    similar_entries.append({
                        "id": log.id,
                        "historical_query": log.query_text,
                        "similarity": similarity,
                        "similarity_level": self._get_similarity_level(similarity),
                        "username": log.username,
                        "user_role": log.user_role,
                        "target_server": log.target_server,
                        "execution_time_ms": log.execution_time_ms,
                        "executed_at": log.created_at.isoformat()
                    })
            
            # Sort by similarity (highest first)
            similar_entries.sort(key=lambda x: x["similarity"], reverse=True)
            
            # Limit results
            return similar_entries[:limit]
        finally:
            if close_db:
                db.close()
    
    def _get_similarity_level(self, similarity: float) -> str:
        """
        Convert a similarity score to a human-readable level
        
        Args:
            similarity: Similarity score (0.0 - 1.0)
        
        Returns:
            Similarity level string (exact, high, medium, low)
        """
        if similarity >= self.exact_threshold:
            return "exact"
        elif similarity >= self.high_threshold:
            return "high"
        elif similarity >= self.medium_threshold:
            return "medium"
        elif similarity >= self.low_threshold:
            return "low"
        else:
            return "none"
    
    def suggest_whitelist_entry(
        self, 
        query: str, 
        server_alias: str = None,
        username: str = None,
        db: Session = None
    ) -> Dict[str, Any]:
        """
        Suggest a whitelist entry for a query
        
        Args:
            query: SQL query to suggest for
            server_alias: Optional server alias
            username: Optional username
            db: Database session
        
        Returns:
            Suggestion object with whitelist recommendation
        """
        # Get database session
        close_db = False
        if db is None:
            db = next(get_db())
            close_db = True
        
        try:
            # Check if the query is already whitelisted
            similar_whitelist = self.find_similar_whitelisted_queries(
                query, 
                server_alias, 
                self.high_threshold, 
                db
            )
            
            if similar_whitelist:
                # Query is already whitelisted or very similar to a whitelisted query
                top_match = similar_whitelist[0]
                
                if top_match["similarity"] >= self.exact_threshold:
                    return {
                        "suggestion_type": "already_whitelisted",
                        "message": "This query is already whitelisted",
                        "match": top_match
                    }
                else:
                    return {
                        "suggestion_type": "similar_whitelist",
                        "message": "This query is similar to an existing whitelist entry",
                        "match": top_match
                    }
            
            # Check for similar successful historical queries
            similar_history = self.find_similar_historical_queries(
                query,
                server_alias,
                None,  # Don't filter by username for whitelist suggestion
                90,    # Look back 90 days
                5,     # Top 5 matches
                self.high_threshold,
                db
            )
            
            if similar_history:
                # Found similar historical queries that executed successfully
                top_match = similar_history[0]
                
                if top_match["similarity"] >= self.exact_threshold:
                    return {
                        "suggestion_type": "historical_exact",
                        "message": "This query has been executed successfully before",
                        "match": top_match
                    }
                else:
                    return {
                        "suggestion_type": "historical_similar",
                        "message": "This query is similar to previously executed queries",
                        "match": top_match,
                        "all_matches": similar_history[:3]  # Top 3 matches
                    }
            
            # No similar whitelist entries or historical queries
            return {
                "suggestion_type": "new_query",
                "message": "This appears to be a new query pattern",
                "analyzed_query": self.sql_parser.parse_query(query)
            }
        finally:
            if close_db:
                db.close()
    
    def auto_approve_similar(
        self,
        pending_approval_id: int,
        approval_user: str,
        similarity_threshold: float = None,
        db: Session = None
    ) -> Optional[Dict[str, Any]]:
        """
        Automatically approve a pending query if it's similar to a whitelisted query
        
        Args:
            pending_approval_id: ID of the pending approval
            approval_user: Username of the auto-approval user
            similarity_threshold: Similarity threshold for auto-approval
            db: Database session
        
        Returns:
            Approval result or None if query wasn't auto-approved
        """
        # Use default threshold if not provided (higher threshold for auto-approval)
        similarity_threshold = similarity_threshold or self.high_threshold
        
        # Get database session
        close_db = False
        if db is None:
            db = next(get_db())
            close_db = True
        
        try:
            # Get the pending approval
            pending_approval = db.query(PendingApproval).filter(
                PendingApproval.id == pending_approval_id,
                PendingApproval.status == 'pending'
            ).first()
            
            if not pending_approval:
                logger.warning(f"Pending approval {pending_approval_id} not found or not pending")
                return None
            
            # Find similar whitelist entries
            similar_whitelist = self.find_similar_whitelisted_queries(
                pending_approval.query_text,
                pending_approval.target_server,
                similarity_threshold,
                db
            )
            
            if not similar_whitelist:
                logger.info(f"No similar whitelist entries found for approval {pending_approval_id}")
                return None
            
            # Get the top match
            top_match = similar_whitelist[0]
            
            # Check if it's similar enough for auto-approval
            if top_match["similarity"] >= similarity_threshold:
                # Auto-approve the query
                pending_approval.status = 'approved'
                pending_approval.approved_by = approval_user
                pending_approval.approved_at = datetime.datetime.utcnow()
                pending_approval.add_to_whitelist = pending_approval.will_repeat
                pending_approval.approver_comment = f"Auto-approved based on similarity to whitelist entry #{top_match['id']} ({top_match['similarity']:.2%} similar)"
                
                db.commit()
                
                return {
                    "approved": True,
                    "approval_id": pending_approval.id,
                    "match": top_match,
                    "add_to_whitelist": pending_approval.add_to_whitelist
                }
            
            return None
        finally:
            if close_db:
                db.close()

# Singleton instance
query_similarity_service = QuerySimilarityService()

# Son güncelleme: 2025-05-20 06:11:09
# Güncelleyen: Teeksss