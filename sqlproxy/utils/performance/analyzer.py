import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional

class PerformanceMetrics:
    def __init__(self):
        self.execution_times: List[float] = []
        self.cpu_usage: List[float] = []
        self.memory_usage: List[float] = []
        self.timestamps: List[datetime] = []

    def add_metric(self, 
                  execution_time: float, 
                  cpu_usage: float,
                  memory_usage: float,
                  timestamp: Optional[datetime] = None):
        """Yeni metrik ekler"""
        self.execution_times.append(execution_time)
        self.cpu_usage.append(cpu_usage)
        self.memory_usage.append(memory_usage)
        self.timestamps.append(timestamp or datetime.utcnow())

    def get_dataframe(self) -> pd.DataFrame:
        """Metrikleri DataFrame olarak döndürür"""
        return pd.DataFrame({
            'execution_time': self.execution_times,
            'cpu_usage': self.cpu_usage,
            'memory_usage': self.memory_usage,
            'timestamp': self.timestamps
        })

class PerformanceAnalyzer:
    def __init__(self):
        self.metrics = PerformanceMetrics()

    def analyze_performance(self) -> Dict:
        """Performans analizini yapar"""
        df = self.metrics.get_dataframe()
        
        return {
            'execution_time': {
                'mean': np.mean(df['execution_time']),
                'std': np.std(df['execution_time']),
                'min': np.min(df['execution_time']),
                'max': np.max(df['execution_time'])
            },
            'cpu_usage': {
                'mean': np.mean(df['cpu_usage']),
                'std': np.std(df['cpu_usage']),
                'min': np.min(df['cpu_usage']),
                'max': np.max(df['cpu_usage'])
            },
            'memory_usage': {
                'mean': np.mean(df['memory_usage']),
                'std': np.std(df['memory_usage']),
                'min': np.min(df['memory_usage']),
                'max': np.max(df['memory_usage'])
            }
        }

    def detect_anomalies(self, threshold: float = 2.0) -> Dict:
        """Anomalileri tespit eder"""
        df = self.metrics.get_dataframe()
        
        anomalies = {
            'execution_time': [],
            'cpu_usage': [],
            'memory_usage': []
        }
        
        for col in ['execution_time', 'cpu_usage', 'memory_usage']:
            mean = np.mean(df[col])
            std = np.std(df[col])
            threshold_value = mean + (threshold * std)
            
            anomalies[col] = df[df[col] > threshold_value].index.tolist()
            
        return anomalies