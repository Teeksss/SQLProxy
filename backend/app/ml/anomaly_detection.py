"""
Machine Learning based Anomaly Detection module for SQL Proxy

Provides advanced anomaly detection for SQL queries and user behaviors
using various machine learning techniques.

Last updated: 2025-05-20 10:16:22
Updated by: Teeksss
"""

import logging
import numpy as np
import pandas as pd
import pickle
import os
import json
import time
from typing import List, Dict, Any, Optional, Tuple, Union
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sklearn.ensemble import IsolationForest
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

from app.models.query import AuditLog
from app.models.anomaly import AnomalyAlert, AnomalyModel
from app.services.query_similarity import query_similarity_service
from app.core.config import settings

logger = logging.getLogger(__name__)

class AnomalyDetection:
    """
    Machine Learning based anomaly detection for SQL queries and user behaviors

    This service provides multiple anomaly detection techniques to identify
    unusual queries, access patterns, and potential security threats.
    """
    
    def __init__(self):
        """Initialize the anomaly detection module"""
        # Models cache
        self.models = {}
        self.model_last_loaded = {}
        
        # Model update interval (7 days)
        self.model_update_interval = settings.ML_MODEL_UPDATE_INTERVAL_DAYS * 86400
        
        # Feature extraction helpers
        self.feature_extractors = {
            'query_volume': self._extract_query_volume_features,
            'execution_time': self._extract_execution_time_features,
            'temporal_pattern': self._extract_temporal_pattern_features,
            'user_behavior': self._extract_user_behavior_features,
            'query_content': self._extract_query_content_features,
            'access_pattern': self._extract_access_pattern_features
        }
        
        # Anomaly thresholds
        self.anomaly_thresholds = {
            'query_volume': {
                'critical': 0.95,
                'high': 0.9,
                'medium': 0.8,
                'low': 0.7
            },
            'execution_time': {
                'critical': 0.95,
                'high': 0.9,
                'medium': 0.8,
                'low': 0.7
            },
            'temporal_pattern': {
                'critical': 0.95,
                'high': 0.9,
                'medium': 0.8,
                'low': 0.7
            },
            'user_behavior': {
                'critical': 0.95,
                'high': 0.9,
                'medium': 0.8,
                'low': 0.7
            },
            'query_content': {
                'critical': 0.95,
                'high': 0.9,
                'medium': 0.8,
                'low': 0.7
            },
            'access_pattern': {
                'critical': 0.95,
                'high': 0.9,
                'medium': 0.8,
                'low': 0.7
            }
        }
        
        # Directory for storing model files
        self.model_dir = os.path.join(settings.DATA_DIR, 'ml_models')
        os.makedirs(self.model_dir, exist_ok=True)
        
        logger.info("Machine Learning Anomaly Detection module initialized")
    
    def detect_anomalies(
        self, 
        query_id: int, 
        query_text: str, 
        username: str,
        user_role: str,
        server_alias: str,
        execution_time_ms: Optional[float] = None,
        db: Session = None
    ) -> List[Dict[str, Any]]:
        """
        Detect anomalies for a specific query execution
        
        Args:
            query_id: ID of the query in the audit log
            query_text: SQL query text
            username: Username who executed the query
            user_role: Role of the user
            server_alias: Target server alias
            execution_time_ms: Query execution time in milliseconds
            db: Database session
            
        Returns:
            List of detected anomalies
        """
        if not db:
            logger.error("Database session required for anomaly detection")
            return []
        
        try:
            # Load models if needed
            self._ensure_models_loaded(db)
            
            # Initialize anomalies list
            anomalies = []
            
            # Get query features
            features = self._extract_features(
                query_id,
                query_text,
                username,
                user_role,
                server_alias,
                execution_time_ms,
                db
            )
            
            # Detect anomalies using different models
            for model_type, model_data in self.models.items():
                if not model_data.get('model'):
                    continue
                
                # Skip if features for this model type are not available
                if model_type not in features:
                    continue
                
                # Get the model and related data
                model = model_data['model']
                scaler = model_data.get('scaler')
                pca = model_data.get('pca')
                
                # Prepare features for this model
                X = features[model_type]
                
                # Apply preprocessing if available
                if scaler and isinstance(X, np.ndarray):
                    if len(X.shape) == 1:
                        X = X.reshape(1, -1)
                    X = scaler.transform(X)
                
                if pca and isinstance(X, np.ndarray):
                    X = pca.transform(X)
                
                # Detect anomaly
                anomaly_info = self._detect_anomaly_with_model(
                    model_type,
                    model,
                    X,
                    query_id,
                    query_text,
                    username,
                    user_role,
                    server_alias,
                    execution_time_ms
                )
                
                if anomaly_info:
                    anomalies.append(anomaly_info)
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Error in anomaly detection: {str(e)}")
            return []
    
    def train_models(self, db: Session, force_retrain: bool = False) -> Dict[str, Any]:
        """
        Train or update all anomaly detection models
        
        Args:
            db: Database session
            force_retrain: Whether to force retraining even if not needed
            
        Returns:
            Status of model training
        """
        try:
            # Check if training is needed
            models_info = db.query(AnomalyModel).all()
            models_to_train = []
            
            for model_type in self.feature_extractors.keys():
                # Check if model exists
                model_info = next((m for m in models_info if m.model_type == model_type), None)
                
                if force_retrain or not model_info or (
                    datetime.utcnow() - model_info.updated_at > 
                    timedelta(days=settings.ML_MODEL_UPDATE_INTERVAL_DAYS)
                ):
                    models_to_train.append(model_type)
            
            if not models_to_train:
                logger.info("All anomaly detection models are up to date")
                return {"status": "up_to_date", "models": []}
            
            # Train each required model
            trained_models = []
            for model_type in models_to_train:
                logger.info(f"Training anomaly detection model: {model_type}")
                result = self._train_model(model_type, db)
                
                if result["success"]:
                    trained_models.append(model_type)
                    logger.info(f"Successfully trained {model_type} model")
                else:
                    logger.error(f"Failed to train {model_type} model: {result['error']}")
            
            return {
                "status": "trained" if trained_models else "failed", 
                "models": trained_models
            }
            
        except Exception as e:
            logger.error(f"Error training anomaly detection models: {str(e)}")
            return {"status": "failed", "error": str(e), "models": []}
    
    def _train_model(self, model_type: str, db: Session) -> Dict[str, Any]:
        """
        Train a specific anomaly detection model
        
        Args:
            model_type: Type of model to train
            db: Database session
            
        Returns:
            Training result with status
        """
        try:
            # Get training data
            data = self._get_training_data(model_type, db)
            
            if not data or len(data) < settings.ML_MIN_TRAINING_SAMPLES:
                return {
                    "success": False, 
                    "error": f"Insufficient training data: {len(data) if data else 0} samples"
                }
            
            # Preprocess data
            X, scaler, pca = self._preprocess_data(data, model_type)
            
            if X.shape[0] < settings.ML_MIN_TRAINING_SAMPLES:
                return {
                    "success": False, 
                    "error": f"Insufficient preprocessed data: {X.shape[0]} samples"
                }
            
            # Create model based on type
            if model_type in ['query_volume', 'execution_time', 'temporal_pattern']:
                # Time series and numerical anomalies: Isolation Forest
                model = IsolationForest(
                    n_estimators=100,
                    max_samples='auto',
                    contamination=0.05,  # Expected anomaly rate
                    random_state=42
                )
            elif model_type in ['user_behavior', 'access_pattern']:
                # Behavioral anomalies: DBSCAN
                model = DBSCAN(
                    eps=0.5,
                    min_samples=5,
                    metric='euclidean'
                )
            else:
                # Default: Isolation Forest
                model = IsolationForest(
                    n_estimators=100,
                    max_samples='auto',
                    contamination=0.05,
                    random_state=42
                )
            
            # Train model
            model.fit(X)
            
            # Save model
            model_path = os.path.join(self.model_dir, f"{model_type}.pkl")
            scaler_path = os.path.join(self.model_dir, f"{model_type}_scaler.pkl")
            pca_path = os.path.join(self.model_dir, f"{model_type}_pca.pkl")
            
            with open(model_path, 'wb') as f:
                pickle.dump(model, f)
            
            if scaler is not None:
                with open(scaler_path, 'wb') as f:
                    pickle.dump(scaler, f)
            
            if pca is not None:
                with open(pca_path, 'wb') as f:
                    pickle.dump(pca, f)
            
            # Update model info in database
            model_info = db.query(AnomalyModel).filter(
                AnomalyModel.model_type == model_type
            ).first()
            
            if model_info:
                model_info.updated_at = datetime.utcnow()
                model_info.parameters = json.dumps(self._get_model_params(model))
                model_info.training_samples = X.shape[0]
                model_info.feature_count = X.shape[1]
            else:
                model_info = AnomalyModel(
                    model_type=model_type,
                    parameters=json.dumps(self._get_model_params(model)),
                    training_samples=X.shape[0],
                    feature_count=X.shape[1],
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.add(model_info)
            
            db.commit()
            
            # Update in-memory cache
            self.models[model_type] = {
                'model': model,
                'scaler': scaler,
                'pca': pca,
                'parameters': self._get_model_params(model),
                'training_samples': X.shape[0],
                'feature_count': X.shape[1]
            }
            
            self.model_last_loaded[model_type] = time.time()
            
            return {
                "success": True,
                "model_type": model_type,
                "training_samples": X.shape[0],
                "feature_count": X.shape[1]
            }
            
        except Exception as e:
            logger.error(f"Error training {model_type} model: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _get_training_data(self, model_type: str, db: Session) -> List[Dict[str, Any]]:
        """
        Get training data for a specific model type
        
        Args:
            model_type: Type of model to get data for
            db: Database session
            
        Returns:
            List of data samples for training
        """
        # Time range for training data
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=settings.ML_TRAINING_HISTORY_DAYS)
        
        if model_type == 'query_volume':
            # Get query volume data by user and hour
            query = """
            SELECT 
                username,
                user_role,
                target_server,
                EXTRACT(HOUR FROM created_at) as hour_of_day,
                DATE(created_at) as date,
                COUNT(*) as query_count
            FROM 
                audit_logs
            WHERE
                created_at BETWEEN :start_date AND :end_date
            GROUP BY
                username, user_role, target_server, hour_of_day, date
            """
            
            result = db.execute(query, {
                'start_date': start_date,
                'end_date': end_date
            }).fetchall()
            
            return [dict(r._mapping) for r in result]
            
        elif model_type == 'execution_time':
            # Get execution time statistics
            query = """
            SELECT
                username,
                user_role,
                target_server,
                query_type,
                AVG(execution_time_ms) as avg_time,
                MAX(execution_time_ms) as max_time,
                MIN(execution_time_ms) as min_time,
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY execution_time_ms) as median_time,
                PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY execution_time_ms) as p90_time,
                COUNT(*) as query_count
            FROM
                audit_logs
            WHERE
                created_at BETWEEN :start_date AND :end_date
                AND execution_time_ms IS NOT NULL
                AND execution_status = 'success'
            GROUP BY
                username, user_role, target_server, query_type
            """
            
            result = db.execute(query, {
                'start_date': start_date,
                'end_date': end_date
            }).fetchall()
            
            return [dict(r._mapping) for r in result]
            
        elif model_type == 'temporal_pattern':
            # Get temporal patterns (day of week, hour of day)
            query = """
            SELECT
                username,
                user_role,
                target_server,
                EXTRACT(DOW FROM created_at) as day_of_week,
                EXTRACT(HOUR FROM created_at) as hour_of_day,
                COUNT(*) as query_count
            FROM
                audit_logs
            WHERE
                created_at BETWEEN :start_date AND :end_date
            GROUP BY
                username, user_role, target_server, day_of_week, hour_of_day
            """
            
            result = db.execute(query, {
                'start_date': start_date,
                'end_date': end_date
            }).fetchall()
            
            return [dict(r._mapping) for r in result]
            
        elif model_type == 'user_behavior':
            # Get user behavior patterns
            query = """
            SELECT
                username,
                user_role,
                client_ip,
                COUNT(*) as query_count,
                COUNT(DISTINCT target_server) as distinct_servers,
                COUNT(DISTINCT query_hash) as distinct_queries,
                SUM(CASE WHEN execution_status != 'success' THEN 1 ELSE 0 END) as error_count,
                AVG(execution_time_ms) as avg_time
            FROM
                audit_logs
            WHERE
                created_at BETWEEN :start_date AND :end_date
            GROUP BY
                username, user_role, client_ip
            """
            
            result = db.execute(query, {
                'start_date': start_date,
                'end_date': end_date
            }).fetchall()
            
            return [dict(r._mapping) for r in result]
            
        elif model_type == 'query_content':
            # Get query content patterns (not implemented in this simplified example)
            # In a real implementation, this would involve NLP or embedding techniques
            return []
            
        elif model_type == 'access_pattern':
            # Get access patterns (which users access which tables)
            query = """
            SELECT
                username,
                user_role,
                target_server,
                tables_accessed,
                COUNT(*) as access_count
            FROM (
                SELECT
                    a.username,
                    a.user_role,
                    a.target_server,
                    a.query_text,
                    a.tables_accessed
                FROM
                    audit_logs a
                WHERE
                    a.created_at BETWEEN :start_date AND :end_date
                    AND a.tables_accessed IS NOT NULL
            ) subq
            GROUP BY
                username, user_role, target_server, tables_accessed
            """
            
            result = db.execute(query, {
                'start_date': start_date,
                'end_date': end_date
            }).fetchall()
            
            return [dict(r._mapping) for r in result]
        
        # Default: empty list
        return []
    
    def _preprocess_data(
        self, 
        data: List[Dict[str, Any]], 
        model_type: str
    ) -> Tuple[np.ndarray, Optional[StandardScaler], Optional[PCA]]:
        """
        Preprocess training data
        
        Args:
            data: Raw training data
            model_type: Type of model being trained
            
        Returns:
            Tuple of (preprocessed_data, scaler, pca)
        """
        if not data:
            return np.array([]), None, None
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Define features based on model type
        if model_type == 'query_volume':
            # For query volume anomalies
            features = ['query_count']
            categorical = ['username', 'user_role', 'target_server', 'hour_of_day']
            
        elif model_type == 'execution_time':
            # For execution time anomalies
            features = ['avg_time', 'max_time', 'min_time', 'median_time', 'p90_time', 'query_count']
            categorical = ['username', 'user_role', 'target_server', 'query_type']
            
        elif model_type == 'temporal_pattern':
            # For temporal pattern anomalies
            features = ['query_count']
            categorical = ['username', 'user_role', 'target_server', 'day_of_week', 'hour_of_day']
            
        elif model_type == 'user_behavior':
            # For user behavior anomalies
            features = ['query_count', 'distinct_servers', 'distinct_queries', 'error_count', 'avg_time']
            categorical = ['username', 'user_role', 'client_ip']
            
        elif model_type == 'access_pattern':
            # For access pattern anomalies
            features = ['access_count']
            categorical = ['username', 'user_role', 'target_server', 'tables_accessed']
            
        else:
            # Default features
            features = list(df.select_dtypes(include=['number']).columns)
            categorical = list(df.select_dtypes(include=['object']).columns)
        
        # Ensure all required columns exist
        for col in features + categorical:
            if col not in df.columns:
                # For missing numeric columns, add with 0
                if col in features:
                    df[col] = 0
                # For missing categorical columns, add as 'unknown'
                else:
                    df[col] = 'unknown'
        
        # One-hot encode categorical features
        df_encoded = pd.get_dummies(df, columns=categorical, drop_first=False)
        
        # Select only numeric columns
        X = df_encoded.select_dtypes(include=['number']).fillna(0).values
        
        # Scale features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Apply PCA if there are many features
        pca = None
        if X_scaled.shape[1] > 10:
            n_components = min(X_scaled.shape[1], 10)
            pca = PCA(n_components=n_components)
            X_scaled = pca.fit_transform(X_scaled)
        
        return X_scaled, scaler, pca
    
    def _get_model_params(self, model) -> Dict[str, Any]:
        """
        Get model parameters for storage
        
        Args:
            model: Trained model
            
        Returns:
            Dictionary of model parameters
        """
        if isinstance(model, IsolationForest):
            return {
                'type': 'isolation_forest',
                'n_estimators': model.n_estimators,
                'max_samples': model.max_samples,
                'contamination': model.contamination
            }
        elif isinstance(model, DBSCAN):
            return {
                'type': 'dbscan',
                'eps': model.eps,
                'min_samples': model.min_samples,
                'metric': model.metric
            }
        else:
            return {'type': str(type(model).__name__)}
    
    def _detect_anomaly_with_model(
        self,
        model_type: str,
        model,
        features,
        query_id: int,
        query_text: str,
        username: str,
        user_role: str,
        server_alias: str,
        execution_time_ms: Optional[float]
    ) -> Optional[Dict[str, Any]]:
        """
        Detect anomaly using a specific model
        
        Args:
            model_type: Type of model
            model: Trained model
            features: Query features
            query_id: Query ID
            query_text: Query text
            username: Username
            user_role: User role
            server_alias: Server alias
            execution_time_ms: Execution time in ms
            
        Returns:
            Anomaly information or None if no anomaly
        """
        try:
            # Format features properly
            if isinstance(features, dict):
                # For dict-like features, flatten
                X = np.array(list(features.values())).reshape(1, -1)
            elif isinstance(features, list):
                # For list features
                X = np.array(features).reshape(1, -1)
            else:
                # Assume X is already in the right format
                X = features
                if len(X.shape) == 1:
                    X = X.reshape(1, -1)
            
            # Detect anomaly based on model type
            if isinstance(model, IsolationForest):
                # Anomaly score (-1 for anomalies, 1 for normal)
                score = model.decision_function(X)[0]
                # Convert to 0-1 range (1 = certain anomaly)
                anomaly_score = 1 - (score + 1) / 2
                is_anomaly = anomaly_score > self.anomaly_thresholds[model_type]['low']
                
            elif isinstance(model, DBSCAN):
                # Check cluster assignment (-1 for outliers)
                cluster = model.fit_predict(X)[0]
                is_anomaly = cluster == -1
                anomaly_score = 1.0 if is_anomaly else 0.0
                
            else:
                # Default handling
                is_anomaly = False
                anomaly_score = 0.0
            
            # Return None if not an anomaly
            if not is_anomaly:
                return None
            
            # Determine severity
            severity = 'low'
            for sev, threshold in sorted(
                self.anomaly_thresholds[model_type].items(),
                key=lambda x: x[1],
                reverse=True
            ):
                if anomaly_score >= threshold:
                    severity = sev
                    break
            
            # Format anomaly details based on model type
            if model_type == 'query_volume':
                details = {
                    'anomaly_score': float(anomaly_score),
                    'current_volume': float(features['query_count']) if isinstance(features, dict) else float(X[0][0]),
                    'typical_volume': 'Unknown',  # Would calculate this from historical data
                    'percent_increase': 'Unknown',  # Would calculate this from historical data
                }
                
            elif model_type == 'execution_time':
                details = {
                    'anomaly_score': float(anomaly_score),
                    'execution_time': float(execution_time_ms) if execution_time_ms else 0.0,
                    'typical_time': 'Unknown',  # Would calculate this from historical data
                    'percent_increase': 'Unknown',  # Would calculate this from historical data
                }
                
            elif model_type == 'temporal_pattern':
                current_hour = datetime.utcnow().hour
                details = {
                    'anomaly_score': float(anomaly_score),
                    'hour_of_day': current_hour,
                    'typical_activity': 'Low',  # Would classify this based on historical data
                    'current_activity': 'High',  # Would classify this based on historical data
                }
                
            elif model_type == 'user_behavior':
                details = {
                    'anomaly_score': float(anomaly_score),
                    'behavior_change': 'Unusual query pattern',  # Would be more specific in real implementation
                    'typical_behavior': 'Unknown',  # Would calculate this from historical data
                }
                
            elif model_type == 'access_pattern':
                details = {
                    'anomaly_score': float(anomaly_score),
                    'tables_accessed': 'Unknown',  # Would extract this from query
                    'unusual_access': 'Accessing tables not normally accessed by this user',  # Would be more specific
                }
                
            else:
                details = {
                    'anomaly_score': float(anomaly_score)
                }
            
            # Create anomaly information
            anomaly_info = {
                'model_type': model_type,
                'anomaly_type': self._map_model_to_anomaly_type(model_type),
                'severity': severity,
                'score': float(anomaly_score),
                'query_id': query_id,
                'query_text': query_text,
                'username': username,
                'user_role': user_role,
                'server_alias': server_alias,
                'details': details
            }
            
            return anomaly_info
            
        except Exception as e:
            logger.error(f"Error detecting anomaly with {model_type} model: {str(e)}")
            return None
    
    def _map_model_to_anomaly_type(self, model_type: str) -> str:
        """
        Map model type to anomaly type
        
        Args:
            model_type: Type of model
            
        Returns:
            Anomaly type string
        """
        if model_type == 'query_volume':
            return 'query_volume'
        elif model_type == 'execution_time':
            return 'slow_query'
        elif model_type == 'temporal_pattern':
            return 'unusual_time'
        elif model_type == 'user_behavior':
            return 'unusual_behavior'
        elif model_type == 'query_content':
            return 'suspicious_query'
        elif model_type == 'access_pattern':
            return 'unusual_access'
        else:
            return 'unknown'
    
    def _ensure_models_loaded(self, db: Session) -> None:
        """
        Ensure all models are loaded in memory
        
        Args:
            db: Database session
        """
        # Get all model types
        model_types = list(self.feature_extractors.keys())
        
        for model_type in model_types:
            # Check if model is already loaded and fresh
            if (
                model_type in self.models and 
                model_type in self.model_last_loaded and
                time.time() - self.model_last_loaded[model_type] < self.model_update_interval
            ):
                continue
            
            # Get model info from database
            model_info = db.query(AnomalyModel).filter(
                AnomalyModel.model_type == model_type
            ).first()
            
            if not model_info:
                logger.warning(f"No model information found for {model_type}")
                self.models[model_type] = {}
                continue
            
            # Check if model file exists
            model_path = os.path.join(self.model_dir, f"{model_type}.pkl")
            scaler_path = os.path.join(self.model_dir, f"{model_type}_scaler.pkl")
            pca_path = os.path.join(self.model_dir, f"{model_type}_pca.pkl")
            
            if not os.path.exists(model_path):
                logger.warning(f"Model file not found for {model_type}")
                self.models[model_type] = {}
                continue
            
            try:
                # Load model and preprocessing components
                with open(model_path, 'rb') as f:
                    model = pickle.load(f)
                
                scaler = None
                if os.path.exists(scaler_path):
                    with open(scaler_path, 'rb') as f:
                        scaler = pickle.load(f)
                
                pca = None
                if os.path.exists(pca_path):
                    with open(pca_path, 'rb') as f:
                        pca = pickle.load(f)
                
                # Store in cache
                self.models[model_type] = {
                    'model': model,
                    'scaler': scaler,
                    'pca': pca,
                    'parameters': json.loads(model_info.parameters) if model_info.parameters else {},
                    'training_samples': model_info.training_samples,
                    'feature_count': model_info.feature_count
                }
                
                self.model_last_loaded[model_type] = time.time()
                
                logger.info(f"Loaded {model_type} model (trained on {model_info.training_samples} samples)")
                
            except Exception as e:
                logger.error(f"Error loading {model_type} model: {str(e)}")
                self.models[model_type] = {}
    
    def _extract_features(
        self,
        query_id: int,
        query_text: str,
        username: str,
        user_role: str,
        server_alias: str,
        execution_time_ms: Optional[float],
        db: Session
    ) -> Dict[str, Any]:
        """
        Extract features for all model types
        
        Args:
            query_id: Query ID
            query_text: Query text
            username: Username
            user_role: User role
            server_alias: Server alias
            execution_time_ms: Execution time in ms
            db: Database session
            
        Returns:
            Dictionary of features for each model type
        """
        features = {}
        
        # Extract features for each model type
        for model_type, extractor in self.feature_extractors.items():
            if model_type not in self.models or not self.models[model_type]:
                continue
                
            try:
                model_features = extractor(
                    query_id,
                    query_text,
                    username,
                    user_role,
                    server_alias,
                    execution_time_ms,
                    db
                )
                
                if model_features is not None:
                    features[model_type] = model_features
                    
            except Exception as e:
                logger.error(f"Error extracting {model_type} features: {str(e)}")
        
        return features
    
    def _extract_query_volume_features(
        self,
        query_id: int,
        query_text: str,
        username: str,
        user_role: str,
        server_alias: str,
        execution_time_ms: Optional[float],
        db: Session
    ) -> Optional[Dict[str, float]]:
        """
        Extract features for query volume anomaly detection
        
        Args:
            query_id: Query ID
            query_text: Query text
            username: Username
            user_role: User role
            server_alias: Server alias
            execution_time_ms: Execution time in ms
            db: Database session
            
        Returns:
            Dictionary of features or None if not possible
        """
        try:
            # Get current hour
            current_dt = datetime.utcnow()
            current_hour = current_dt.hour
            lookback_minutes = 10
            
            # Get recent query count for this user and server in the last few minutes
            query = """
            SELECT COUNT(*) as recent_count
            FROM audit_logs
            WHERE username = :username
              AND target_server = :server_alias
              AND created_at >= :start_time
            """
            
            start_time = current_dt - timedelta(minutes=lookback_minutes)
            
            result = db.execute(query, {
                'username': username,
                'server_alias': server_alias,
                'start_time': start_time
            }).scalar()
            
            recent_count = result or 0
            
            # Get historical average for this user, server, and hour
            query = """
            SELECT AVG(query_count) as avg_count
            FROM (
                SELECT 
                    DATE(created_at) as date,
                    COUNT(*) as query_count
                FROM 
                    audit_logs
                WHERE 
                    username = :username
                    AND target_server = :server_alias
                    AND EXTRACT(HOUR FROM created_at) = :hour
                    AND created_at >= :start_date
                    AND created_at < :end_date
                GROUP BY
                    date
            ) as daily_counts
            """
            
            end_date = current_dt.date()
            start_date = end_date - timedelta(days=settings.ML_TRAINING_HISTORY_DAYS)
            
            avg_result = db.execute(query, {
                'username': username,
                'server_alias': server_alias,
                'hour': current_hour,
                'start_date': start_date,
                'end_date': end_date
            }).scalar()
            
            avg_count = avg_result or 0
            
            # Create feature vector
            # Scale recent count to hourly rate for comparison
            hourly_rate = (recent_count / lookback_minutes) * 60
            
            features = {
                'query_count': hourly_rate,
                'avg_historical': avg_count,
                'ratio': hourly_rate / max(avg_count, 1),
                'hour': current_hour
            }
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting query volume features: {str(e)}")
            return None
    
    def _extract_execution_time_features(
        self,
        query_id: int,
        query_text: str,
        username: str,
        user_role: str,
        server_alias: str,
        execution_time_ms: Optional[float],
        db: Session
    ) -> Optional[Dict[str, float]]:
        """
        Extract features for execution time anomaly detection
        
        Args:
            query_id: Query ID
            query_text: Query text
            username: Username
            user_role: User role
            server_alias: Server alias
            execution_time_ms: Execution time in ms
            db: Database session
            
        Returns:
            Dictionary of features or None if not possible
        """
        if not execution_time_ms:
            return None
            
        try:
            # Get the query type
            query_type = self._get_query_type(query_text)
            
            # Get historical execution time statistics for similar queries
            query = """
            SELECT 
                AVG(execution_time_ms) as avg_time,
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY execution_time_ms) as median_time,
                PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY execution_time_ms) as p90_time,
                PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY execution_time_ms) as p95_time,
                COUNT(*) as count
            FROM 
                audit_logs
            WHERE 
                target_server = :server_alias
                AND query_type = :query_type
                AND execution_status = 'success'
                AND execution_time_ms IS NOT NULL
                AND created_at >= :start_date
            """
            
            start_date = datetime.utcnow() - timedelta(days=settings.ML_TRAINING_HISTORY_DAYS)
            
            result = db.execute(query, {
                'server_alias': server_alias,
                'query_type': query_type,
                'start_date': start_date
            }).first()
            
            if not result or not result.count or result.count < 10:
                # Not enough historical data
                return None
            
            avg_time = result.avg_time or 0
            median_time = result.median_time or 0
            p90_time = result.p90_time or 0
            p95_time = result.p95_time or 0
            
            # Create feature vector
            features = {
                'execution_time': execution_time_ms,
                'avg_historical': avg_time,
                'median_historical': median_time,
                'p90_historical': p90_time,
                'p95_historical': p95_time,
                'ratio_to_avg': execution_time_ms / max(avg_time, 1),
                'ratio_to_p90': execution_time_ms / max(p90_time, 1),
                'ratio_to_p95': execution_time_ms / max(p95_time, 1)
            }
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting execution time features: {str(e)}")
            return None
    
    def _extract_temporal_pattern_features(
        self,
        query_id: int,
        query_text: str,
        username: str,
        user_role: str,
        server_alias: str,
        execution_time_ms: Optional[float],
        db: Session
    ) -> Optional[Dict[str, float]]:
        """
        Extract features for temporal pattern anomaly detection
        
        Args:
            query_id: Query ID
            query_text: Query text
            username: Username
            user_role: User role
            server_alias: Server alias
            execution_time_ms: Execution time in ms
            db: Database session
            
        Returns:
            Dictionary of features or None if not possible
        """
        try:
            # Get current time details
            current_dt = datetime.utcnow()
            current_hour = current_dt.hour
            current_dow = current_dt.weekday()  # 0-6 for Monday-Sunday
            
            # Get historical activity level for this user at this time
            query = """
            SELECT 
                AVG(query_count) as avg_count,
                MAX(query_count) as max_count
            FROM (
                SELECT 
                    DATE(created_at) as date,
                    COUNT(*) as query_count
                FROM 
                    audit_logs
                WHERE 
                    username = :username
                    AND EXTRACT(HOUR FROM created_at) = :hour
                    AND EXTRACT(DOW FROM created_at) = :dow
                    AND created_at >= :start_date
                GROUP BY
                    date
            ) as daily_counts
            """
            
            start_date = current_dt.date() - timedelta(days=settings.ML_TRAINING_HISTORY_DAYS)
            
            result = db.execute(query, {
                'username': username,
                'hour': current_hour,
                'dow': current_dow,
                'start_date': start_date
            }).first()
            
            if not result:
                # Not enough historical data
                return None
            
            avg_count = result.avg_count or 0
            max_count = result.max_count or 0
            
            # Get recent query count in the past hour
            recent_query = """
            SELECT 
                COUNT(*) as recent_count
            FROM 
                audit_logs
            WHERE 
                username = :username
                AND created_at >= :start_time
            """
            
            recent_result = db.execute(recent_query, {
                'username': username,
                'start_time': current_dt - timedelta(hours=1)
            }).scalar()
            
            recent_count = recent_result or 0
            
            # Create feature vector
            features = {
                'hour_of_day': current_hour,
                'day_of_week': current_dow,
                'recent_count': recent_count,
                'avg_historical': avg_count,
                'max_historical': max_count,
                'ratio_to_avg': recent_count / max(avg_count, 1),
                'ratio_to_max': recent_count / max(max_count, 1),
                'is_weekend': 1 if current_dow >= 5 else 0,  # 5-6 are Saturday-Sunday
                'is_business_hours': 1 if 8 <= current_hour <= 18 else 0
            }
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting temporal pattern features: {str(e)}")
            return None
    
    def _extract_user_behavior_features(
        self,
        query_id: int,
        query_text: str,
        username: str,
        user_role: str,
        server_alias: str,
        execution_time_ms: Optional[float],
        db: Session
    ) -> Optional[Dict[str, float]]:
        """
        Extract features for user behavior anomaly detection
        
        Args:
            query_id: Query ID
            query_text: Query text
            username: Username
            user_role: User role
            server_alias: Server alias
            execution_time_ms: Execution time in ms
            db: Database session
            
        Returns:
            Dictionary of features or None if not possible
        """
        try:
            # Get recent user behavior patterns
            lookback_days = 7
            start_date = datetime.utcnow() - timedelta(days=lookback_days)
            
            query = """
            SELECT 
                COUNT(*) as query_count,
                COUNT(DISTINCT target_server) as distinct_servers,
                COUNT(DISTINCT query_hash) as distinct_queries,
                SUM(CASE WHEN execution_status != 'success' THEN 1 ELSE 0 END) as error_count,
                AVG(execution_time_ms) as avg_time,
                COUNT(DISTINCT DATE(created_at)) as active_days
            FROM 
                audit_logs
            WHERE 
                username = :username
                AND created_at >= :start_date
            """
            
            result = db.execute(query, {
                'username': username,
                'start_date': start_date
            }).first()
            
            if not result or not result.query_count:
                # Not enough historical data
                return None
            
            # Calculate daily averages
            active_days = max(result.active_days or 1, 1)
            queries_per_day = result.query_count / active_days
            servers_per_day = result.distinct_servers / active_days
            unique_queries_per_day = result.distinct_queries / active_days
            errors_per_day = result.error_count / active_days
            error_rate = result.error_count / max(result.query_count, 1)
            
            # Get information about the current query
            query_complexity = self._calculate_query_complexity(query_text)
            query_type = self._get_query_type(query_text)
            query_risk_level = self._assess_query_risk(query_text, query_type)
            
            # Create feature vector
            features = {
                'queries_per_day': queries_per_day,
                'servers_per_day': servers_per_day,
                'unique_queries_per_day': unique_queries_per_day,
                'errors_per_day': errors_per_day,
                'error_rate': error_rate,
                'avg_execution_time': result.avg_time or 0,
                'query_complexity': query_complexity,
                'query_risk_level': query_risk_level
            }
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting user behavior features: {str(e)}")
            return None
    
    def _extract_query_content_features(
        self,
        query_id: int,
        query_text: str,
        username: str,
        user_role: str,
        server_alias: str,
        execution_time_ms: Optional[float],
        db: Session
    ) -> Optional[Dict[str, float]]:
        """
        Extract features for query content anomaly detection
        
        Args:
            query_id: Query ID
            query_text: Query text
            username: Username
            user_role: User role
            server_alias: Server alias
            execution_time_ms: Execution time in ms
            db: Database session
            
        Returns:
            Dictionary of features or None if not possible
        """
        # Not implemented in this simplified example
        # In a real implementation, this would use NLP or embedding techniques
        return None
    
    def _extract_access_pattern_features(
        self,
        query_id: int,
        query_text: str,
        username: str,
        user_role: str,
        server_alias: str,
        execution_time_ms: Optional[float],
        db: Session
    ) -> Optional[Dict[str, float]]:
        """
        Extract features for access pattern anomaly detection
        
        Args:
            query_id: Query ID
            query_text: Query text
            username: Username
            user_role: User role
            server_alias: Server alias
            execution_time_ms: Execution time in ms
            db: Database session
            
        Returns:
            Dictionary of features or None if not possible
        """
        try:
            # Extract tables accessed in this query
            tables = self._extract_tables_from_query(query_text)
            
            if not tables:
                return None
            
            # Get historical table access patterns for this user
            lookback_days = 30
            start_date = datetime.utcnow() - timedelta(days=lookback_days)
            
            # This query would need to be adapted based on your schema
            # It assumes you have a way to extract tables from queries
            query = """
            SELECT 
                table_name,
                COUNT(*) as access_count
            FROM 
                audit_logs,
                UNNEST(tables_accessed) as table_name
            WHERE 
                username = :username
                AND created_at >= :start_date
            GROUP BY
                table_name
            """
            
            result = db.execute(query, {
                'username': username,
                'start_date': start_date
            }).fetchall()
            
            if not result:
                # Not enough historical data
                return None
            
            # Create a dictionary of historical access counts
            historical_access = {r.table_name: r.access_count for r in result}
            
            # Calculate access patterns
            features = {}
            
            # For each table in the current query
            for table in tables:
                # Check if this user has accessed this table before
                if table in historical_access:
                    features[f"table_{table}_known"] = 1
                    features[f"table_{table}_count"] = historical_access[table]
                else:
                    features[f"table_{table}_known"] = 0
                    features[f"table_{table}_count"] = 0
            
            # Calculate ratio of new tables
            known_tables = sum(1 for table in tables if table in historical_access)
            new_tables = len(tables) - known_tables
            features['new_table_ratio'] = new_tables / max(len(tables), 1)
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting access pattern features: {str(e)}")
            return None
    
    def _get_query_type(self, query_text: str) -> str:
        """
        Get the type of a SQL query
        
        Args:
            query_text: SQL query text
            
        Returns:
            Query type (SELECT, INSERT, UPDATE, DELETE, etc.)
        """
        if not query_text:
            return "UNKNOWN"
        
        # Simple regex-based detection
        query_text = query_text.strip().upper()
        
        if query_text.startswith("SELECT"):
            return "SELECT"
        elif query_text.startswith("INSERT"):
            return "INSERT"
        elif query_text.startswith("UPDATE"):
            return "UPDATE"
        elif query_text.startswith("DELETE"):
            return "DELETE"
        elif query_text.startswith("CREATE"):
            return "CREATE"
        elif query_text.startswith("ALTER"):
            return "ALTER"
        elif query_text.startswith("DROP"):
            return "DROP"
        elif query_text.startswith("TRUNCATE"):
            return "TRUNCATE"
        else:
            return "OTHER"
    
    def _calculate_query_complexity(self, query_text: str) -> float:
        """
        Calculate the complexity of a SQL query
        
        Args:
            query_text: SQL query text
            
        Returns:
            Complexity score (0-10)
        """
        if not query_text:
            return 0
        
        # Simple heuristic-based approach
        complexity = 0
        
        # Length-based complexity
        length = len(query_text)
        if length > 1000:
            complexity += 3
        elif length > 500:
            complexity += 2
        elif length > 200:
            complexity += 1
        
        # JOIN complexity
        join_count = query_text.upper().count("JOIN")
        complexity += min(join_count, 4)
        
        # Subquery complexity
        subquery_count = query_text.count("(SELECT")
        complexity += min(subquery_count * 2, 4)
        
        # Aggregate function complexity
        if any(func in query_text.upper() for func in ["GROUP BY", "HAVING", "SUM(", "AVG(", "COUNT("]):
            complexity += 1
        
        # Limit to 0-10 range
        return min(complexity, 10)
    
    def _assess_query_risk(self, query_text: str, query_type: str) -> float:
        """
        Assess the risk level of a SQL query
        
        Args:
            query_text: SQL query text
            query_type: Query type
            
        Returns:
            Risk score (0-10)
        """
        if not query_text:
            return 0
        
        # Simple heuristic-based approach
        risk = 0
        
        # Base risk by query type
        if query_type in ["DELETE", "TRUNCATE", "DROP"]:
            risk += 5
        elif query_type == "UPDATE":
            risk += 3
        elif query_type == "INSERT":
            risk += 2
        elif query_type == "ALTER":
            risk += 4
        elif query_type == "SELECT":
            risk += 1
        
        # Risk for mass operations without WHERE
        if query_type in ["UPDATE", "DELETE"] and "WHERE" not in query_text.upper():
            risk += 5
        
        # Risk for SELECT without LIMIT
        if query_type == "SELECT" and "LIMIT" not in query_text.upper():
            risk += 1
        
        # Risk for potential SQL injection patterns
        if "'" in query_text or ";" in query_text:
            risk += 2
        
        # Limit to 0-10 range
        return min(risk, 10)
    
    def _extract_tables_from_query(self, query_text: str) -> List[str]:
        """
        Extract table names from a SQL query
        
        Args:
            query_text: SQL query text
            
        Returns:
            List of table names
        """
        if not query_text:
            return []
        
        # In a real implementation, this would use a proper SQL parser
        # This is a simplified approach using regex
        
        # Convert to uppercase for consistency
        query_text = query_text.upper()
        
        tables = []
        
        # Extract tables from FROM clause
        from_parts = query_text.split('FROM ')
        for i in range(1, len(from_parts)):
            part = from_parts[i].strip()
            # Get the first word after FROM
            if ' ' in part:
                table = part.split(' ')[0].strip(',;()')
                if table:
                    tables.append(table)
        
        # Extract tables from JOIN clauses
        join_parts = query_text.split('JOIN ')
        for i in range(1, len(join_parts)):
            part = join_parts[i].strip()
            # Get the first word after JOIN
            if ' ' in part:
                table = part.split(' ')[0].strip(',;()')
                if table:
                    tables.append(table)
        
        # Extract tables from UPDATE clause
        if query_text.startswith('UPDATE '):
            part = query_text[7:].strip()
            # Get the first word after UPDATE
            if ' ' in part:
                table = part.split(' ')[0].strip(',;()')
                if table:
                    tables.append(table)
        
        # Extract tables from INSERT INTO clause
        insert_parts = query_text.split('INSERT INTO ')
        for i in range(1, len(insert_parts)):
            part = insert_parts[i].strip()
            # Get the first word after INSERT INTO
            if ' ' in part:
                table = part.split(' ')[0].strip(',;()')
                if table:
                    tables.append(table)
        
        # Remove duplicates and return
        return list(set(tables))

# Create singleton instance
anomaly_detection = AnomalyDetection()

# Son güncelleme: 2025-05-20 10:16:22
# Güncelleyen: Teeksss