from typing import Dict, List
import asyncio
from concurrent.futures import ThreadPoolExecutor
from .optimizer import QueryOptimizer
from .executor import QueryExecutor
from .merger import ResultMerger

class DistributedQueryEngine:
    def __init__(self):
        self.optimizer = QueryOptimizer()
        self.executor = QueryExecutor()
        self.merger = ResultMerger()
        self.max_parallel_queries = 10
        
    async def execute_query(self, query: str, 
                          context: Dict) -> Dict:
        """Distributed query execution."""
        try:
            # Query analizi ve optimizasyon
            plan = await self._create_execution_plan(query, context)
            
            # Parallel execution
            results = await self._execute_in_parallel(plan)
            
            # Result merging
            final_result = await self._merge_results(results)
            
            return {
                'status': 'success',
                'result': final_result,
                'metrics': self._collect_execution_metrics(results)
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
            
    async def _create_execution_plan(self, query: str,
                                   context: Dict) -> Dict:
        """Execution plan oluşturur."""
        # Query parsing
        parsed = self.optimizer.parse_query(query)
        
        # Cost-based optimization
        optimized = self.optimizer.optimize(parsed)
        
        # Sharding strategy
        shards = self._determine_shards(optimized, context)
        
        # Create execution plan
        return {
            'query': optimized['query'],
            'shards': shards,
            'parallelizable': optimized['can_parallelize'],
            'estimated_cost': optimized['cost']
        }
        
    async def _execute_in_parallel(self, plan: Dict) -> List[Dict]:
        """Parallel query execution."""
        async def execute_shard(shard):
            return await self.executor.execute(
                query=plan['query'],
                shard=shard
            )
            
        # Thread pool ile parallel execution
        with ThreadPoolExecutor(max_workers=self.max_parallel_queries) as executor:
            futures = [
                asyncio.ensure_future(execute_shard(shard))
                for shard in plan['shards']
            ]
            
            return await asyncio.gather(*futures)