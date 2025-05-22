from typing import Dict, List
import numpy as np
from datetime import datetime, timedelta
from .models import Permission, AccessPattern
from .risk_analyzer import RiskAnalyzer

class PermissionOptimizer:
    def __init__(self):
        self.risk_analyzer = RiskAnalyzer()
        self.optimization_window = timedelta(days=30)
        
    async def optimize_permissions(self) -> Dict:
        """Permission'ları optimize eder."""
        # Get current permissions
        current_permissions = await self._get_current_permissions()
        
        # Analyze usage patterns
        usage_patterns = await self._analyze_usage_patterns(
            current_permissions
        )
        
        # Generate optimization suggestions
        suggestions = await self._generate_suggestions(
            current_permissions,
            usage_patterns
        )
        
        # Risk analysis
        risk_assessment = await self.risk_analyzer.analyze_changes(
            suggestions
        )
        
        return {
            'suggestions': suggestions,
            'risk_assessment': risk_assessment,
            'metadata': {
                'analyzed_permissions': len(current_permissions),
                'optimization_count': len(suggestions),
                'timestamp': datetime.utcnow()
            }
        }
        
    async def _analyze_usage_patterns(self,
                                    permissions: List[Dict]) -> Dict:
        """Permission kullanım pattern'lerini analiz eder."""
        patterns = {}
        
        for permission in permissions:
            # Get usage history
            history = await self._get_permission_history(
                permission['id']
            )
            
            # Analyze patterns
            pattern = {
                'frequency': self._calculate_frequency(history),
                'last_used': self._get_last_usage(history),
                'access_times': self._analyze_access_times(history),
                'common_contexts': self._find_common_contexts(history)
            }
            
            patterns[permission['id']] = pattern
            
        return patterns
        
    async def _generate_suggestions(self, permissions: List[Dict],
                                  patterns: Dict) -> List[Dict]:
        """Optimization önerileri oluşturur."""
        suggestions = []
        
        for permission in permissions:
            pattern = patterns.get(permission['id'])
            
            if not pattern:
                continue
                
            # Check for unused permissions
            if self._is_unused(pattern):
                suggestions.append({
                    'type': 'remove',
                    'permission_id': permission['id'],
                    'reason': 'Unused permission',
                    'confidence': 0.9
                })
                
            # Check for over-privileged permissions
            elif self._is_over_privileged(pattern):
                suggestions.append({
                    'type': 'restrict',
                    'permission_id': permission['id'],
                    'suggested_scope': self._calculate_optimal_scope(pattern),
                    'reason': 'Over-privileged permission',
                    'confidence': 0.8
                })
                
        return suggestions