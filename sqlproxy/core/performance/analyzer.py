"""
Performance analysis tools
"""
import time
from typing import Dict, List, Optional, Any

from sqlproxy.core.performance.metrics import PerformanceMetrics

class PerformanceAnalyzer:
    """
    Analyzes query performance and resource usage
    """
    
    def __init__(self):
        """Initialize performance analyzer"""
        self.metrics = PerformanceMetrics()
        self.start_time = time.time()
    
    def record_query(self, query: str, execution_time: float, query_type: str = "default") -> None:
        """
        Record query execution metrics
        
        Args:
            query: SQL query string
            execution_time: Execution time in seconds
            query_type: Type of query
        """
        self.metrics.add_query(query, execution_time, query_type)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        return self.metrics.get_summary()
    
    def reset(self) -> None:
        """Reset performance metrics"""
        self.metrics.reset()
        self.start_time = time.time()
    
    def get_slow_queries(self, threshold: float = 1.0) -> List[Dict[str, Any]]:
        """
        Get list of slow queries
        
        Args:
            threshold: Threshold in seconds
            
        Returns:
            List of slow queries
        """
        return self.metrics.get_slow_queries(threshold)