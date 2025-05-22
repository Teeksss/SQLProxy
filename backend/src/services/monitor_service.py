from datetime import datetime
from typing import Dict, Any
import time
import logging
from elasticsearch import Elasticsearch

class MonitorService:
    def __init__(self):
        self.es = Elasticsearch(['http://localhost:9200'])
        self.setup_logging()
        
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('sqlproxy')
        
    def log_query(self, 
                  database: str,
                  query: str,
                  user_id: int,
                  execution_time: float,
                  status: str,
                  error: str = None):
        doc = {
            'timestamp': datetime.utcnow(),
            'database': database,
            'query': query,
            'user_id': user_id,
            'execution_time': execution_time,
            'status': status,
            'error': error
        }
        
        # Log to Elasticsearch
        self.es.index(index='sqlproxy-queries', body=doc)
        
        # Log to file
        self.logger.info(f"Query executed: {database} - {execution_time}s - {status}")