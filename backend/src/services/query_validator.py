import sqlparse
from typing import Tuple, Optional
import re

class QueryValidator:
    def __init__(self):
        self.forbidden_keywords = ['DROP', 'DELETE', 'TRUNCATE', 'ALTER', 'CREATE']
        self.max_query_length = 5000
        
    def validate(self, query: str) -> Tuple[bool, Optional[str]]:
        # Length check
        if len(query) > self.max_query_length:
            return False, 'Query too long'
            
        # Basic SQL injection check
        if self._contains_dangerous_characters(query):
            return False, 'Query contains invalid characters'
            
        # Parse query
        try:
            parsed = sqlparse.parse(query)[0]
        except Exception:
            return False, 'Invalid SQL syntax'
            
        # Check query type
        if parsed.get_type().upper() in self.forbidden_keywords:
            return False, 'Operation not allowed'
            
        return True, None
        
    def _contains_dangerous_characters(self, query: str) -> bool:
        dangerous_patterns = [
            r'--',           # Comment
            r'/\*.*?\*/',    # Multi-line comment
            r';.*$',         # Multiple queries
            r'xp_.*',        # XP cmdshell
            r'exec.*'        # Exec commands
        ]
        
        return any(re.search(pattern, query, re.IGNORECASE) 
                  for pattern in dangerous_patterns)