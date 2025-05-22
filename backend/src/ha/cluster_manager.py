from typing import Dict, List
import etcd3
from datetime import datetime
import asyncio
from .health_checker import HealthChecker
from .load_balancer import LoadBalancer

class ClusterManager:
    def __init__(self, config: Dict):
        self.config = config
        self.etcd = etcd3.client()
        self.health_checker = HealthChecker()
        self.load_balancer = LoadBalancer()
        self.node_id = config['node_id']
        
    async def start(self):
        """Cluster yönetimini başlatır."""
        await self._register_node()
        await self._start_health_checks()
        await self._start_leader_election()
        
    async def _register_node(self):
        """Node'u cluster'a kaydeder."""
        node_info = {
            'id': self.node_id,
            'host': self.config['host'],
            'port': self.config['port'],
            'status': 'active',
            'capabilities': self.config['capabilities'],
            'last_heartbeat': datetime.utcnow().isoformat()
        }
        
        # etcd'ye kaydet
        self.etcd.put(
            f'/nodes/{self.node_id}',
            str(node_info)
        )
        
    async def _start_leader_election(self):
        """Leader election başlatır."""
        while True:
            try:
                # Lock al
                lock = self.etcd.lock('leader_lock')
                if lock.acquire():
                    await self._become_leader()
                else:
                    await self._become_follower()
                    
            except Exception as e:
                self.logger.error(f"Leader election error: {str(e)}")
                
            await asyncio.sleep(5)
            
    async def _become_leader(self):
        """Leader rolünü üstlenir."""
        self.is_leader = True
        
        # Cluster state'i yönet
        await self._manage_cluster_state()
        
        # Load balancing
        await self._manage_load_balancing()
        
    async def _manage_cluster_state(self):
        """Cluster durumunu yönetir."""
        while self.is_leader:
            try:
                # Node health kontrolü
                nodes = self._get_all_nodes()
                for node in nodes:
                    if not await self.health_checker.check_node(node):
                        await self._handle_node_failure(node)
                        
                # Rebalancing ihtiyacı kontrolü
                if self.load_balancer.needs_rebalancing(nodes):
                    await self._rebalance_cluster()
                    
                # Metrics toplama
                await self._collect_cluster_metrics()
                
            except Exception as e:
                self.logger.error(f"Cluster management error: {str(e)}")
                
            await asyncio.sleep(10)