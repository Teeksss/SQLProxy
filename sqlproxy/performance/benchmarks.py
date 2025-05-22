import time
from typing import Dict, List, Optional
from datetime import datetime

class BenchmarkRunner:
    def __init__(self):
        self.results: List[Dict] = []
        
    def run_benchmark(self, func, iterations: int = 1000) -> Dict:
        """Run benchmark test"""
        start_time = time.time()
        for _ in range(iterations):
            func()
        end_time = time.time()
        
        result = {
            'iterations': iterations,
            'total_time': end_time - start_time,
            'avg_time': (end_time - start_time) / iterations,
            'timestamp': datetime.utcnow()
        }
        self.results.append(result)
        return result