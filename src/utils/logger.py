import logging
from elasticsearch import Elasticsearch
from datetime import datetime

class QueryLogger:
    def __init__(self):
        self.es = Elasticsearch(['http://localhost:9200'])
        self.setup_logging()
        
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
    def log_query(self, query: str, execution_time: float, status: str):
        doc = {
            'timestamp': datetime.utcnow(),
            'query': query,
            'execution_time': execution_time,
            'status': status
        }
        self.es.index(index='sql-proxy-logs', body=doc)