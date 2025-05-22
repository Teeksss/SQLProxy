from typing import Dict, List, Optional
import random
from datetime import datetime
from db.models import DatabaseNode

class LoadBalancer:
    def __init__(self):
        self.nodes: Dict[str, List[DatabaseNode]] = {}
        self.health_checks = {}
        
    def register_node(self, database: str, node: DatabaseNode):
        if database not in self.nodes:
            self.nodes[database] = []
        self.nodes[database].append(node)
        
    def get_node(self, database: str) -> Optional[DatabaseNode]:
        if database not in self.nodes:
            return None
            
        # Filter healthy nodes
        healthy_nodes = [
            node for node in self.nodes[database]
            if self._is_healthy(node)
        ]
        
        if not healthy_nodes:
            return None
            
        # Load balancing strategies
        return self._least_connections(healthy_nodes)
        
    def _is_healthy(self, node: DatabaseNode) -> bool:
        last_check = self.health_checks.get(node.id)
        if not last_check or (datetime.now() - last_check).seconds > 30:
            healthy = node.check_health()
            self.health_checks[node.id] = datetime.now()
            return healthy
        return True
        
    def _least_connections(self, nodes: List[DatabaseNode]) -> DatabaseNode:
        return min(nodes, key=lambda x: x.active_connections)