"""
SQL Query Parser Module
"""
import re
from typing import Dict, Any, List, Optional

class QueryParser:
    """
    Parses SQL queries to extract query type and structure
    """
    
    def __init__(self):
        """Initialize query parser"""
        # Regex patterns for different query types
        self.patterns = {
            'select': re.compile(r'^\s*SELECT', re.IGNORECASE),
            'insert': re.compile(r'^\s*INSERT', re.IGNORECASE),
            'update': re.compile(r'^\s*UPDATE', re.IGNORECASE),
            'delete': re.compile(r'^\s*DELETE', re.IGNORECASE),
            'create': re.compile(r'^\s*CREATE', re.IGNORECASE),
            'alter': re.compile(r'^\s*ALTER', re.IGNORECASE),
            'drop': re.compile(r'^\s*DROP', re.IGNORECASE),
            'truncate': re.compile(r'^\s*TRUNCATE', re.IGNORECASE),
            'show': re.compile(r'^\s*SHOW', re.IGNORECASE),
            'describe': re.compile(r'^\s*DESCRIBE|DESC', re.IGNORECASE),
            'explain': re.compile(r'^\s*EXPLAIN', re.IGNORECASE),
            'begin': re.compile(r'^\s*BEGIN', re.IGNORECASE),
            'commit': re.compile(r'^\s*COMMIT', re.IGNORECASE),
            'rollback': re.compile(r'^\s*ROLLBACK', re.IGNORECASE)
        }
        
        # Extract table names
        self.table_pattern = re.compile(
            r'(?:FROM|JOIN|UPDATE|INTO)\s+([a-zA-Z0-9_\.]+)', 
            re.IGNORECASE
        )
        
        # Extract columns for SELECT queries
        self.column_pattern = re.compile(
            r'SELECT\s+(.*?)\s+FROM', 
            re.IGNORECASE | re.DOTALL
        )
        
        # Extract WHERE conditions
        self.where_pattern = re.compile(
            r'WHERE\s+(.*?)(?:ORDER BY|GROUP BY|HAVING|LIMIT|$)', 
            re.IGNORECASE | re.DOTALL
        )
    
    def parse(self, query: str