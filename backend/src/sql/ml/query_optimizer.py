from typing import Dict, List, Tuple
import tensorflow as tf
import numpy as np
from sklearn.preprocessing import StandardScaler
from .models import QueryCostModel, QueryPlanModel
from ..parser import SQLParser

class MLQueryOptimizer:
    def __init__(self):
        self.parser = SQLParser()
        self.cost_model = QueryCostModel()
        self.plan_model = QueryPlanModel()
        self.scaler = StandardScaler()
        
    def optimize(self, query: str) -> Dict:
        """ML tabanlı query optimization yapar."""
        # Parse query
        parsed = self.parser.parse_query(query)
        
        # Extract features
        features = self._extract_features(parsed)
        
        # Predict cost
        predicted_cost = self._predict_cost(features)
        
        # Generate optimized plan
        optimized_plan = self._generate_optimal_plan(
            features, predicted_cost
        )
        
        # Apply optimizations
        optimized_query = self._apply_optimizations(
            query, optimized_plan
        )
        
        return {
            'original_query': query,
            'optimized_query': optimized_query,
            'predicted_cost': predicted_cost,
            'optimization_plan': optimized_plan
        }
        
    def _extract_features(self, parsed_query: Dict) -> np.ndarray:
        """Query'den ML features çıkarır."""
        features = {
            'num_joins': len(parsed_query.get('joins', [])),
            'num_conditions': len(parsed_query.get('conditions', [])),
            'num_tables': len(parsed_query.get('tables', [])),
            'has_subqueries': bool(parsed_query.get('subqueries')),
            'has_aggregations': bool(parsed_query.get('aggregations')),
            'estimated_rows': self._estimate_result_size(parsed_query)
        }
        
        return self.scaler.transform([list(features.values())])
        
    def _predict_cost(self, features: np.ndarray) -> Dict:
        """Query cost prediction yapar."""
        cost_prediction = self.cost_model.predict(features)
        
        return {
            'cpu_cost': float(cost_prediction[0]),
            'io_cost': float(cost_prediction[1]),
            'memory_cost': float(cost_prediction[2]),
            'network_cost': float(cost_prediction[3])
        }
        
    def _generate_optimal_plan(self, 
                             features: np.ndarray,
                             predicted_cost: Dict) -> Dict:
        """Optimal execution plan oluşturur."""
        plan_prediction = self.plan_model.predict(
            np.concatenate([
                features,
                np.array([list(predicted_cost.values())])
            ], axis=1)
        )
        
        return self._decode_plan_prediction(plan_prediction)