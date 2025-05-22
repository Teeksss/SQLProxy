import pytest
import numpy as np
from datetime import datetime, timedelta
from sqlproxy.core.analysis import PerformanceAnalyzer
from sqlproxy.models import PerformanceMetrics

class TestPerformanceAnalysis:
    @pytest.fixture
    def analyzer(self):
        return PerformanceAnalyzer()

    def test_query_optimization(self, analyzer):
        """Query optimizasyonunu test eder"""
        # Test queries
        queries = [
            # Non-optimized
            """
            SELECT *
            FROM users u, orders o
            WHERE u.id = o.user_id
            AND u.created_at > '2025-01-01'
            """,
            
            # Expected optimization
            """
            SELECT u.id, u.name, o.order_date
            FROM users u
            INNER JOIN orders o ON u.id = o.user_id
            WHERE u.created_at > '2025-01-01'
            """
        ]

        for query in queries:
            optimization = analyzer.optimize_query(query)
            
            assert optimization.estimated_cost < 1000
            assert optimization.recommended_indexes
            assert optimization.execution_plan

    def test_resource_utilization(self, analyzer):
        """Kaynak kullanımını analiz eder"""
        # Generate test metrics
        metrics = [
            PerformanceMetrics(
                timestamp=datetime.utcnow() - timedelta(minutes=i),
                cpu_usage=np.random.uniform(20, 80),
                memory_usage=np.random.uniform(100, 500),
                disk_io=np.random.uniform(10, 100),
                network_io=np.random.uniform(50, 200)
            ) for i in range(60)
        ]

        analysis = analyzer.analyze_resources(metrics)
        
        assert analysis.cpu_threshold < 90
        assert analysis.memory_threshold < 800
        assert analysis.io_saturation < 0.8

    def test_scalability_analysis(self, analyzer):
        """Ölçeklenebilirlik analizi yapar"""
        # Test scenarios
        scenarios = [
            {'users': 100, 'qps': 1000},
            {'users': 500, 'qps': 5000},
            {'users': 1000, 'qps': 10000}
        ]

        for scenario in scenarios:
            scalability = analyzer.analyze_scalability(
                users=scenario['users'],
                queries_per_second=scenario['qps']
            )
            
            assert scalability.max_throughput > scenario['qps']
            assert scalability.bottleneck_resources
            assert scalability.scaling_recommendations

    def test_performance_prediction(self, analyzer):
        """Performans tahminlemesi yapar"""
        # Historical data
        history = [
            PerformanceMetrics(
                timestamp=datetime.utcnow() - timedelta(hours=i),
                queries_per_second=np.random.normal(1000, 100),
                avg_response_time=np.random.normal(0.1, 0.02)
            ) for i in range(24)
        ]

        # Make predictions
        predictions = analyzer.predict_performance(
            history=history,
            horizon_hours=6
        )
        
        assert len(predictions) == 6
        assert all(p.queries_per_second > 0 for p in predictions)
        assert all(p.avg_response_time > 0 for p in predictions)