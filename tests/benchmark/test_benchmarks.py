import pytest
from sqlproxy.performance.benchmarks import BenchmarkRunner

def test_benchmark_runner():
    runner = BenchmarkRunner()
    
    def sample_func():
        return sum(range(1000))
    
    result = runner.run_benchmark(sample_func, iterations=100)
    
    assert result['iterations'] == 100
    assert result['total_time'] > 0
    assert result['avg_time'] > 0