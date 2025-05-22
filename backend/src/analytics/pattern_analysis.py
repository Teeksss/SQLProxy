from typing import Dict, List
import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
from .feature_extractor import QueryFeatureExtractor

class QueryPatternAnalyzer:
    def __init__(self):
        self.feature_extractor = QueryFeatureExtractor()
        
    async def analyze_patterns(self, queries: List[Dict]) -> Dict:
        """Query pattern analizi yapar."""
        # Feature extraction
        features = await self._extract_features(queries)
        
        # Pattern clustering
        clusters = await self._cluster_patterns(features)
        
        # Pattern analysis
        analysis = {
            'clusters': clusters,
            'similar_queries': await self._find_similar_queries(queries, features),
            'optimizable_patterns': await self._find_optimizable_patterns(queries),
            'anti_patterns': await self._detect_anti_patterns(queries)
        }
        
        return analysis
        
    async def _extract_features(self, queries: List[Dict]) -> np.ndarray:
        """Query özelliklerini çıkarır."""
        features = []
        
        for query in queries:
            query_features = await self.feature_extractor.extract(query)
            features.append(query_features)
            
        return np.array(features)
        
    async def _cluster_patterns(self, features: np.ndarray) -> List[Dict]:
        """Query patternlerini cluster'lar."""
        # Normalize features
        scaler = StandardScaler()
        scaled_features = scaler.fit_transform(features)
        
        # DBSCAN clustering
        dbscan = DBSCAN(eps=0.3, min_samples=5)
        clusters = dbscan.fit_predict(scaled_features)
        
        # Analyze clusters
        cluster_info = []
        for cluster_id in np.unique(clusters):
            if cluster_id == -1:
                continue  # Skip noise
                
            cluster_features = features[clusters == cluster_id]
            cluster_info.append({
                'cluster_id': int(cluster_id),
                'size': len(cluster_features),
                'centroid': np.mean(cluster_features, axis=0),
                'variance': np.var(cluster_features, axis=0)
            })
            
        return cluster_info