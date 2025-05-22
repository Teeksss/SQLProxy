from typing import Dict, List
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from tensorflow import keras
from .feature_engineering import WorkloadFeatureExtractor
from .models import LSTMPredictor

class WorkloadPredictor:
    def __init__(self):
        self.feature_extractor = WorkloadFeatureExtractor()
        self.rf_model = RandomForestRegressor(n_estimators=100)
        self.lstm_model = LSTMPredictor()
        self.lookback_period = 30  # days
        
    async def predict_workload(self, horizon: int = 24) -> Dict:
        """Gelecek workload tahminini yapar."""
        # Historical data
        historical = await self._get_historical_data()
        
        # Feature extraction
        features = self.feature_extractor.extract_features(historical)
        
        # Short-term prediction (Random Forest)
        short_term = await self._predict_short_term(
            features, horizon
        )
        
        # Long-term prediction (LSTM)
        long_term = await self._predict_long_term(
            features, horizon
        )
        
        # Combine predictions
        predictions = self._combine_predictions(
            short_term, long_term
        )
        
        return {
            'predictions': predictions,
            'confidence_intervals': self._calculate_confidence(
                predictions
            ),
            'influencing_factors': self._identify_factors(features)
        }
        
    async def _predict_short_term(self, features: pd.DataFrame,
                                horizon: int) -> np.ndarray:
        """Kısa vadeli tahmin yapar."""
        predictions = []
        
        for h in range(horizon):
            # Rolling window prediction
            window_features = self._prepare_window(features, h)
            pred = self.rf_model.predict(window_features)
            predictions.append(pred)
            
            # Update features for next prediction
            features = self._update_features(features, pred)
            
        return np.array(predictions)
        
    async def _predict_long_term(self, features: pd.DataFrame,
                               horizon: int) -> np.ndarray:
        """Uzun vadeli tahmin yapar."""
        # Prepare sequences for LSTM
        sequences = self._prepare_sequences(features)
        
        # LSTM prediction
        predictions = self.lstm_model.predict_sequences(
            sequences, horizon
        )
        
        return predictions
        
    def _combine_predictions(self, short_term: np.ndarray,
                           long_term: np.ndarray) -> np.ndarray:
        """Kısa ve uzun vadeli tahminleri birleştirir."""
        # Weighted combination
        weights = self._calculate_weights()
        combined = (
            weights['short_term'] * short_term +
            weights['long_term'] * long_term
        )
        
        return combined