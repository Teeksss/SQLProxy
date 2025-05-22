import time
from typing import Any, Dict, List, Optional
from datetime import datetime

class QueryPerformance:
    def __init__(self):
        self.query_stats: List[Dict] = []

    def measure_query(self, query: str, 
                     params: Optional[Dict] = None) -> Dict:
        """Measure query performance"""
        start_time = time.time()
        success = True
        error = None
        
        try:
            # Query execution would go here
            time.sleep(0.1)  # Simulate query execution
        except Exception as e:
            success = False
            error = str(e)

        end_time = time.time()
        execution_time = end_time - start_time

        stats = {
            'query': query,
            'params': params,
            'execution_time': execution_time,
            'success': success,
            'error': error,
            'timestamp': datetime.utcnow()
        }

        self.query_stats.append(stats)
        return stats

    def get_performance_stats(self) -> Dict:
        """Get query performance statistics"""
        if not self.query_stats:
            return {}

        total_queries = len(self.query_stats)
        successful_queries = sum(1 for stat in self.query_stats 
                               if stat['success'])
        
        execution_times = [stat['execution_time'] 
                          for stat in self.query_stats]

        return {
            'total_queries': total_queries,
            'successful_queries': successful_queries,
            'failed_queries': total_queries - successful_queries,
            'avg_execution_time': sum(execution_times) / total_queries,
            'min_execution_time': min(execution_times),
            'max_execution_time': max(execution_times)
        }