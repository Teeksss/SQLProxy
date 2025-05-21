from typing import Dict, Optional, List, Tuple
import hashlib
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.query import QueryWhitelist
from app.query.parser import SQLAnalyzer

class QueryValidator:
    """
    Validates SQL queries against whitelist and enforces permissions.
    """
    
    def __init__(self, sql_analyzer: SQLAnalyzer):
        self.sql_analyzer = sql_analyzer
    
    def hash_query(self, sql: str) -> str:
        """
        Create a normalized hash of the SQL query for whitelist comparisons.
        Handles spacing, casing, and some variations to match similar queries.
        """
        # Normalize SQL (remove extra spaces, lowercase, etc.)
        normalized_sql = " ".join(sql.lower().split())
        # Create a SHA256 hash
        return hashlib.sha256(normalized_sql.encode()).hexdigest()
    
    def check_whitelist(self, sql: str, db: Session) -> Tuple[bool, Optional[QueryWhitelist]]:
        """
        Check if query is in the whitelist.
        
        Args:
            sql: The SQL query to check
            db: Database session
            
        Returns:
            Tuple of (is_whitelisted, whitelist_entry)
        """
        query_hash = self.hash_query(sql)
        
        # Look for the query in the whitelist
        whitelist_entry = db.query(QueryWhitelist).filter(
            QueryWhitelist.query_hash == query_hash
        ).first()
        
        if whitelist_entry:
            return True, whitelist_entry
        
        return False, None
    
    def validate_query(
        self, 
        sql: str, 
        user_role: str,
        target_server: str,
        db: Session,
        auto_approve: bool = False
    ) -> Dict:
        """
        Validate a query against whitelist and role permissions.
        
        Args:
            sql: The SQL query to execute
            user_role: Role of the requesting user
            target_server: Server ID where query will be executed
            db: Database session
            auto_approve: Whether to automatically approve new queries
            
        Returns:
            Dict with validation result:
            {
                'is_approved': bool,
                'status': str,
                'whitelist_id': Optional[int],
                'analysis': Dict,
                'error': Optional[str]
            }
        """
        # Analyze the query
        analysis = self.sql_analyzer.parse_query(sql)
        
        # Check if query is in whitelist
        is_whitelisted, whitelist_entry = self.check_whitelist(sql, db)
        
        # PowerBI role can only execute powerbi_only queries
        if user_role == 'powerbi' and (not is_whitelisted or not whitelist_entry.powerbi_only):
            return {
                'is_approved': False,
                'status': 'rejected',
                'whitelist_id': whitelist_entry.id if whitelist_entry else None,
                'analysis': analysis,
                'error': 'PowerBI users can only execute pre-approved PowerBI queries'
            }
        
        # Read-only users can only execute read queries
        if user_role == 'readonly' and analysis['query_type'] != 'read':
            return {
                'is_approved': False,
                'status': 'rejected',
                'whitelist_id': None,
                'analysis': analysis,
                'error': 'Read-only users can only execute SELECT queries'
            }
        
        # Analyst users can execute read/write but not DDL
        if user_role == 'analyst' and analysis['query_type'] == 'ddl':
            return {
                'is_approved': False,
                'status': 'rejected',
                'whitelist_id': None,
                'analysis': analysis,
                'error': 'Analyst users cannot execute DDL queries'
            }
        
        # If query is whitelisted, check server restrictions
        if is_whitelisted:
            # Check if this query is allowed on the target server
            if whitelist_entry.server_restrictions and target_server not in whitelist_entry.server_restrictions:
                return {
                    'is_approved': False,
                    'status': 'rejected',
                    'whitelist_id': whitelist_entry.id,
                    'analysis': analysis,
                    'error': f'This query is not allowed on server: {target_server}'
                }
            
            # Query is approved
            return {
                'is_approved': True,
                'status': 'approved',
                'whitelist_id': whitelist_entry.id,
                'analysis': analysis,
                'error': None
            }
        
        # Query is not whitelisted
        if user_role == 'admin' and auto_approve:
            # Auto-approve for admins if enabled
            query_hash = self.hash_query(sql)
            new_whitelist = QueryWhitelist(
                query_hash=query_hash,
                sql_query=sql,
                query_type=analysis['query_type'],
                approved_by="auto-system",
                server_restrictions=[target_server],
                powerbi_only=False
            )
            db.add(new_whitelist)
            db.commit()
            
            return {
                'is_approved': True,
                'status': 'auto-approved',
                'whitelist_id': new_whitelist.id,
                'analysis': analysis,
                'error': None
            }
        
        # Query needs admin approval
        return {
            'is_approved': False,
            'status': 'pending_approval',
            'whitelist_id': None,
            'analysis': analysis,
            'error': 'Query needs admin approval before execution'
        }