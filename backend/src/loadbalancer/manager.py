from typing import Dict, List
import asyncio
from datetime import datetime
from .models import ServerNode, BalancingStrategy
from ..monitoring import ServerMonitor

class LoadBalancer:
    def __init__(self):
        self.nodes: List[ServerNode] = []
        self.monitor = ServerMonitor()
        self.strategy = BalancingStrategy.LEAST_CONNECTIONS
        
    async def add_node(self, node: ServerNode) -> None:
        """Yeni node ekler."""
        await self._test_node(node)
        self.nodes.append(node)
        
    async def get_node(self, context: Dict) -> ServerNode:
        """Request için uygun node seçer."""
        available_nodes = [
            node for node in self.nodes
            if await self._is_node_available(node)
        ]
        
        if not available_nodes:
            raise NoAvailableNodesError()
            
        if self.strategy == BalancingStrategy.ROUND_ROBIN:
            return self._round_robin_select(available_nodes)
            
        elif self.strategy == BalancingStrategy.LEAST_CONNECTIONS:
            return await self._least_connections_select(
                available_nodes
            )
            
        elif self.strategy == BalancingStrategy.RESPONSE_TIME:
            return await self._response_time_select(
                available_nodes
            )
            
    async def _is_node_available(self, node: ServerNode) -> bool:
        """Node durumunu kontrol eder."""
        stats = await self.monitor.get_node_stats(node)
        
        return (
            stats['status'] == 'healthy' and
            stats['current_connections'] < node.max_connections and
            stats['cpu_usage'] < 80
        )
        
    async def _least_connections_select(self,
                                     nodes: List[ServerNode]) -> ServerNode:
        """En az bağlantılı node'u seçer."""
        min_connections = float('inf')
        selected_node = None
        
        for node in nodes:
            stats = await self.monitor.get_node_stats(node)
            connections = stats['current_connections']
            
            if connections < min_connections:
                min_connections = connections
                selected_node = node
                
        return selected_node
        
    async def _response_time_select(self,
                                 nodes: List[ServerNode]) -> ServerNode:
        """En hızlı response veren node'u seçer."""
        response_times = []
        
        for node in nodes:
            start_time = datetime.utcnow()
            await self._test_node(node)
            end_time = datetime.utcnow()
            
            response_times.append({
                'node': node,
                'time': (end_time - start_time).total_seconds()
            })
            
        fastest = min(response_times, key=lambda x: x['time'])
        return fastest['node']