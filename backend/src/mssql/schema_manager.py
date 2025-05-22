from typing import Dict, List
import pandas as pd

class MSSQLSchemaManager:
    def __init__(self, connection_manager):
        self.conn_manager = connection_manager
        
    def get_schema_info(self, database: str) -> Dict:
        """Schema bilgilerini getirir."""
        with self.conn_manager.get_connection(database) as conn:
            return {
                'tables': self._get_tables(conn),
                'views': self._get_views(conn),
                'stored_procs': self._get_stored_procedures(conn),
                'functions': self._get_functions(conn),
                'indexes': self._get_indexes(conn),
                'constraints': self._get_constraints(conn)
            }
            
    def _get_tables(self, conn) -> List[Dict]:
        """Tablo bilgilerini getirir."""
        query = """
        SELECT 
            t.name AS table_name,
            p.rows AS row_count,
            SUM(a.total_pages) * 8 AS size_kb,
            SCHEMA_NAME(t.schema_id) AS schema_name
        FROM sys.tables t
        INNER JOIN sys.indexes i ON t.object_id = i.object_id
        INNER JOIN sys.partitions p ON i.object_id = p.object_id AND i.index_id = p.index_id
        INNER JOIN sys.allocation_units a ON p.partition_id = a.container_id
        GROUP BY t.name, p.rows, t.schema_id
        """
        
        return pd.read_sql(query, conn).to_dict('records')
        
    def _get_indexes(self, conn) -> List[Dict]:
        """Index bilgilerini getirir."""
        query = """
        SELECT 
            i.name AS index_name,
            t.name AS table_name,
            i.type_desc AS index_type,
            i.fill_factor,
            p.rows AS row_count,
            s.user_seeks,
            s.user_scans,
            s.user_lookups,
            s.user_updates
        FROM sys.indexes i
        INNER JOIN sys.tables t ON i.object_id = t.object_id
        INNER JOIN sys.partitions p ON i.object_id = p.object_id AND i.index_id = p.index_id
        LEFT JOIN sys.dm_db_index_usage_stats s ON i.object_id = s.object_id AND i.index_id = s.index_id
        """
        
        return pd.read_sql(query, conn).to_dict('records')