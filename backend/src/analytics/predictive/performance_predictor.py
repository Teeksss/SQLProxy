from typing import Dict, List
import tensorflow as tf
import numpy as np
from .query_analyzer import QueryAnalyzer
from .models import PerformanceModel

class PerformancePredictor:
    def __init__(self):
        self.query_analyzer = QueryAnalyzer()
        self.model = PerformanceModel()
        
    async def predict_performance(self, query: str,
                                context: Dict) -> Dict:
        """Query performance tahminini yapar."""
        # Query analysis
        analysis = await self.query_analyzer.analyze(query)
        
        # Feature extraction
        features = self._extract_features(analysis, context)
        
        # Performance prediction
        predictions = await self._predict(features)
        
        # Bottleneck analysis
        bottlenecks = self._identify_bottlenecks(
            predictions, analysis
        )
        
        return {
            'execution_time': predictions['execution_time'],
            'resource_usage': predictions['resource_usage'],
            'bottlenecks': bottlenecks,
            'optimization_suggestions': self._generate_suggestions(
                bottlenecks
            )
        }
        
    async def _predict(self, features: np.ndarray) -> Dict:
        """Performance tahminlerini yapar."""
        return {
            'execution_time': self.model.predict_execution_time(
                features
            ),
            'resource_usage': self.model.predict_resource_usage(
                features
            ),
            'confidence': self.model.get_prediction_confidence(
                features
            )
        }
        
    def _identify_bottlenecks(self, predictions: Dict,
                             analysis: Dict) -> List[Dict]:
        """Performance bottleneck'lerini belirler."""
        bottlenecks = []
        
        # CPU bottleneck check
        if predictions['resource_usage']['cpu'] > 80:
            bottlenecks.append({
                'type': 'cpu',
                'severity': 'high',
                'impact': 'Query execution time may increase'
            })
            
        # Memory bottleneck check
        if predictions['resource_usage']['memory'] > 80:
            bottlenecks.append({
                'type': 'memory',
                'severity': 'high',
                'impact': 'Possible OOM errors'
            })
            
        return bottlenecks