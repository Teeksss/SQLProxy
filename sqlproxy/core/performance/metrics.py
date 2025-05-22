"""
Performance metrics collection
"""
import time
from typing import Dict, List, Any

class PerformanceMetrics:
    """
    Collects and analyzes performance metrics
    """
    
    def __init__(self):
        """Initialize metrics collection"""
        self.query_times = []
        self.query_types = {}
        self.total_queries = 0
        self.total_time = 0.0
        self.max_time = 0.0
        self.min_time = float('inf')
        self.start_time = time.time()
    
    def add_query(self, query: str, execution_time: float, query_type: str = "default") -> None:
        """
        Add query metrics
        
        Args:
            query: SQL query string
            execution_time: Execution time in seconds
            query_type: Type of query
        """
        self.query_times.append((query, execution_time, time.time()))
        
        # Update type statistics
        if query_type not in self.query_types:
            self.query_types[query_type] = {
                'count': 0,
                'total_time': 0.0,
                'max_time': 0.0,
                'min_time': float('inf')
            }
        
        self.query_types[query_type]['count'] += 1
        self.query_types[query_type]['total_time'] += execution_time
        self.query_types[query_type]['max_time'] = max(
            self.query_types[query_type]['max_time'], execution_time
        )
        self.query_types[query_type]['min_time'] = min(
            self.query_types[query_type]['min_time'], execution_time
        )
        
        # Update overall statistics
        self.total_queries += 1
        self.total_time += execution_time
        self.max_time = max(self.max_time, execution_time)
        self.min_time = min(self.min_time, execution_time)
    
    def add_metric(
        self, 
        execution_time: float, 
        query_count: int = 1, 
        memory_usage: float = 0.0,
        timestamp: Optional[float] = None
    ) -> None:
        """
        Add general performance metric
        
        Args:
            execution_time: Execution time in seconds
            query_count: Number of queries
            memory_usage: Memory usage in MB
            timestamp: Timestamp (defaults to current time)
        """
        self.total_time += execution_time
        self.total_queries += query_count
    
    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary"""
        avg_time = self.total_time / self.total_queries if self.total_queries > 0 else 0
        
        return {
            'total_queries': self.total_queries,
            'total_time': self.total_time,
            'avg_time': avg_time,
            'max_time': self.max_time,
            'min_time': self.min_time if self.min_time != float('inf') else 0,
            'uptime': time.time() - self.start_time,
            'query_types': self.query_types
        }
    
    def get_slow_queries(self, threshold: float = 1.0) -> List[Dict[str, Any]]:
        """
        Get list of slow queries
        
        Args:
            threshold: Threshold in seconds
            
        Returns:
            List of slow queries
        """
        slow_queries = []
        
        for query, exec_time, timestamp in self.query_times:
            if exec_time > threshold:
                slow_queries.append({
                    'query': query,
                    'execution_time': exec_time,
                    'timestamp': timestamp
                })
        
        return sorted(slow_queries, key=lambda x: x['execution_time'], reverse=True)
    
    def reset(self) -> None:
        """Reset metrics"""
        self.query_times = []
        self.query_types = {}
        self.total_queries = 0
        self.total_time = 0.0
        self.max_time = 0.0
        self.min_time = float('inf')
        self.start_time = time.time()