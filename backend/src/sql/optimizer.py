from typing import List, Dict, Optional
from .parser import SQLParser

class SQLOptimizer:
    def __init__(self):
        self.parser = SQLParser()
        
    def optimize(self, query: str) -> Dict:
        """Query'yi optimize eder."""
        parsed_info = self.parser.parse_query(query)
        optimized_query = query
        
        optimizations = []
        
        # JOIN optimizasyonu
        if join_optimization := self._optimize_joins(parsed_info):
            optimized_query = join_optimization['query']
            optimizations.append(join_optimization['description'])
            
        # WHERE optimizasyonu
        if where_optimization := self._optimize_where(parsed_info):
            optimized_query = where_optimization['query']
            optimizations.append(where_optimization['description'])
            
        # INDEX önerileri
        index_suggestions = self._suggest_indexes(parsed_info)
        
        return {
            'original_query': query,
            'optimized_query': optimized_query,
            'optimizations': optimizations,
            'index_suggestions': index_suggestions,
            'estimated_improvement': self._estimate_improvement(
                query, optimized_query
            )
        }
        
    def _optimize_joins(self, parsed_info: Dict) -> Optional[Dict]:
        """JOIN sıralamasını optimize eder."""
        if len(parsed_info['joins']) <= 1:
            return None
            
        # Table statistics'e göre join sıralaması
        tables = parsed_info['tables']
        table_stats = self._get_table_statistics(tables)
        
        # En küçük tablodan başla
        ordered_tables = sorted(
            table_stats.items(),
            key=lambda x: x[1]['row_count']
        )
        
        # Join sıralamasını yeniden düzenle
        new_query = self._reorder_joins(
            parsed_info,
            [t[0] for t in ordered_tables]
        )
        
        return {
            'query': new_query,
            'description': 'Optimized JOIN order based on table sizes'
        }
        
    def _optimize_where(self, parsed_info: Dict) -> Optional[Dict]:
        """WHERE koşullarını optimize eder."""
        conditions = parsed_info['conditions']
        if not conditions:
            return None
            
        # İndexli kolonları öne al
        indexed_conditions = []
        non_indexed_conditions = []
        
        for condition in conditions:
            if self._is_indexed(condition['column']):
                indexed_conditions.append(condition)
            else:
                non_indexed_conditions.append(condition)
                
        if len(indexed_conditions) == len(conditions):
            return None
            
        # WHERE clause'u yeniden düzenle
        new_query = self._reorder_where(
            parsed_info,
            indexed_conditions + non_indexed_conditions
        )
        
        return {
            'query': new_query,
            'description': 'Optimized WHERE clause using indexes'
        }