from typing import Dict, List
import numpy as np
from .metrics import ResourceMetrics
from .scheduler import QueryScheduler

class LoadBalancer:
    def __init__(self):
        self.metrics = ResourceMetrics()
        self.scheduler = QueryScheduler()
        self.rebalance_threshold = 0.2  # 20% imbalance
        
    async def balance_load(self) -> Dict:
        """Load balancing yapar."""
        # Current load durumu
        current_load = await self.metrics.get_resource_load()
        
        # İmbalance analizi
        imbalance = self._analyze_imbalance(current_load)
        
        if imbalance['needs_rebalancing']:
            # Rebalancing planı
            plan = self._create_rebalancing_plan(
                current_load, imbalance
            )
            
            # Planı uygula
            results = await self._apply_rebalancing(plan)
            
            return {
                'status': 'rebalanced',
                'changes': results,
                'metrics': await self.metrics.get_resource_load()
            }
            
        return {
            'status': 'balanced',
            'metrics': current_load
        }
        
    def _analyze_imbalance(self, load: Dict) -> Dict:
        """Load imbalance analizi."""
        analysis = {
            'needs_rebalancing': False,
            'imbalanced_resources': []
        }
        
        # CPU imbalance
        cpu_imbalance = self._calculate_resource_imbalance(
            load['cpu']
        )
        if cpu_imbalance > self.rebalance_threshold:
            analysis['needs_rebalancing'] = True
            analysis['imbalanced_resources'].append({
                'type': 'cpu',
                'imbalance': cpu_imbalance,
                'distribution': load['cpu']
            })
            
        # Memory imbalance
        memory_imbalance = self._calculate_resource_imbalance(
            load['memory']
        )
        if memory_imbalance > self.rebalance_threshold:
            analysis['needs_rebalancing'] = True
            analysis['imbalanced_resources'].append({
                'type': 'memory',
                'imbalance': memory_imbalance,
                'distribution': load['memory']
            })
            
        return analysis