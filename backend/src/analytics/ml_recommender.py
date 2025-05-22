from typing import Dict, List
import tensorflow as tf
import numpy as np
from .feature_engineering import FeatureEngineer
from .models import OptimizationModel

class MLRecommender:
    def __init__(self):
        self.feature_engineer = FeatureEngineer()
        self.model = OptimizationModel()
        
    async def generate_recommendations(self, 
                                    query_data: List[Dict]) -> List[Dict]:
        """ML tabanlı optimizasyon önerileri üretir."""
        # Feature engineering
        features = await self.feature_engineer.process(query_data)
        
        # Generate predictions
        predictions = self.model.predict(features)
        
        # Convert predictions to recommendations
        recommendations = []
        
        for i, pred in enumerate(predictions):
            if pred['optimization_score'] > 0.7:  # High potential
                recommendations.append({
                    'query_id': query_data[i]['id'],
                    'optimization_type': pred['optimization_type'],
                    'estimated_improvement': pred['improvement_estimate'],
                    'confidence': pred['confidence'],
                    'steps': self._generate_optimization_steps(
                        query_data[i], pred
                    )
                })
                
        return recommendations
        
    def _generate_optimization_steps(self, query: Dict,
                                   prediction: Dict) -> List[str]:
        """Optimizasyon adımlarını oluşturur."""
        steps = []
        
        if prediction['optimization_type'] == 'indexing':
            steps.extend(self._generate_index_recommendations(query))
        elif prediction['optimization_type'] == 'rewrite':
            steps.extend(self._generate_rewrite_suggestions(query))
        elif prediction['optimization_type'] == 'structure':
            steps.extend(self._generate_structure_improvements(query))
            
        return steps