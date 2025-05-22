import pytest
import time
import asyncio
import numpy as np
from datetime import datetime, timedelta
from sqlproxy.core.performance import PerformanceAnalyzer
from sqlproxy.models import (
    QueryMetrics,
    PerformanceReport,
    ResourceMetrics
)

class TestPerformanceAnalyzer:
    @pytest.fixture
    def analyzer(self):
        return PerformanceAnalyzer()
        
    @pytest.fixture
    def sample_metrics(self):
        """Test için örnek metrikler oluşturur"""
        return [
            QueryMetrics(
                query_id=f"query_{i}",
                execution_time=np.random.normal(100, 20),  # ms
                cpu_usage=np.random.uniform(20, 80),      # %
                memory_usage=np.random.uniform(100, 500),  # MB
                timestamp=datetime.utcnow() - timedelta(minutes=i)
            ) for i in range(100)
        ]
        
    def test_basic_metrics_calculation(self, analyzer, sample_metrics):
        """Temel metrik hesaplamalarını test eder"""
        # Act
        report = analyzer.analyze_metrics(sample_metrics)
        
        # Assert
        assert isinstance(report, PerformanceReport)
        assert report.avg_execution_time > 0
        assert report.avg_cpu_usage > 0
        assert report.avg_memory_usage > 0
        
    @pytest.mark.asyncio
    async def test_real_time_analysis(self, analyzer):
        """Gerçek zamanlı analizi test eder"""
        # Arrange
        async def generate_metrics():
            for _ in range(10):
                yield QueryMetrics(
                    query_id=f"realtime_{_}",
                    execution_time=np.random.normal(100, 20),
                    cpu_usage=np.random.uniform(20, 80),
                    memory_usage=np.random.uniform(100, 500),
                    timestamp=datetime.utcnow()
                )
                await asyncio.sleep(0.1)
                
        # Act
        metrics = []
        async for metric in analyzer.analyze_stream(generate_metrics()):
            metrics.append(metric)
            
        # Assert
        assert len(metrics) == 10
        assert all(isinstance(m, QueryMetrics) for m in metrics)
        
    def test_performance_anomaly_detection(self, analyzer, sample_metrics):
        """Performans anomalilerini tespit eder"""
        # Arrange
        # Anomali ekle
        anomaly_metrics = sample_metrics + [
            QueryMetrics(
                query_id="anomaly_1",
                execution_time=1000,  # Aşırı yüksek execution time
                cpu_usage=95,        # Yüksek CPU kullanımı
                memory_usage=1500,    # Yüksek memory kullanımı
                timestamp=datetime.utcnow()
            )
        ]
        
        # Act
        anomalies = analyzer.detect_anomalies(anomaly_metrics)
        
        # Assert
        assert len(anomalies) > 0
        assert any(a.query_id == "anomaly_1" for a in anomalies)
        
    def test_resource_utilization_analysis(self, analyzer):
        """Kaynak kullanımı analizini test eder"""
        # Arrange
        resources = [
            ResourceMetrics(
                cpu_usage=np.random.uniform(20, 80),
                memory_usage=np.random.uniform(100, 500),
                disk_io=np.random.uniform(10, 100),
                network_io=np.random.uniform(50, 200),
                timestamp=datetime.utcnow() - timedelta(minutes=i)
            ) for i in range(60)  # 1 saatlik veri
        ]
        
        # Act
        analysis = analyzer.analyze_resources(resources)
        
        # Assert
        assert analysis.peak_cpu_usage == max(r.cpu_usage for r in resources)
        assert analysis.peak_memory_usage == max(r.memory_usage for r in resources)
        assert hasattr(analysis, 'resource_trends')
        
    @pytest.mark.parametrize("query_type,expected_range", [
        ("SELECT", (0, 200)),    # ms
        ("INSERT", (0, 300)),    # ms
        ("UPDATE", (0, 300)),    # ms
        ("DELETE", (0, 250)),    # ms
    ])
    def test_query_type_performance(self, analyzer, query_type, expected_range):
        """Query tipine göre performans beklentilerini test eder"""
        # Arrange
        metrics = [
            QueryMetrics(
                query_id=f"{query_type}_{i}",
                query_type=query_type,
                execution_time=np.random.uniform(*expected_range),
                cpu_usage=np.random.uniform(20, 80),
                memory_usage=np.random.uniform(100, 500),
                timestamp=datetime.utcnow()
            ) for i in range(50)
        ]
        
        # Act
        analysis = analyzer.analyze_by_query_type(metrics)
        
        # Assert
        assert query_type in analysis
        assert expected_range[0] <= analysis[query_type].avg_execution_time <= expected_range[1]
        
    def test_performance_regression_detection(self, analyzer):
        """Performans regresyonlarını tespit eder"""
        # Arrange
        # İlk hafta metrikleri
        week1_metrics = [
            QueryMetrics(
                query_id=f"week1_{i}",
                execution_time=np.random.normal(100, 10),
                cpu_usage=np.random.uniform(20, 60),
                memory_usage=np.random.uniform(100, 400),
                timestamp=datetime.utcnow() - timedelta(days=7, minutes=i)
            ) for i in range(100)
        ]
        
        # İkinci hafta metrikleri (performans düşüşü)
        week2_metrics = [
            QueryMetrics(
                query_id=f"week2_{i}",
                execution_time=np.random.normal(150, 10),  # 50% slower
                cpu_usage=np.random.uniform(30, 70),      # Higher CPU
                memory_usage=np.random.uniform(150, 450),  # Higher memory
                timestamp=datetime.utcnow() - timedelta(minutes=i)
            ) for i in range(100)
        ]
        
        # Act
        regressions = analyzer.detect_regressions(
            week1_metrics, week2_metrics
        )
        
        # Assert
        assert len(regressions) > 0
        assert regressions[0].performance_impact > 0.2  # 20% kötüleşme
        
    def test_concurrent_query_impact(self, analyzer, sample_metrics):
        """Eşzamanlı sorguların etkisini analiz eder"""
        # Arrange
        concurrent_times = [
            datetime.utcnow() - timedelta(minutes=5),
            datetime.utcnow() - timedelta(minutes=10),
            datetime.utcnow() - timedelta(minutes=15)
        ]
        
        concurrent_metrics = []
        for t in concurrent_times:
            # Her zaman noktası için 10 eşzamanlı sorgu
            concurrent_metrics.extend([
                QueryMetrics(
                    query_id=f"concurrent_{t}_{i}",
                    execution_time=np.random.normal(120, 30),
                    cpu_usage=np.random.uniform(40, 90),
                    memory_usage=np.random.uniform(200, 600),
                    timestamp=t
                ) for i in range(10)
            ])
            
        # Act
        impact = analyzer.analyze_concurrency_impact(concurrent_metrics)
        
        # Assert
        assert impact.peak_concurrent_queries >= 10
        assert impact.performance_degradation > 0
        
    def test_optimization_recommendations(self, analyzer, sample_metrics):
        """Optimizasyon önerilerini test eder"""
        # Act
        recommendations = analyzer.generate_recommendations(sample_metrics)
        
        # Assert
        assert len(recommendations) > 0
        assert all(hasattr(r, 'priority') for r in recommendations)
        assert all(hasattr(r, 'estimated_impact') for r in recommendations)
        
        # En az bir yüksek öncelikli öneri olmalı
        assert any(r.priority == 'high' for r in recommendations)