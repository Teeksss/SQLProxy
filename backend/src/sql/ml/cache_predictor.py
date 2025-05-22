from typing import Dict, List
import tensorflow as tf
import numpy as np
from datetime import datetime, timedelta
from collections import deque

class CachePredictor:
    def __init__(self, model_path: str = None):
        self.model = self._load_or_create_model(model_path)
        self.history = deque(maxlen=1000)
        self.min_samples = 100
        
    def predict_cache_hit(self, query: str, 
                         context: Dict) -> Tuple[bool, float]:
        """Cache hit olasılığını tahmin eder."""
        features = self._extract_cache_features(query, context)
        
        # Model prediction
        prediction = self.model.predict(
            np.array([features])
        )[0]
        
        return bool(prediction[0] > 0.5), float(prediction[0])
        
    def train(self, new_samples: List[Dict]):
        """Model'i yeni örneklerle eğitir."""
        # Add to history
        self.history.extend(new_samples)
        
        if len(self.history) < self.min_samples:
            return
            
        # Prepare training data
        X, y = self._prepare_training_data(list(self.history))
        
        # Train model
        self.model.fit(
            X, y,
            epochs=5,
            batch_size=32,
            verbose=0
        )
        
    def _extract_cache_features(self, query: str, 
                              context: Dict) -> np.ndarray:
        """Cache prediction features çıkarır."""
        return np.array([
            len(query),
            context.get('time_of_day', 0) / 24.0,
            context.get('day_of_week', 0) / 7.0,
            context.get('is_repeated', False),
            context.get('last_access_time', 0),
            context.get('access_count', 0),
            context.get('cache_hit_rate', 0.0)
        ])
        
    def _load_or_create_model(self, model_path: str) -> tf.keras.Model:
        """ML modelini yükler veya oluşturur."""
        try:
            if model_path:
                return tf.keras.models.load_model(model_path)
        except:
            pass
            
        return self._create_model()
        
    def _create_model(self) -> tf.keras.Model:
        """Yeni cache prediction modeli oluşturur."""
        model = tf.keras.Sequential([
            tf.keras.layers.Dense(64, activation='relu', 
                                input_shape=(7,)),
            tf.keras.layers.Dropout(0.2),
            tf.keras.layers.Dense(32, activation='relu'),
            tf.keras.layers.Dense(1, activation='sigmoid')
        ])
        
        model.compile(
            optimizer='adam',
            loss='binary_crossentropy',
            metrics=['accuracy']
        )
        
        return model