from typing import Dict, List
import asyncio
from datetime import datetime
import numpy as np
from .stream_processor import StreamProcessor
from .ml_predictor import MLPredictor

class RealtimeAnalyticsEngine:
    def __init__(self):
        self.stream_processor = StreamProcessor()
        self.ml_predictor = MLPredictor()
        self.window_size = 60  # seconds
        
    async def process_metrics(self, metrics: Dict):
        """Real-time metric processing."""
        try:
            # Stream processing
            processed = await self.stream_processor.process(metrics)
            
            # Anomaly detection
            anomalies = await self._detect_anomalies(processed)
            
            # Trend analysis
            trends = await self._analyze_trends(processed)
            
            # Prediction
            predictions = await self._make_predictions(processed)
            
            return {
                'timestamp': datetime.utcnow().isoformat(),
                'metrics': processed,
                'anomalies': anomalies,
                'trends': trends,
                'predictions': predictions
            }
            
        except Exception as e:
            self.logger.error(f"Analytics error: {str(e)}")
            return None
            
    async def _detect_anomalies(self, data: Dict) -> List[Dict]:
        """Anomaly detection."""
        anomalies = []
        
        for metric, values in data.items():
            # Statistical analysis
            mean = np.mean(values)
            std = np.std(values)
            
            # Z-score calculation
            z_scores = np.abs((values - mean) / std)
            
            # Anomaly detection
            threshold = 3
            anomaly_indices = np.where(z_scores > threshold)[0]
            
            if len(anomaly_indices) > 0:
                anomalies.append({
                    'metric': metric,
                    'indices': anomaly_indices.tolist(),
                    'values': values[anomaly_indices].tolist(),
                    'severity': 'high' if np.max(z_scores) > 5 else 'medium'
                })
                
        return anomalies