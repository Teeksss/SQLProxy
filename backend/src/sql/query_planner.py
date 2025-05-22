from typing import Dict, List, Optional
import numpy as np
from dataclasses import dataclass
from .parser import SQLParser

@dataclass
class QueryCost:
    cpu_cost: float
    io_cost: float
    memory_cost: float
    network_cost: float
    
    @property
    def total_cost(self) -> float:
        return (self.cpu_cost + self.io_cost + 
                self.memory_cost + self.network_cost)

class QueryPlanner:
    def __init__(self):
        self.parser = SQLParser()
        self.stats_manager = TableStatisticsManager()
        
    def create_plan(self, query: str) -> Dict:
        """Detaylı query execution planı oluşturur."""
        parsed = self.parser.parse_query(query)
        
        # Farklı plan alternatifleri oluştur
        plan_candidates = self._generate_plan_candidates(parsed)
        
        # En iyi planı seç
        best_plan = self._select_best_plan(plan_candidates)
        
        # Resource allocation
        resources = self._allocate_resources(best_plan)
        
        return {
            'execution_plan': best_plan,
            'cost_analysis': self._analyze_cost(best_plan),
            'resource_allocation': resources,
            'parallelization': self._plan_parallelization(best_plan)
        }
        
    def _generate_plan_candidates(self, parsed_query: Dict) -> List[Dict]:
        """Alternatif execution planları oluşturur."""
        candidates = []
        
        # Base plan
        base_plan = self._create_base_plan(parsed_query)
        candidates.append(base_plan)
        
        # Join order variations
        if parsed_query['joins']:
            join_variations = self._generate_join_orders(parsed_query)
            candidates.extend(join_variations)
            
        # Index kullanım variations
        index_variations = self._generate_index_plans(parsed_query)
        candidates.extend(index_variations)
        
        # Parallelization variations
        parallel_variations = self._generate_parallel_plans(base_plan)
        candidates.extend(parallel_variations)
        
        return candidates
        
    def _select_best_plan(self, candidates: List[Dict]) -> Dict:
        """Cost-based plan seçimi yapar."""
        best_plan = None
        min_cost = float('inf')
        
        for plan in candidates:
            cost = self._calculate_plan_cost(plan)
            
            # Resource constraints kontrolü
            if not self._check_resource_constraints(plan):
                continue
                
            if cost.total_cost < min_cost:
                min_cost = cost.total_cost
                best_plan = plan
                
        return best_plan
        
    def _plan_parallelization(self, plan: Dict) -> Dict:
        """Query'nin parallel execution planını oluşturur."""
        parallel_config = {
            'can_parallelize': False,
            'max_parallel_workers': 1,
            'parallel_tasks': []
        }
        
        # Parallelization uygunluk kontrolü
        if self._can_parallelize(plan):
            parallel_config['can_parallelize'] = True
            parallel_config['max_parallel_workers'] = self._calculate_optimal_workers(plan)
            parallel_config['parallel_tasks'] = self._split_into_parallel_tasks(plan)
            
        return parallel_config
        
    def _allocate_resources(self, plan: Dict) -> Dict:
        """Query için resource allocation yapar."""
        cost = self._calculate_plan_cost(plan)
        
        return {
            'memory': {
                'min_required': self._calculate_min_memory(plan),
                'optimal': self._calculate_optimal_memory(plan, cost),
                'max_allowed': self._get_max_memory_limit()
            },
            'cpu': {
                'min_threads': self._calculate_min_threads(plan),
                'optimal_threads': self._calculate_optimal_threads(plan, cost),
                'max_threads': self._get_max_threads()
            },
            'io': {
                'estimated_reads': self._estimate_io_reads(plan),
                'estimated_writes': self._estimate_io_writes(plan)
            }
        }