import pytest
import numpy as np
from datetime import datetime, timedelta
from sqlproxy.utils.performance.analyzer import (
    PerformanceAnalyzer,
    PerformanceMetrics
)

class TestPerformanceAnalyzer:
    @pytest.fixture
    def analyzer(self):
        """Test için analyzer instance'ı oluşturur"""
        return PerformanceAnalyzer()
        
    @pytest.fixture
    def sample_metrics(self, analyzer):
        """Test metrikleri ekler"""
        for i in range(100):
            analyzer.metrics.add_metric(
                execution_time=np.random.normal(100, 10),
                cpu_usage=np.random.uniform(20, 80),
                memory_usage=np.random.uniform(100, 500),
                timestamp=datetime.utcnow() - timedelta(minutes=i)
            )
        return analyzer.metrics
        
    def test_metrics_collection(self, analyzer, sample_metrics):
        """Metrik toplama işlemini test eder"""
        df = sample_metrics.get_dataframe()
        
        assert len(df) == 100
        assert all(col in df.columns 
                  for col in ['execution_time', 'cpu_usage', 
                             'memory_usage', 'timestamp'])
                             
    def test_performance_analysis(self, analyzer, sample_metrics):
        """Performans analizini test eder"""
        analysis = analyzer.analyze_performance()
        
        assert 'execution_time' in analysis
        assert 'cpu_usage' in analysis
        assert 'memory_usage' in analysis
        
        for metric in analysis.values():
            assert all(stat in metric 
                      for stat in ['mean', 'std', 'min', 'max'])
            
    def test_anomaly_detection(self, analyzer, sample_metrics):
        """Anomali tespitini test eder"""
        # Anomali ekle
        analyzer.metrics.add_metric(
            execution_time=1000,  # Aşırı yüksek
            cpu_usage=90,        # Yüksek
            memory_usage=800,    # Yüksek
            timestamp=datetime.utcnow()
        )
        
        anomalies = analyzer.detect_anomalies()
        
        assert len(anomalies['execution_time']) > 0
        assert len(anomalies['cpu_usage']) > 0
        assert len(anomalies['memory_usage']) > 0