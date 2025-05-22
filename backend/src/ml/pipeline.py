from typing import Dict, List
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from .models import MLModel, ModelVersion, Feature
from .preprocessors import FeaturePreprocessor

class MLPipelineManager:
    def __init__(self):
        self.feature_processor = FeaturePreprocessor()
        self.models: Dict[str, MLModel] = {}
        self.versions: Dict[str, List[ModelVersion]] = {}
        
    async def train_model(self, name: str,
                         data: pd.DataFrame,
                         config: Dict) -> Dict:
        """Model eğitimi yapar."""
        try:
            # Preprocess data
            X, y = await self._prepare_data(data, config)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            # Create pipeline
            pipeline = self._create_pipeline(config)
            
            # Train model
            pipeline.fit(X_train, y_train)
            
            # Evaluate model
            metrics = await self._evaluate_model(
                pipeline, X_test, y_test
            )
            
            # Save model version
            version = await self._save_model_version(
                name, pipeline, metrics, config
            )
            
            return {
                'status': 'success',
                'model_name': name,
                'version': version.id,
                'metrics': metrics
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
            
    async def predict(self, model_name: str,
                     data: pd.DataFrame,
                     version_id: str = None) -> Dict:
        """Model prediction yapar."""
        try:
            # Get model version
            version = await self._get_model_version(
                model_name, version_id
            )
            
            # Preprocess data
            X = await self.feature_processor.process(
                data, version.config
            )
            
            # Make prediction
            predictions = version.pipeline.predict(X)
            
            # Get prediction probabilities if available
            probabilities = None
            if hasattr(version.pipeline, 'predict_proba'):
                probabilities = version.pipeline.predict_proba(X)
                
            return {
                'status': 'success',
                'predictions': predictions.tolist(),
                'probabilities': probabilities.tolist() if probabilities is not None else None,
                'model_version': version.id
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
            
    async def _evaluate_model(self, pipeline: Pipeline,
                            X_test: np.ndarray,
                            y_test: np.ndarray) -> Dict:
        """Model değerlendirmesi yapar."""
        predictions = pipeline.predict(X_test)
        
        metrics = {
            'accuracy': accuracy_score(y_test, predictions),
            'precision': precision_score(y_test, predictions, average='weighted'),
            'recall': recall_score(y_test, predictions, average='weighted'),
            'f1': f1_score(y_test, predictions, average='weighted')
        }
        
        if hasattr(pipeline, 'predict_proba'):
            probas = pipeline.predict_proba(X_test)
            metrics['roc_auc'] = roc_auc_score(
                y_test, probas, multi_class='ovr'
            )
            
        return metrics