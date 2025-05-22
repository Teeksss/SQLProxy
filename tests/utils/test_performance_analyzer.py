import pytest
import numpy as np
from datetime import datetime, timedelta
from app.utils.performance_analyzer import (
    PerformanceAnalyzer,
    QueryMetrics,
    ResourceMetrics
)

class TestPerformanceAnalyzer:
    @pytest.fixture(autouse=True)
    def setup(self):
        """Test setup"""
        try:
            import numpy as np
        except ImportError:
            pytest.skip("numpy is required for performance tests")
            
        self.analyzer = PerformanceAnalyzer()

    @pytest.fixture
    def sample_metrics(self):
        """Test metrikleri oluşturur"""
        return [
            QueryMetrics(
                query_id=f"test_{i}",
                execution_time=100 + i,  # ms
                cpu_usage=50 + (i % 20),  # %
                memory_usage=200 + (i % 50),  # MB
                timestamp=datetime.utcnow() - timedelta(minutes=i)
            ) for i in range(100)
        ]

    def test_basic_analysis(self, sample_metrics):
        """Temel analiz fonksiyonlarını test eder"""
        # Act
        results = self.analyzer.analyze(sample_metrics)
        
        # Assert
        assert results is not None
        assert 'avg_execution_time' in results
        assert 'avg_cpu_usage' in results
        assert 'avg_memory_usage' in results

    def test_performance_trends(self, sample_metrics):
        """Performans trendlerini test eder"""
        # Act
        trends = self.analyzer.analyze_trends(sample_metrics)
        
        # Assert
        assert trends is not None
        assert len(trends['execution_time_trend']) > 0
        assert len(trends['cpu_usage_trend']) > 0
        assert len(trends['memory_usage_trend']) > 0

    def test_anomaly_detection(self, sample_metrics):
        """Anomali tespitini test eder"""
        # Arrange
        # Anomali ekle
        anomaly = QueryMetrics(
            query_id="anomaly",
            execution_time=1000,  # Yüksek execution time
            cpu_usage=90,         # Yüksek CPU
            memory_usage=800,     # Yüksek memory
            timestamp=datetime.utcnow()
        )
        metrics_with_anomaly = sample_metrics + [anomaly]
        
        # Act
        anomalies = self.analyzer.detect_anomalies(
            metrics_with_anomaly
        )
        
        # Assert
        assert anomalies is not None
        assert len(anomalies) > 0
        assert any(a.query_id == "anomaly" for a in anomalies)

    def test_resource_analysis(self):
        """Kaynak analizini test eder"""
        # Arrange
        resources = [
            ResourceMetrics(
                cpu_usage=50 + (i % 20),
                memory_usage=200 + (i % 50),
                disk_io=100 + (i % 30),
                network_io=500 + (i % 100),
                timestamp=datetime.utcnow() - timedelta(minutes=i)
            ) for i in range(60)
        ]
        
        # Act
        analysis = self.analyzer.analyze_resources(resources)
        
        # Assert
        assert analysis is not None
        assert 'cpu_trend' in analysis
        assert 'memory_trend' in analysis
        assert 'io_trend' in analysis