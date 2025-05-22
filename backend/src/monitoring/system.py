from typing import Dict, List
import psutil
import asyncio
from datetime import datetime
from .models import (
    SystemMetrics,
    QueryMetrics,
    ResourceUsage,
    Alert
)
from .collectors import MetricsCollector
from .alerting import AlertManager

class MonitoringSystem:
    def __init__(self):
        self.collector = MetricsCollector()
        self.alert_manager = AlertManager()
        self.metrics_history: List[SystemMetrics] = []
        self.alert_history: List[Alert] = []
        
    async def collect_metrics(self) -> SystemMetrics:
        """Sistem metriklerini toplar."""
        metrics = SystemMetrics(
            timestamp=datetime.utcnow(),
            cpu_usage=await self._get_cpu_usage(),
            memory_usage=await self._get_memory_usage(),
            disk_usage=await self._get_disk_usage(),
            network_stats=await self._get_network_stats(),
            query_metrics=await self._get_query_metrics()
        )
        
        # Store metrics
        self.metrics_history.append(metrics)
        
        # Check alerts
        await self._check_alerts(metrics)
        
        return metrics
        
    async def _get_cpu_usage(self) -> Dict:
        """CPU kullanımını alır."""
        return {
            'total': psutil.cpu_percent(interval=1),
            'per_cpu': psutil.cpu_percent(interval=1, percpu=True),
            'load_avg': psutil.getloadavg()
        }
        
    async def _get_memory_usage(self) -> Dict:
        """Memory kullanımını alır."""
        mem = psutil.virtual_memory()
        return {
            'total': mem.total,
            'available': mem.available,
            'used': mem.used,
            'percent': mem.percent
        }
        
    async def _get_query_metrics(self) -> QueryMetrics:
        """Query metriklerini alır."""
        return await self.collector.get_query_metrics()
        
    async def _check_alerts(self, metrics: SystemMetrics) -> None:
        """Alert kontrolü yapar."""
        # CPU alert
        if metrics.cpu_usage['total'] > 80:
            await self.alert_manager.create_alert(
                level='warning',
                message='High CPU usage detected',
                metrics=metrics.cpu_usage
            )
            
        # Memory alert
        if metrics.memory_usage['percent'] > 90:
            await self.alert_manager.create_alert(
                level='critical',
                message='Memory usage critical',
                metrics=metrics.memory_usage
            )
            
class QueryMonitor:
    def __init__(self):
        self.current_queries: Dict[str, Dict] = {}
        self.slow_query_threshold = 5  # seconds
        
    async def start_query(self, query_id: str,
                         query: str) -> None:
        """Query monitoring başlatır."""
        self.current_queries[query_id] = {
            'query': query,
            'start_time': datetime.utcnow(),
            'status': 'running'
        }
        
    async def end_query(self, query_id: str,
                       result: Dict) -> None:
        """Query monitoring bitirir."""
        if query_id not in self.current_queries:
            return
            
        query_info = self.current_queries[query_id]
        duration = (
            datetime.utcnow() - query_info['start_time']
        ).total_seconds()
        
        # Check for slow query
        if duration > self.slow_query_threshold:
            await self._handle_slow_query(
                query_id, query_info, duration
            )
            
        # Update query info
        query_info.update({
            'end_time': datetime.utcnow(),
            'duration': duration,
            'status': 'completed',
            'result': result
        })
        
    async def _handle_slow_query(self, query_id: str,
                               query_info: Dict,
                               duration: float) -> None:
        """Yavaş query'leri handle eder."""
        await self.alert_manager.create_alert(
            level='warning',
            message='Slow query detected',
            details={
                'query_id': query_id,
                'query': query_info['query'],
                'duration': duration
            }
        )