from typing import Dict, List
import numpy as np
import pandas as pd
from statsmodels.tsa.arima.model import ARIMA
from sklearn.decomposition import PCA
from .models import AnalyticsConfig, TimeSeries
from .nlp import NLPProcessor

class AdvancedAnalytics:
    def __init__(self):
        self.nlp_processor = NLPProcessor()
        self.time_series_models = {}
        
    async def analyze_patterns(self, data: pd.DataFrame,
                             config: AnalyticsConfig) -> Dict:
        """Gelişmiş pattern analizi yapar."""
        try:
            # Time series analysis
            time_series = await self._analyze_time_series(
                data, config
            )
            
            # Pattern detection
            patterns = await self._detect_patterns(
                data, config
            )
            
            # Correlation analysis
            correlations = await self._analyze_correlations(
                data
            )
            
            # Dimension reduction
            reduced_data = await self._reduce_dimensions(
                data, config.n_components
            )
            
            return {
                'status': 'success',
                'time_series': time_series,
                'patterns': patterns,
                'correlations': correlations,
                'reduced_data': reduced_data
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
            
    async def predict_trends(self, time_series: TimeSeries,
                           horizon: int = 10) -> Dict:
        """Trend tahmini yapar."""
        try:
            # Fit ARIMA model
            model = ARIMA(
                time_series.values,
                order=self._get_optimal_order(time_series)
            )
            
            results = model.fit()
            
            # Make predictions
            forecast = results.forecast(steps=horizon)
            
            # Calculate confidence intervals
            conf_int = results.get_forecast(horizon).conf_int()
            
            return {
                'status': 'success',
                'forecast': forecast.tolist(),
                'confidence_intervals': conf_int.tolist(),
                'model_metrics': {
                    'aic': results.aic,
                    'bic': results.bic
                }
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
            
    async def process_query_text(self, query: str) -> Dict:
        """NLP tabanlı query analizi."""
        try:
            # Process query
            processed = await self.nlp_processor.process_text(query)
            
            # Extract entities
            entities = await self.nlp_processor.extract_entities(
                processed
            )
            
            # Analyze sentiment
            sentiment = await self.nlp_processor.analyze_sentiment(
                processed
            )
            
            # Get suggestions
            suggestions = await self.nlp_processor.get_suggestions(
                processed, entities
            )
            
            return {
                'status': 'success',
                'entities': entities,
                'sentiment': sentiment,
                'suggestions': suggestions,
                'processed_text': processed
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }