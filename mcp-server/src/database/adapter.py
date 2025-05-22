from typing import Dict, Optional
from .sqlproxy_client import SQLProxyClient
from .models import DatabaseConfig

class DatabaseAdapter:
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.client = SQLProxyClient(config.sqlproxy)
        
    async def initialize(self) -> None:
        """Database sistemini initialize eder."""
        await self.client.connect()
        
        # Initialize database schema
        await self._init_schema()
        
        # Set up migrations
        await self._run_migrations()
        
    async def query(self, query: str,
                   params: Dict = None) -> Dict:
        """Query çalıştırır."""
        return await self.client.execute_query(
            query, params
        )
        
    async def transaction(self) -> 'DatabaseTransaction':
        """Transaction başlatır."""
        return DatabaseTransaction(self.client)
        
    async def _init_schema(self) -> None:
        """Database şemasını oluşturur."""
        schema_queries = [
            """
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(255) UNIQUE NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS sessions (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                token VARCHAR(255) NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        ]
        
        for query in schema_queries:
            await self.query(query)