import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime

class PerformanceMetrics:
    def __init__(self):
        self.execution_times: List[float] = []
        self.query_counts: List[int] = []
        self.memory_usage: List[float] = []
        self.timestamps: List[datetime] = []

    def add_metric(self, 
                  execution_time: float,
                  query_count: int,
                  memory_usage: float,
                  timestamp: Optional[datetime] = None):
        """Add new performance metric"""
        self.execution_times.append(execution_time)
        self.query_counts.append(query_count)
        self.memory_usage.append(memory_usage)
        self.timestamps.append(timestamp or datetime.utcnow())

    def to_dataframe(self) -> pd.DataFrame:
        """Convert metrics to DataFrame"""
        return pd.DataFrame({
            'execution_time': self.execution_times,
            'query_count': self.query_counts,
            'memory_usage': self.memory_usage,
            'timestamp': self.timestamps
        })

class PerformanceAnalyzer:
    def __init__(self):
        self.metrics = PerformanceMetrics()

    def analyze(self) -> Dict:
        """Analyze performance metrics"""
        df = self.metrics.to_dataframe()
        
        return {
            'execution_time': {
                'mean': float(np.mean(df['execution_time'])),
                'std': float(np.std(df['execution_time'])),
                'min': float(np.min(df['execution_time'])),
                'max': float(np.max(df['execution_time']))
            },
            'query_performance': {
                'queries_per_second': float(np.mean(df['query_count'] / df['execution_time'])),
                'total_queries': int(np.sum(df['query_count']))
            },
            'memory_usage': {
                'mean': float(np.mean(df['memory_usage'])),
                'max': float(np.max(df['memory_usage']))
            }
        }

    def detect_anomalies(self, threshold: float = 2.0) -> List[Dict]:
        """Detect performance anomalies"""
        df = self.metrics.to_dataframe()
        anomalies = []

        mean = np.mean(df['execution_time'])
        std = np.std(df['execution_time'])
        threshold_value = mean + (threshold * std)

        anomaly_indices = df[df['execution_time'] > threshold_value].index

        for idx in anomaly_indices:
            anomalies.append({
                'timestamp': df.loc[idx, 'timestamp'],
                'execution_time': df.loc[idx, 'execution_time'],
                'expected_max': threshold_value
            })

        return anomalies