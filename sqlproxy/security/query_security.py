import re
from typing import List, Optional

class SQLInjectionChecker:
    def __init__(self):
        self.patterns = [
            r';\s*DROP\s+TABLE',
            r';\s*DELETE\s+FROM',
            r';\s*UPDATE\s+.*\s+SET',
            r'UNION\s+SELECT',
            r'--',
            r'/\*.*\*/'
        ]
        
    def check_query(self, query: str) -> List[str]:
        """Check query for SQL injection patterns"""
        findings = []
        for pattern in self.patterns:
            if re.search(pattern, query, re.IGNORECASE):
                findings.append(f"Found potentially dangerous pattern: {pattern}")
        return findings