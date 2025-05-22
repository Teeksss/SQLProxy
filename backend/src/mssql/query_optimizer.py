from typing import Dict, List, Optional
import sqlparse
from .execution_plan import ExecutionPlanAnalyzer

class MSSQLQueryOptimizer:
    def __init__(self):
        self.plan_analyzer = ExecutionPlanAnalyzer()
        
    def optimize(self, query: str) -> Dict:
        """Query optimizasyonu yapar."""
        parsed = sqlparse.parse(query)[0]
        
        optimizations = []
        original_query = query
        
        # Index önerileri
        index_suggestions = self._suggest_indexes(parsed)
        
        # Join optimizasyonu
        if join_opt := self._optimize_joins(parsed):
            optimizations.append(join_opt)
            query = join_opt['query']
            
        # Where clause optimizasyonu
        if where_opt := self._optimize_where(parsed):
            optimizations.append(where_opt)
            query = where_opt['query']
            
        # Execution plan analizi
        plan_analysis = self.plan_analyzer.analyze(query)
        
        return {
            'original_query': original_query,
            'optimized_query': query,
            'optimizations': optimizations,
            'index_suggestions': index_suggestions,
            'execution_plan': plan_analysis
        }
        
    def _suggest_indexes(self, parsed) -> List[Dict]:
        """Index önerileri oluşturur."""
        suggestions = []
        
        # WHERE clause analizi
        where_columns = self._extract_where_columns(parsed)
        for column in where_columns:
            suggestions.append({
                'type': 'INDEX',
                'column': column,
                'reason': 'Frequently used in WHERE clause'
            })
            
        # JOIN analizi
        join_columns = self._extract_join_columns(parsed)
        for column in join_columns:
            suggestions.append({
                'type': 'INDEX',
                'column': column,
                'reason': 'Used in JOIN conditions'
            })
            
        return suggestions
        
    def _optimize_joins(self, parsed) -> Optional[Dict]:
        """JOIN sıralamasını optimize eder."""
        joins = self._extract_joins(parsed)
        if not joins:
            return None
            
        # Table statistics'e göre sıralama
        ordered_joins = self._order_joins_by_size(joins)
        
        new_query = self._rebuild_query_with_joins(parsed, ordered_joins)
        
        return {
            'type': 'JOIN_OPTIMIZATION',
            'query': new_query,
            'description': 'Reordered joins based on table sizes'
        }