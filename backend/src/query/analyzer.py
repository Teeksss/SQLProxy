from typing import Dict, List
import pandas as pd
from datetime import datetime, timedelta
from .models import QueryMetrics, QueryPattern
from .pattern_detector import PatternDetector

class QueryAnalyzer:
    def __init__(self):
        self.pattern_detector = PatternDetector()
        self.analysis_window = timedelta(hours=24)
        
    async def analyze_queries(self, timeframe: str = '24h') -> Dict:
        """Query analizini gerçekleştirir."""
        # Get query history
        history = await self._get_query_history(timeframe)
        
        # Performance analysis
        performance = await self._analyze_performance(history)
        
        # Pattern analysis
        patterns = await self.pattern_detector.detect_patterns(history)
        
        # Resource impact analysis
        impact = await self._analyze_resource_impact(history)
        
        # Generate insights
        insights = await self._generate_insights(
            performance, patterns, impact
        )
        
        return {
            'performance': performance,
            'patterns': patterns,
            'impact': impact,
            'insights': insights,
            'metadata': {
                'analyzed_queries': len(history),
                'timeframe': timeframe,
                'timestamp': datetime.utcnow()
            }
        }
        
    async def _analyze_performance(self, history: List[Dict]) -> Dict:
        """Query performans analizi."""
        df = pd.DataFrame(history)
        
        return {
            'execution_time': {
                'mean': df['execution_time'].mean(),
                'median': df['execution_time'].median(),
                'p95': df['execution_time'].quantile(0.95),
                'max': df['execution_time'].max()
            },
            'resource_usage': {
                'cpu': self._analyze_cpu_usage(df),
                'memory': self._analyze_memory_usage(df),
                'io': self._analyze_io_usage(df)
            },
            'query_types': {
                'distribution': df['type'].value_counts().to_dict(),
                'complexity': self._analyze_complexity(df)
            }
        }
        
    async def _generate_insights(self, performance: Dict,
                               patterns: Dict,
                               impact: Dict) -> List[Dict]:
        """Query insights oluşturur."""
        insights = []
        
        # Performance insights
        if performance['execution_time']['p95'] > 1.0:  # 1 second
            insights.append({
                'type': 'performance_warning',
                'message': 'High p95 execution time detected',
                'recommendation': 'Consider query optimization'
            })
            
        # Pattern insights
        for pattern in patterns['frequent_patterns']:
            if pattern['impact_score'] > 0.8:
                insights.append({
                    'type': 'pattern_alert',
                    'message': f"High impact pattern detected: {pattern['description']}",
                    'recommendation': pattern['optimization_suggestion']
                })
                
        return insights