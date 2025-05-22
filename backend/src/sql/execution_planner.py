from typing import Dict, List, Optional
import json

class ExecutionPlanner:
    def __init__(self):
        self.parser = SQLParser()
        self.optimizer = SQLOptimizer()
        
    def create_execution_plan(self, query: str) -> Dict:
        """Query için execution plan oluşturur."""
        parsed_info = self.parser.parse_query(query)
        optimized = self.optimizer.optimize(query)
        
        plan = {
            'steps': self._generate_steps(parsed_info),
            'estimated_cost': self._estimate_cost(parsed_info),
            'optimization_suggestions': optimized['optimizations'],
            'index_usage': self._analyze_index_usage(parsed_info),
            'resource_requirements': self._estimate_resources(parsed_info)
        }
        
        return plan
        
    def _generate_steps(self, parsed_info: Dict) -> List[Dict]:
        """Execution steps oluşturur."""
        steps = []
        query_type = parsed_info['type']
        
        if query_type == 'SELECT':
            if parsed_info['joins']:
                steps.extend(self._plan_joins(parsed_info))
            else:
                steps.append(self._plan_table_scan(parsed_info))
                
            if parsed_info['conditions']:
                steps.append({
                    'type': 'FILTER',
                    'conditions': parsed_info['conditions']
                })
                
            if parsed_info['group_by']:
                steps.append({
                    'type': 'GROUP',
                    'columns': parsed_info['group_by']
                })
                
        return steps
        
    def _plan_joins(self, parsed_info: Dict) -> List[Dict]:
        """JOIN operasyonları için plan oluşturur."""
        steps = []
        joins = parsed_info['joins']
        
        # İlk tablo için scan
        steps.append({
            'type': 'TABLE_SCAN',
            'table': parsed_info['tables'][0]
        })
        
        # Her join için adım
        for join in joins:
            steps.append({
                'type': 'JOIN',
                'method': self._determine_join_method(join),
                'table': join['table'],
                'conditions': join['conditions']
            })
            
        return steps
        
    def _determine_join_method(self, join: Dict) -> str:
        """En uygun join metodunu belirler."""
        if self._has_index(join['conditions']):
            return 'INDEX_NESTED_LOOP'
        elif self._is_small_table(join['table']):
            return 'NESTED_LOOP'
        else:
            return 'HASH_JOIN'