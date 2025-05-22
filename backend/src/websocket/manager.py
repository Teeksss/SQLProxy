import asyncio
from typing import Dict, Set
from fastapi import WebSocket
from .models import WSMessage, WSConnection

class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WSConnection]] = {}
        self.lock = asyncio.Lock()
        
    async def connect(self, websocket: WebSocket,
                     client_id: str) -> None:
        """Client bağlantısını kabul eder."""
        await websocket.accept()
        connection = WSConnection(
            socket=websocket,
            client_id=client_id
        )
        
        async with self.lock:
            if client_id not in self.active_connections:
                self.active_connections[client_id] = set()
            self.active_connections[client_id].add(connection)
            
    async def disconnect(self, websocket: WebSocket,
                        client_id: str) -> None:
        """Client bağlantısını kapatır."""
        async with self.lock:
            if client_id in self.active_connections:
                connections = self.active_connections[client_id]
                connections.discard(
                    next(
                        (conn for conn in connections 
                         if conn.socket == websocket),
                        None
                    )
                )
                
                if not connections:
                    del self.active_connections[client_id]
                    
    async def broadcast(self, message: WSMessage,
                       client_id: str = None) -> None:
        """Mesaj broadcast eder."""
        if client_id:
            # Specific client
            if client_id in self.active_connections:
                for connection in self.active_connections[client_id]:
                    await connection.socket.send_json(message.dict())
        else:
            # All clients
            for connections in self.active_connections.values():
                for connection in connections:
                    await connection.socket.send_json(message.dict())