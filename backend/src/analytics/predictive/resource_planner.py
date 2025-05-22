from typing import Dict, List
import numpy as np
from datetime import datetime, timedelta
from .capacity_analyzer import CapacityAnalyzer
from .cost_optimizer import CostOptimizer

class ResourcePlanner:
    def __init__(self):
        self.capacity_analyzer = CapacityAnalyzer()
        self.cost_optimizer = CostOptimizer()
        
    async def plan_resources(self, workload_prediction: Dict) -> Dict:
        """Resource planlaması yapar."""
        # Current capacity analysis
        current_capacity = await self.capacity_analyzer.analyze_current()
        
        # Required capacity calculation
        required_capacity = await self._calculate_required_capacity(
            workload_prediction
        )
        
        # Optimization suggestions
        optimizations = await self.cost_optimizer.optimize(
            current_capacity,
            required_capacity
        )
        
        return {
            'current_capacity': current_capacity,
            'required_capacity': required_capacity,
            'recommendations': optimizations,
            'timeline': self._create_timeline(
                current_capacity,
                required_capacity
            )
        }
        
    async def _calculate_required_capacity(self,
                                        prediction: Dict) -> Dict:
        """Gerekli kapasiteyi hesaplar."""
        required = {
            'cpu': self._calculate_cpu_requirements(prediction),
            'memory': self._calculate_memory_requirements(prediction),
            'storage': self._calculate_storage_requirements(prediction),
            'network': self._calculate_network_requirements(prediction)
        }
        
        # Add safety margins
        required = self._apply_safety_margins(required)
        
        return required
        
    def _create_timeline(self, current: Dict,
                        required: Dict) -> List[Dict]:
        """Kaynak planı timeline'ı oluşturur."""
        timeline = []
        now = datetime.utcnow()
        
        for hour in range(24):
            timestamp = now + timedelta(hours=hour)
            timeline.append({
                'timestamp': timestamp.isoformat(),
                'cpu_utilization': required['cpu'][hour] / current['cpu'],
                'memory_utilization': required['memory'][hour] / current['memory'],
                'storage_utilization': required['storage'][hour] / current['storage'],
                'network_utilization': required['network'][hour] / current['network']
            })
            
        return timeline