from typing import Dict, List, Optional
import sqlparse
from sqlparse.sql import Token, TokenList
import re

class SQLParser:
    def __init__(self):
        self.supported_operations = {
            'SELECT', 'INSERT', 'UPDATE', 'DELETE',
            'CREATE', 'ALTER', 'DROP', 'TRUNCATE'
        }
        
    def parse_query(self, query: str) -> Dict:
        """Detaylı SQL query analizi yapar."""
        parsed = sqlparse.parse(query)[0]
        
        return {
            'type': self._get_query_type(parsed),
            'tables': self._extract_tables(parsed),
            'columns': self._extract_columns(parsed),
            'conditions': self._extract_conditions(parsed),
            'joins': self._extract_joins(parsed),
            'subqueries': self._extract_subqueries(parsed),
            'parameters': self._extract_parameters(parsed)
        }
        
    def validate_query(self, query: str) -> Tuple[bool, Optional[str]]:
        """Query'nin geçerliliğini kontrol eder."""
        try:
            parsed = sqlparse.parse(query)[0]
            
            # Syntax kontrolü
            if not self._check_syntax(parsed):
                return False, "Invalid SQL syntax"
                
            # Operation type kontrolü
            if not self._check_operation_type(parsed):
                return False, "Unsupported operation type"
                
            # SQL injection kontrolü
            if self._check_sql_injection(query):
                return False, "Potential SQL injection detected"
                
            # Kompleks query kontrolü
            if not self._check_query_complexity(parsed):
                return False, "Query too complex"
                
            return True, None
            
        except Exception as e:
            return False, str(e)
            
    def _get_query_type(self, parsed: TokenList) -> str:
        """Query tipini belirler."""
        for token in parsed.tokens:
            if token.is_keyword and token.value.upper() in self.supported_operations:
                return token.value.upper()
        return 'UNKNOWN'
        
    def _extract_tables(self, parsed: TokenList) -> List[str]:
        """Query'de kullanılan tabloları çıkarır."""
        tables = []
        from_seen = False
        
        for token in parsed.tokens:
            if token.is_keyword and token.value.upper() == 'FROM':
                from_seen = True
            elif from_seen and token.ttype is None:
                tables.extend(
                    t.strip() for t in token.value.split(',')
                )
                from_seen = False
                
        return tables
        
    def _extract_columns(self, parsed: TokenList) -> List[str]:
        """Query'de kullanılan kolonları çıkarır."""
        columns = []
        select_seen = False
        
        for token in parsed.tokens:
            if token.is_keyword and token.value.upper() == 'SELECT':
                select_seen = True
            elif select_seen and token.ttype is None:
                if token.value.upper() != 'FROM':
                    columns.extend(
                        c.strip() for c in token.value.split(',')
                    )
                    
        return columns