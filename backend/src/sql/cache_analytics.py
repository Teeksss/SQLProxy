from typing import Dict, List
from datetime import datetime, timedelta
import numpy as np
from collections import defaultdict

class CacheStats:
    def __init__(self):
        self.hits = defaultdict(int)
        self.misses = defaultdict(int)
        self.sets = defaultdict(int)
        self.errors = defaultdict(list)
        self.invalidations = []
        
    def record_hit(self, key: str):
        self.hits[key] += 1
        
    def record_miss(self, key: str):
        self.misses[key] += 1
        
    def record_set(self, key: str):
        self.sets[key] += 1
        
    def record_error(self, key: str, error: str):
        self.errors[key].append({
            'timestamp': datetime.utcnow(),
            'error': error
        })
        
    def record_invalidation(self, pattern: str, count: Optional[int]):
        self.invalidations.append({
            'timestamp': datetime.utcnow(),
            'pattern': pattern,
            'count': count
        })
        
    def get_stats(self, time_window: timedelta = None) -> Dict:
        """Cache istatistiklerini hesaplar."""
        end_time = datetime.utcnow()
        start_time = end_time - (time_window or timedelta(hours=24))
        
        return {
            'summary': self._calculate_summary(start_time, end_time),
            'hit_rate': self._calculate_hit_rate(),
            'popular_queries': self._get_popular_queries(),
            'error_analysis': self._analyze_errors(),
            'invalidation_impact': self._analyze_invalidations()
        }
        
    def _calculate_summary(self, start_time: datetime, 
                         end_time: datetime) -> Dict:
        """Özet istatistikler hesaplar."""
        return {
            'total_hits': sum(self.hits.values()),
            'total_misses': sum(self.misses.values()),
            'total_sets': sum(self.sets.values()),
            'total_errors': sum(len(errors) for errors in self.errors.values()),
            'unique_keys': len(set(self.hits.keys()) | set(self.misses.keys())),
            'error_rate': self._calculate_error_rate()
        }
        
    def _calculate_hit_rate(self) -> float:
        """Cache hit rate hesaplar."""
        total_requests = sum(self.hits.values()) + sum(self.misses.values())
        if total_requests == 0:
            return 0.0
        return sum(self.hits.values()) / total_requests
        
    def _get_popular_queries(self) -> List[Dict]:
        """En popüler cache key'leri bulur."""
        popularity = defaultdict(int)
        
        for key, hits in self.hits.items():
            popularity[key] = hits
            
        return [
            {
                'key': key,
                'hits': hits,
                'misses': self.misses[key],
                'hit_rate': hits / (hits + self.misses[key])
            }
            for key, hits in sorted(
                popularity.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
        ]