from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool
from typing import Dict, Any
import json
import os

class DatabaseManager:
    def __init__(self):
        self.connections: Dict[str, Any] = {}
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        config_path = os.getenv('DB_CONFIG_PATH', 'config/databases.json')
        with open(config_path, 'r') as f:
            return json.load(f)
    
    def get_connection(self, database: str):
        if database not in self.connections:
            if database not in self.config:
                raise ValueError(f"Database {database} not configured")
                
            db_config = self.config[database]
            engine = create_engine(
                self._build_connection_string(db_config),
                poolclass=QueuePool,
                pool_size=5,
                max_overflow=10,
                pool_timeout=30
            )
            self.connections[database] = engine
            
        return self.connections[database]
    
    def _build_connection_string(self, config: Dict[str, str]) -> str:
        return f"postgresql://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}"