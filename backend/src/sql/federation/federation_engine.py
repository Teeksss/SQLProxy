from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor
import asyncio
from .router import QueryRouter
from .merger import ResultMerger
from ..parser import SQLParser

class FederationEngine:
    def __init__(self):
        self.parser = SQLParser()
        self.router = QueryRouter()
        self.merger = ResultMerger()
        self.max_workers = 10
        
    async def execute_federated_query(self, query: str) -> Dict:
        """Federe edilmiş query'yi execute eder."""
        # Query'yi parse et
        parsed = self.parser.parse_query(query)
        
        # Query'yi alt querylere böl
        sub_queries = self._split_query(parsed)
        
        # Route sub-queries
        routed_queries = self.router.route_queries(sub_queries)
        
        # Parallel execution
        results = await self._execute_parallel(routed_queries)
        
        # Merge results
        final_result = self.merger.merge_results(results)
        
        return {
            'result': final_result,
            'execution_info': self._get_execution_info(results)
        }
        
    def _split_query(self, parsed_query: Dict) -> List[Dict]:
        """Query'yi sub-querylere böler."""
        sub_queries = []
        
        # JOIN analizi
        if joins := parsed_query.get('joins'):
            for join in joins:
                sub_queries.extend(
                    self._create_join_sub_queries(join)
                )
        
        # UNION analizi
        if unions := parsed_query.get('unions'):
            for union in unions:
                sub_queries.extend(
                    self._create_union_sub_queries(union)
                )
                
        # Subquery analizi
        if subqueries := parsed_query.get('subqueries'):
            for subquery in subqueries:
                sub_queries.extend(
                    self._create_subquery_parts(subquery)
                )
                
        return sub_queries
        
    async def _execute_parallel(self, routed_queries: List[Dict]) -> List[Dict]:
        """Sub-queryleri parallel execute eder."""
        async def execute_query(query_info: Dict) -> Dict:
            source = query_info['source']
            query = query_info['query']
            
            try:
                result = await source.execute_async(query)
                return {
                    'source': source.name,
                    'result': result,
                    'status': 'success'
                }
            except Exception as e:
                return {
                    'source': source.name,
                    'error': str(e),
                    'status': 'error'
                }
                
        # ThreadPoolExecutor ile parallel execution
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [
                asyncio.ensure_future(execute_query(query))
                for query in routed_queries
            ]
            
            return await asyncio.gather(*futures)