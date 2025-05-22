from typing import Dict, List
import numpy as np
from datetime import datetime, timedelta
from .metrics_collector import MetricsCollector
from .resource_manager import ResourceManager
from .cost_calculator import CostCalculator

class AutoScaler:
    def __init__(self):
        self.metrics = MetricsCollector()
        self.resource_manager = ResourceManager()
        self.cost_calculator = CostCalculator()
        self.scale_cooldown = 300  # seconds
        
    async def evaluate_scaling(self) -> Dict:
        """Scaling ihtiyacını değerlendirir."""
        # Current metrics
        current_metrics = await self.metrics.get_current_metrics()
        
        # Scaling analizi
        analysis = await self._analyze_scaling_needs(current_metrics)
        
        # Cost impact
        cost_impact = await self.cost_calculator.calculate_scaling_impact(
            analysis
        )
        
        # Scaling kararı
        decision = self._make_scaling_decision(analysis, cost_impact)
        
        if decision['should_scale']:
            await self._apply_scaling(decision)
            
        return {
            'analysis': analysis,
            'decision': decision,
            'cost_impact': cost_impact,
            'applied_changes': decision.get('changes', [])
        }
        
    async def _analyze_scaling_needs(self, metrics: Dict) -> Dict:
        """Scaling ihtiyaçlarını analiz eder."""
        analysis = {
            'cpu_pressure': self._analyze_cpu_pressure(metrics),
            'memory_pressure': self._analyze_memory_pressure(metrics),
            'io_pressure': self._analyze_io_pressure(metrics),
            'network_pressure': self._analyze_network_pressure(metrics),
            'query_latency': self._analyze_query_latency(metrics)
        }
        
        # Trend analizi
        analysis['trends'] = await self._analyze_trends(metrics)
        
        # Resource utilization
        analysis['utilization'] = await self._analyze_utilization(metrics)
        
        return analysis
        
    def _make_scaling_decision(self, analysis: Dict,
                             cost_impact: Dict) -> Dict:
        """Scaling kararı verir."""
        decision = {
            'should_scale': False,
            'direction': None,
            'resources': [],
            'priority': 'low'
        }
        
        # CPU scaling
        if analysis['cpu_pressure']['level'] > 80:
            decision['should_scale'] = True
            decision['direction'] = 'up'
            decision['resources'].append({
                'type': 'cpu',
                'amount': self._calculate_cpu_increment(analysis)
            })
            decision['priority'] = 'high'
            
        # Memory scaling
        if analysis['memory_pressure']['level'] > 75:
            decision['should_scale'] = True
            decision['direction'] = 'up'
            decision['resources'].append({
                'type': 'memory',
                'amount': self._calculate_memory_increment(analysis)
            })
            
        return decision