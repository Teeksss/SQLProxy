import pytest
import numpy as np
from datetime import datetime, timedelta

# Import path düzeltmesi
try:
    from sqlproxy.utils.performance import PerformanceAnalyzer
except ImportError:
    from backend.app.utils.performance_analyzer import PerformanceAnalyzer

class TestPerformanceAnalyzer:
    @pytest.fixture(autouse=True)
    def setup(self):
        """Test setup ve dependency kontrolü"""
        try:
            import numpy as np
            import pandas as pd
        except ImportError as e:
            pytest.skip(f"Required dependency not found: {str(e)}")

        self.analyzer = PerformanceAnalyzer()

    def test_basic_metrics(self):
        """Temel metrikleri test eder"""
        # Arrange
        execution_time = 100.0
        cpu_usage = 50.0
        memory_usage = 200.0

        # Act
        self.analyzer.add_metric(
            execution_time=execution_time,
            cpu_usage=cpu_usage,
            memory_usage=memory_usage
        )

        # Assert
        metrics = self.analyzer.get_metrics()
        assert len(metrics['execution_times']) == 1
        assert metrics['execution_times'][0] == execution_time
        assert metrics['cpu_usage'][0] == cpu_usage
        assert metrics['memory_usage'][0] == memory_usage

    def test_performance_analysis(self):
        """Performans analizini test eder"""
        # Arrange
        for _ in range(10):
            self.analyzer.add_metric(
                execution_time=np.random.normal(100, 10),
                cpu_usage=np.random.uniform(20, 80),
                memory_usage=np.random.uniform(100, 500)
            )

        # Act
        analysis = self.analyzer.analyze()

        # Assert
        assert 'execution_time' in analysis
        assert 'cpu_usage' in analysis
        assert 'memory_usage' in analysis
        for metric in analysis.values():
            assert all(key in metric for key in ['mean', 'std', 'min', 'max'])

    def test_anomaly_detection(self):
        """Anomali tespitini test eder"""
        # Arrange
        # Normal metrikler
        for _ in range(10):
            self.analyzer.add_metric(
                execution_time=np.random.normal(100, 10),
                cpu_usage=np.random.uniform(20, 80),
                memory_usage=np.random.uniform(100, 500)
            )
        # Anomali metriği
        self.analyzer.add_metric(
            execution_time=1000.0,  # Aşırı yüksek
            cpu_usage=95.0,         # Yüksek
            memory_usage=1000.0     # Yüksek
        )

        # Act
        anomalies = self.analyzer.detect_anomalies()

        # Assert
        assert len(anomalies) > 0
        assert any(a['execution_time'] > 500 for a in anomalies)