"""Health check module for SQLProxy"""
import time
import logging
from typing import Dict, Any, List, Optional

from sqlproxy.core.database.integration import DatabaseIntegration
from sqlproxy.core.redis.connection import RedisConnection

logger = logging.getLogger(__name__)

class HealthCheck:
    """Health check service for SQLProxy"""
    
    def __init__(
        self,
        db_integration: Optional[DatabaseIntegration] = None,
        redis_connection: Optional[RedisConnection] = None
    ):
        self.db = db_integration
        self.redis = redis_connection
        self.components = []
        
        if self.db:
            self.components.append({
                'name': 'database',
                'check': self._check_database
            })
        
        if self.redis:
            self.components.append({
                'name': 'redis',
                'check': self._check_redis
            })
        
        # Always add system checks
        self.components.append({
            'name': 'system',
            'check': self._check_system
        })
    
    def check_health(self) -> Dict[str, Any]:
        """Run all health checks and return results"""
        results = {
            'status': 'healthy',
            'timestamp': time.time(),
            'components': {}
        }
        
        for component in self.components:
            name = component['name']
            check_func = component['check']
            
            try:
                component_result = check_func()
                results['components'][name] = component_result
                
                if component_result['status'] != 'healthy':
                    results['status'] = 'degraded'
            except Exception as e:
                logger.error(f"Health check failed for {name}: {str(e)}")
                results['components'][name] = {
                    'status': 'unhealthy',
                    'error': str(e)
                }
                results['status'] = 'unhealthy'
        
        return results
    
    def _check_database(self) -> Dict[str, Any]:
        """Check database connection"""
        start_time = time.time()
        try:
            self.db.test_connection()
            return {
                'status': 'healthy',
                'latency_ms': int((time.time() - start_time) * 1000)
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'latency_ms': int((time.time() - start_time) * 1000)
            }
    
    def _check_redis(self) -> Dict[str, Any]:
        """Check Redis connection"""
        start_time = time.time()
        try:
            ping_result = self.redis.test_connection()
            return {
                'status': 'healthy' if ping_result else 'degraded',
                'latency_ms': int((time.time() - start_time) * 1000)
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'latency_ms': int((time.time() - start_time) * 1000)
            }
    
    def _check_system(self) -> Dict[str, Any]:
        """Check system resources"""
        import psutil
        
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        status = 'healthy'
        
        # Check memory
        if memory.percent > 90:
            status = 'degraded'
        
        # Check disk
        if disk.percent > 90:
            status = 'degraded'
        
        return {
            'status': status,
            'memory': {
                'total_mb': memory.total / (1024 * 1024),
                'used_percent': memory.percent
            },
            'disk': {
                'total_gb': disk.total / (1024 * 1024 * 1024),
                'used_percent': disk.percent
            },
            'cpu_percent': psutil.cpu_percent(interval=0.1)
        }