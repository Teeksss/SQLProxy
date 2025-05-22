from typing import Dict, List
from datetime import datetime, timedelta
import pandas as pd

class MSSQLPerformanceMonitor:
    def __init__(self, connection_manager):
        self.conn_manager = connection_manager
        
    def get_performance_metrics(self, database: str) -> Dict:
        """Performance metrikleri toplar."""
        with self.conn_manager.get_connection(database) as conn:
            return {
                'wait_stats': self._get_wait_statistics(conn),
                'memory_usage': self._get_memory_usage(conn),
                'cpu_usage': self._get_cpu_usage(conn),
                'io_stats': self._get_io_statistics(conn),
                'index_usage': self._get_index_usage_stats(conn),
                'blocking': self._get_blocking_info(conn)
            }
            
    def _get_wait_statistics(self, conn) -> List[Dict]:
        """Wait istatistiklerini getirir."""
        query = """
        SELECT 
            wait_type,
            waiting_tasks_count,
            wait_time_ms,
            max_wait_time_ms,
            signal_wait_time_ms
        FROM sys.dm_os_wait_stats
        WHERE wait_time_ms > 0
        ORDER BY wait_time_ms DESC
        """
        
        df = pd.read_sql(query, conn)
        return df.to_dict('records')
        
    def _get_memory_usage(self, conn) -> Dict:
        """Memory kullanım istatistiklerini getirir."""
        query = """
        SELECT
            physical_memory_kb,
            virtual_memory_kb,
            committed_kb,
            committed_target_kb
        FROM sys.dm_os_process_memory
        """
        
        df = pd.read_sql(query, conn)
        memory_info = df.iloc[0].to_dict()
        
        # Buffer pool analizi
        buffer_query = """
        SELECT
            COUNT_BIG(*) * 8 / 1024.0 AS cached_size_mb,
            COUNT_BIG(CASE WHEN is_modified = 1 THEN 1 END) * 8 / 1024.0 AS dirty_size_mb
        FROM sys.dm_os_buffer_descriptors
        """
        
        buffer_df = pd.read_sql(buffer_query, conn)
        memory_info.update(buffer_df.iloc[0].to_dict())
        
        return memory_info