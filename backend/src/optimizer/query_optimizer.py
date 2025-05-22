from typing import Dict, List
import sqlparse
from .models import OptimizationRule, QueryPlan
from .analyzers import QueryAnalyzer

class QueryOptimizer:
    def __init__(self):
        self.analyzer = QueryAnalyzer()
        self.rules = self._load_optimization_rules()
        
    async def optimize_query(self, query: str,
                           context: Dict) -> Dict:
        """Query optimizasyonu yapar."""
        # Parse query
        parsed = sqlparse.parse(query)[0]
        
        # Analyze query
        analysis = await self.analyzer.analyze_query(parsed)
        
        # Apply optimization rules
        optimizations = []
        for rule in self.rules:
            if rule.should_apply(analysis):
                optimization = await rule.apply(parsed, analysis)
                optimizations.append(optimization)
                
        # Generate execution plan
        plan = await self._generate_execution_plan(
            parsed, analysis
        )
        
        # Estimate cost
        cost = await self._estimate_cost(plan)
        
        return {
            'optimized_query': str(parsed),
            'execution_plan': plan,
            'estimated_cost': cost,
            'applied_optimizations': optimizations
        }
        
    async def _generate_execution_plan(self, parsed_query,
                                    analysis: Dict) -> QueryPlan:
        """Execution plan oluşturur."""
        plan = QueryPlan()
        
        # Add scan operations
        for table in analysis['tables']:
            scan = self._plan_table_scan(table, analysis)
            plan.add_operation(scan)
            
        # Add join operations
        for join in analysis['joins']:
            join_op = self._plan_join(join, analysis)
            plan.add_operation(join_op)
            
        # Add filter operations
        for condition in analysis['conditions']:
            filter_op = self._plan_filter(condition)
            plan.add_operation(filter_op)
            
        return plan
        
    async def _estimate_cost(self, plan: QueryPlan) -> Dict:
        """Query maliyetini tahmin eder."""
        costs = {
            'cpu_cost': 0,
            'io_cost': 0,
            'memory_cost': 0
        }
        
        for operation in plan.operations:
            op_cost = await self._calculate_operation_cost(
                operation
            )
            costs['cpu_cost'] += op_cost['cpu']
            costs['io_cost'] += op_cost['io']
            costs['memory_cost'] += op_cost['memory']
            
        return costs