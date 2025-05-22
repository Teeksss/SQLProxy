from typing import Dict, List
import numpy as np
from sklearn.ensemble import IsolationForest
import tensorflow as tf

class AnomalyDetector:
    def __init__(self):
        self.isolation_forest = IsolationForest(
            contamination=0.1,
            random_state=42
        )
        self.lstm_model = self._build_lstm_model()
        
    def detect_realtime(self, metrics: Dict) -> Dict:
        # Convert metrics to feature vector
        features = self._prepare_features(metrics)
        
        # Statistical anomaly detection
        is_statistical_anomaly = self.isolation_forest.predict(
            features.reshape(1, -1)
        )[0] == -1
        
        # Deep learning anomaly detection
        is_dl_anomaly = self._detect_sequence_anomaly(
            metrics['historical_data']
        )
        
        return {
            'is_anomaly': is_statistical_anomaly or is_dl_anomaly,
            'confidence': self._calculate_confidence(
                is_statistical_anomaly,
                is_dl_anomaly
            ),
            'details': {
                'statistical_anomaly': is_statistical_anomaly,
                'sequence_anomaly': is_dl_anomaly,
                'metrics': self._analyze_metrics(metrics)
            }
        }
        
    def _build_lstm_model(self) -> tf.keras.Model:
        model = tf.keras.Sequential([
            tf.keras.layers.LSTM(64, input_shape=(None, 5)),
            tf.keras.layers.Dense(32, activation='relu'),
            tf.keras.layers.Dense(1, activation='sigmoid')
        ])
        model.compile(
            optimizer='adam',
            loss='binary_crossentropy',
            metrics=['accuracy']
        )
        return model
        
    def _prepare_features(self, metrics: Dict) -> np.ndarray:
        return np.array([
            metrics['query_time'],
            metrics['cpu_usage'],
            metrics['memory_usage'],
            metrics['io_operations'],
            metrics['network_usage']
        ])