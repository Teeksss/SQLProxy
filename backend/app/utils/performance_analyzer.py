import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional

class PerformanceAnalyzer:
    """Performans analizi yapar"""
    
    def __init__(self):
        self.execution_times: List[float] = []
        self.cpu_usage: List[float] = []
        self.memory_usage: List[float] = []
        self.timestamps: List[datetime] = []

    def add_metric(self,
                  execution_time: float,
                  cpu_usage: float,
                  memory_usage: float,
                  timestamp: Optional[datetime] = None) -> None:
        """Yeni metrik ekler"""
        self.execution_times.append(execution_time)
        self.cpu_usage.append(cpu_usage)
        self.memory_usage.append(memory_usage)
        self.timestamps.append(timestamp or datetime.utcnow())

    def get_metrics(self) -> Dict[str, List]:
        """Tüm metrikleri döndürür"""
        return {
            'execution_times': self.execution_times,
            'cpu_usage': self.cpu_usage,
            'memory_usage': self.memory_usage,
            'timestamps': self.timestamps
        }

    def analyze(self) -> Dict:
        """Performans analizini yapar"""
        metrics = {
            'execution_time': np.array(self.execution_times),
            'cpu_usage': np.array(self.cpu_usage),
            'memory_usage': np.array(self.memory_usage)
        }

        analysis = {}
        for name, values in metrics.items():
            if len(values) > 0:
                analysis[name] = {
                    'mean': float(np.mean(values)),
                    'std': float(np.std(values)),
                    'min': float(np.min(values)),
                    'max': float(np.max(values))
                }
            else:
                analysis[name] = {
                    'mean': 0.0,
                    'std': 0.0,
                    'min': 0.0,
                    'max': 0.0
                }

        return analysis

    def detect_anomalies(self, threshold: float = 2.0) -> List[Dict]:
        """Anomalileri tespit eder"""
        metrics = self.get_metrics()
        anomalies = []

        for i in range(len(self.execution_times)):
            is_anomaly = False
            anomaly = {
                'execution_time': self.execution_times[i],
                'cpu_usage': self.cpu_usage[i],
                'memory_usage': self.memory_usage[i],
                'timestamp': self.timestamps[i]
            }

            # Execution time anomalisi
            if len(self.execution_times) > 1:
                mean = np.mean(self.execution_times)
                std = np.std(self.execution_times)
                if (self.execution_times[i] - mean) > (threshold * std):
                    is_anomaly = True

            # CPU usage anomalisi
            if self.cpu_usage[i] > 90:  # %90 üzeri CPU kullanımı
                is_anomaly = True

            # Memory usage anomalisi
            if len(self.memory_usage) > 1:
                mean = np.mean(self.memory_usage)
                if self.memory_usage[i] > (2 * mean):  # 2x ortalama memory
                    is_anomaly = True

            if is_anomaly:
                anomalies.append(anomaly)

        return anomalies