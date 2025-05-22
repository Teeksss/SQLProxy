from typing import Dict, List
import pandas as pd
from datetime import datetime, timedelta
from .billing_manager import BillingManager
from .resource_tracker import ResourceTracker

class CostOptimizer:
    def __init__(self):
        self.billing = BillingManager()
        self.tracker = ResourceTracker()
        
    async def optimize_costs(self) -> Dict:
        """Maliyet optimizasyonu yapar."""
        # Current resource usage
        usage = await self.tracker.get_resource_usage()
        
        # Cost analysis
        analysis = await self._analyze_costs(usage)
        
        # Optimization önerileri
        recommendations = self._generate_recommendations(
            analysis
        )
        
        # Saving projections
        projections = self._calculate_saving_projections(
            recommendations
        )
        
        return {
            'current_costs': analysis['current'],
            'potential_savings': projections['total_savings'],
            'recommendations': recommendations,
            'projections': projections
        }
        
    async def _analyze_costs(self, usage: Dict) -> Dict:
        """Maliyet analizi yapar."""
        # Resource bazlı maliyet
        resource_costs = {}
        
        for resource, metrics in usage.items():
            cost = await self.billing.calculate_resource_cost(
                resource, metrics
            )
            resource_costs[resource] = {
                'cost': cost,
                'utilization': metrics['utilization'],
                'waste': self._calculate_waste(
                    metrics['utilization']
                )
            }
            
        # Total cost calculation
        total = sum(rc['cost'] for rc in resource_costs.values())
        
        return {
            'current': total,
            'by_resource': resource_costs,
            'trends': await self._analyze_cost_trends()
        }
        
    def _generate_recommendations(self, analysis: Dict) -> List[Dict]:
        """Optimization önerileri oluşturur."""
        recommendations = []
        
        # Resource waste check
        for resource, metrics in analysis['by_resource'].items():
            if metrics['waste'] > 0.2:  # 20% waste
                recommendations.append({
                    'type': 'resource_reduction',
                    'resource': resource,
                    'potential_savings': metrics['cost'] * metrics['waste'],
                    'impact': 'low',
                    'action': f"Reduce {resource} allocation by {metrics['waste']*100}%"
                })
                
        # Reserved instance önerileri
        ri_recommendations = self._analyze_ri_opportunities(
            analysis
        )
        recommendations.extend(ri_recommendations)
        
        return recommendations