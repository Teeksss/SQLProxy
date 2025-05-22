import asyncio
from typing import Dict, Set
from datetime import datetime
import socketio
import json

sio = socketio.AsyncServer(async_mode='asgi')

class QueryMonitor:
    def __init__(self):
        self.active_queries: Dict[str, Dict] = {}
        self.subscribers: Set[str] = set()
        
    async def start_query(self, query_id: str, query: str, database: str):
        self.active_queries[query_id] = {
            'query': query,
            'database': database,
            'start_time': datetime.utcnow(),
            'status': 'running'
        }
        await self._notify_subscribers()
        
    async def end_query(self, query_id: str, status: str, result: Dict = None):
        if query_id in self.active_queries:
            self.active_queries[query_id].update({
                'end_time': datetime.utcnow(),
                'status': status,
                'result': result
            })
            await self._notify_subscribers()
            
    async def subscribe(self, client_id: str):
        self.subscribers.add(client_id)
        # Send current state
        await sio.emit('query_state', self.active_queries, room=client_id)
        
    async def unsubscribe(self, client_id: str):
        self.subscribers.remove(client_id)
        
    async def _notify_subscribers(self):
        for client_id in self.subscribers:
            await sio.emit('query_state', self.active_queries, room=client_id)