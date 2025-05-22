from typing import Dict, List, Optional
from datetime import datetime, timedelta
import numpy as np
from collections import defaultdict

class QueryAnalytics:
    def __init__(self):
        self.query_history = []
        self.performance_metrics = defaultdict(list)
        
    def record_query(self, query_info: Dict):
        """Query execution bilgilerini kaydeder."""
        self.query_history.append({
            'timestamp': datetime.utcnow(),
            'query': query_info['query'],
            'execution_time': query_info['duration'],
            'rows_affected': query_info.get('rows_affected', 0),
            'cpu_usage': query_info.get('cpu_usage', 0),
            'memory_usage': query_info.get('memory_usage', 0),
            'cache_hits': query_info.get('cache_hits', 0)
        })
        
    def analyze_performance(self, time_window: timedelta = None) -> Dict:
        """Performance analizi yapar."""
        queries = self._filter_queries(time_window)
        
        return {
            'summary': self._calculate_summary(queries),
            'patterns': self._analyze_patterns(queries),
            'bottlenecks': self._identify_bottlenecks(queries),
            'recommendations': self._generate_recommendations(queries)
        }
        
    def _calculate_summary(self, queries: List[Dict]) -> Dict:
        """İstatistiksel özet hesaplar."""
        execution_times = [q['execution_time'] for q in queries]
        
        return {
            'total_queries': len(queries),
            'avg_execution_time': np.mean(execution_times),
            'p95_execution_time': np.percentile(execution_times, 95),
            'max_execution_time': max(execution_times),
            'total_rows_affected': sum(q['rows_affected'] for q in queries)
        }
        
    def _analyze_patterns(self, queries: List[Dict]) -> Dict:
        """Query pattern analizi yapar."""
        patterns = defaultdict(int)
        
        for query in queries:
            pattern = self._extract_query_pattern(query['query'])
            patterns[pattern] += 1
            
        return {
            'common_patterns': dict(
                sorted(
                    patterns.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:10]
            )
        }
        
    def _identify_bottlenecks(self, queries: List[Dict]) -> List[Dict]:
        """Performance bottleneck'leri belirler."""
        bottlenecks = []
        
        # CPU yoğun queryler
        cpu_intensive = [
            q for q in queries
            if q['cpu_usage'] > np.mean([q['cpu_usage'] for q in queries]) * 2
        ]
        if cpu_intensive:
            bottlenecks.append({
                'type': 'CPU_INTENSIVE',
                'queries': cpu_intensive
            })
            
        # Memory yoğun queryler
        memory_intensive = [
            q for q in queries
            if q['memory_usage'] > np.mean([q['memory_usage'] for q in queries]) * 2
        ]
        if memory_intensive:
            bottlenecks.append({
                'type': 'MEMORY_INTENSIVE',
                'queries': memory_intensive
            })
            
        return bottlenecks