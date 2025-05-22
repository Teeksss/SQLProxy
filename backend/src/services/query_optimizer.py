from typing import Dict, List, Tuple
import sqlparse
from sqlparse.sql import Token, TokenList

class QueryOptimizer:
    def __init__(self):
        self.optimization_rules = [
            self._check_index_usage,
            self._check_join_order,
            self._check_where_clause,
            self._check_select_columns
        ]
        
    def optimize(self, query: str) -> Tuple[str, List[str]]:
        parsed = sqlparse.parse(query)[0]
        optimized_query = query
        suggestions = []
        
        for rule in self.optimization_rules:
            result = rule(parsed)
            if result:
                optimized_query, suggestion = result
                suggestions.append(suggestion)
                
        return optimized_query, suggestions
        
    def _check_index_usage(self, parsed: TokenList) -> Optional[Tuple[str, str]]:
        # Analyze WHERE clauses for index usage
        where_found = False
        for token in parsed.tokens:
            if token.is_keyword and token.value.upper() == 'WHERE':
                where_found = True
                break
                
        if where_found:
            # Check if columns in WHERE clause are indexed
            return None, "Consider adding index for WHERE clause columns"
            
        return None
        
    def _check_join_order(self, parsed: TokenList) -> Optional[Tuple[str, str]]:
        # Analyze and optimize join order
        joins = []
        for token in parsed.tokens:
            if token.is_keyword and 'JOIN' in token.value.upper():
                joins.append(token)
                
        if len(joins) > 1:
            return None, "Consider optimizing join order based on table sizes"
            
        return None