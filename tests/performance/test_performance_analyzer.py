import pytest
from datetime import datetime, timedelta
from sqlproxy.core.performance.analyzer import PerformanceAnalyzer

@pytest.fixture
def analyzer():
    return PerformanceAnalyzer()

def test_performance_analysis(analyzer):
    # Add test metrics
    for i in range(10):
        analyzer.metrics.add_metric(
            execution_time=100 + i,
            query_count=10,
            memory_usage=200 + i,
            timestamp=datetime.utcnow() - timedelta(minutes=i)
        )

    analysis = analyzer.analyze()
    
    assert 'execution_time' in analysis
    assert 'query_performance' in analysis
    assert 'memory_usage' in analysis