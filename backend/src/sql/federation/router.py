from typing import Dict, List
from dataclasses import dataclass
import networkx as nx

@dataclass
class DataSource:
    name: str
    type: str  # postgresql, mysql, oracle, etc.
    capabilities: List[str]
    cost_factors: Dict[str, float]

class QueryRouter:
    def __init__(self):
        self.sources: Dict[str, DataSource] = {}
        self.routing_graph = nx.DiGraph()
        
    def add_source(self, source: DataSource):
        """Yeni data source ekler."""
        self.sources[source.name] = source
        self._update_routing_graph(source)
        
    def route_queries(self, queries: List[Dict]) -> List[Dict]:
        """Queryleri uygun data source'lara route eder."""
        routed = []
        
        for query in queries:
            best_source = self._find_best_source(query)
            if best_source:
                routed.append({
                    'query': query['query'],
                    'source': best_source,
                    'estimated_cost': self._estimate_cost(
                        query, best_source
                    )
                })
                
        return self._optimize_routing(routed)
        
    def _find_best_source(self, query: Dict) -> Optional[DataSource]:
        """Query için en uygun source'u bulur."""
        scores = {}
        
        for name, source in self.sources.items():
            # Capability check
            if not self._check_capabilities(query, source):
                continue
                
            # Calculate score
            scores[name] = self._calculate_source_score(
                query, source
            )
            
        if not scores:
            return None
            
        return self.sources[max(scores.items(), key=lambda x: x[1])[0]]
        
    def _optimize_routing(self, routed_queries: List[Dict]) -> List[Dict]:
        """Route edilmiş queryleri optimize eder."""
        # Build optimization graph
        g = nx.DiGraph()
        
        for i, query in enumerate(routed_queries):
            g.add_node(i, **query)
            
        # Add edges based on dependencies
        for i, query1 in enumerate(routed_queries):
            for j, query2 in enumerate(routed_queries):
                if i != j and self._has_dependency(query1, query2):
                    g.add_edge(i, j)
                    
        # Topological sort for execution order
        try:
            ordered = list(nx.topological_sort(g))
            return [routed_queries[i] for i in ordered]
        except nx.NetworkXUnfeasible:
            # Cycle detected, fall back to original order
            return routed_queries