from typing import Dict, Optional
import aiohttp
import asyncio
from datetime import datetime
from .models import SQLProxyConfig

class SQLProxyClient:
    def __init__(self, config: SQLProxyConfig):
        self.config = config
        self.session = None
        self.base_url = f"http://{config.host}:{config.port}"
        
    async def connect(self) -> None:
        """SQLProxy'ye bağlanır."""
        if not self.session:
            self.session = aiohttp.ClientSession()
            
        try:
            async with self.session.get(
                f"{self.base_url}/health"
            ) as response:
                if response.status != 200:
                    raise ConnectionError(
                        "SQLProxy service is not available"
                    )
                    
        except Exception as e:
            raise ConnectionError(f"Connection failed: {str(e)}")
            
    async def execute_query(self, query: str,
                          params: Dict = None) -> Dict:
        """Query çalıştırır."""
        if not self.session:
            await self.connect()
            
        try:
            async with self.session.post(
                f"{self.base_url}/query/execute",
                json={
                    'query': query,
                    'params': params or {},
                    'context': {
                        'source': 'mcp_server',
                        'timestamp': datetime.utcnow().isoformat()
                    }
                }
            ) as response:
                return await response.json()
                
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
            
    async def get_analytics(self, timeframe: str = '24h') -> Dict:
        """Analytics verilerini alır."""
        if not self.session:
            await self.connect()
            
        try:
            async with self.session.get(
                f"{self.base_url}/analytics",
                params={'timeframe': timeframe}
            ) as response:
                return await response.json()
                
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }