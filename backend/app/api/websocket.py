"""
WebSocket API for SQL Proxy

This module provides WebSocket endpoints for real-time communication.

Last updated: 2025-05-21 07:11:02
Updated by: Teeksss
"""

import logging
import json
import asyncio
from typing import Dict, List, Any, Optional, Set
from fastapi import WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.websockets import WebSocketState
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user_ws
from app.models.user import User
from app.core.config import settings

logger = logging.getLogger(__name__)

# WebSocket connection manager
class ConnectionManager:
    """
    WebSocket connection manager
    
    Manages active WebSocket connections and message broadcasting.
    """
    
    def __init__(self):
        """Initialize connection manager"""
        self.active_connections: Dict[int, List[WebSocket]] = {}
        self.connection_channels: Dict[WebSocket, Set[str]] = {}
    
    async def connect(
        self,
        websocket: WebSocket,
        user_id: int,
        channels: Optional[List[str]] = None
    ):
        """
        Connect a new WebSocket client
        
        Args:
            websocket: WebSocket connection
            user_id: User ID
            channels: Optional channels to subscribe to
        """
        await websocket.accept()
        
        # Initialize user connections list if needed
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        
        # Add connection
        self.active_connections[user_id].append(websocket)
        
        # Initialize channels
        if channels:
            self.connection_channels[websocket] = set(channels)
        else:
            self.connection_channels[websocket] = set(["notifications"])
        
        logger.info(f"WebSocket client connected: user_id={user_id}, channels={channels}")
        
        # Send welcome message
        channel_list = list(self.connection_channels[websocket])
        await self.send_message(
            websocket,
            {
                "type": "connection_established",
                "user_id": user_id,
                "subscribed_channels": channel_list,
                "message": f"Connected to {len(channel_list)} channels: {', '.join(channel_list)}"
            }
        )
    
    def disconnect(self, websocket: WebSocket):
        """
        Disconnect a WebSocket client
        
        Args:
            websocket: WebSocket connection
        """
        # Find and remove connection
        for user_id, connections in self.active_connections.items():
            if websocket in connections:
                connections.remove(websocket)
                logger.info(f"WebSocket client disconnected: user_id={user_id}")
                
                # Clean up empty user connections
                if not connections:
                    del self.active_connections[user_id]
                break
        
        # Clean up channels
        if websocket in self.connection_channels:
            del self.connection_channels[websocket]
    
    async def subscribe(
        self,
        websocket: WebSocket,
        channels: List[str]
    ) -> List[str]:
        """
        Subscribe a connection to channels
        
        Args:
            websocket: WebSocket connection
            channels: Channels to subscribe to
            
        Returns:
            List of subscribed channels
        """
        if websocket not in self.connection_channels:
            self.connection_channels[websocket] = set()
        
        # Add channels
        for channel in channels:
            self.connection_channels[websocket].add(channel)
        
        # Return current subscriptions
        return list(self.connection_channels[websocket])
    
    async def unsubscribe(
        self,
        websocket: WebSocket,
        channels: List[str]
    ) -> List[str]:
        """
        Unsubscribe a connection from channels
        
        Args:
            websocket: WebSocket connection
            channels: Channels to unsubscribe from
            
        Returns:
            List of remaining subscribed channels
        """
        if websocket in self.connection_channels:
            # Remove channels
            for channel in channels:
                self.connection_channels[websocket].discard(channel)
        
        # Return current subscriptions
        return list(self.connection_channels.get(websocket, set()))
    
    async def send_message(self, websocket: WebSocket, message: Dict[str, Any]):
        """
        Send a message to a specific client
        
        Args:
            websocket: WebSocket connection
            message: Message to send
        """
        if websocket.client_state == WebSocketState.CONNECTED:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error sending WebSocket message: {e}", exc_info=True)
    
    async def broadcast(
        self,
        message: Dict[str, Any],
        channel: str = "notifications",
        exclude: Optional[WebSocket] = None
    ):
        """
        Broadcast a message to all clients subscribed to a channel
        
        Args:
            message: Message to broadcast
            channel: Channel to broadcast to
            exclude: Optional connection to exclude
        """
        # Add channel to message
        message["channel"] = channel
        
        # Find connections subscribed to the channel
        send_tasks = []
        for user_id, connections in self.active_connections.items():
            for connection in connections:
                if connection != exclude and connection in self.connection_channels:
                    if channel in self.connection_channels[connection]:
                        send_tasks.append(self.send_message(connection, message))
        
        # Send messages concurrently
        if send_tasks:
            await asyncio.gather(*send_tasks)
    
    async def broadcast_to_user(
        self,
        user_id: int,
        message: Dict[str, Any],
        channel: str = "notifications"
    ):
        """
        Broadcast a message to a specific user's connections
        
        Args:
            user_id: User ID
            message: Message to broadcast
            channel: Channel to broadcast to
        """
        # Add channel to message
        message["channel"] = channel
        
        # Find user's connections subscribed to the channel
        if user_id in self.active_connections:
            send_tasks = []
            for connection in self.active_connections[user_id]:
                if connection in self.connection_channels:
                    if channel in self.connection_channels[connection]:
                        send_tasks.append(self.send_message(connection, message))
            
            # Send messages concurrently
            if send_tasks:
                await asyncio.gather(*send_tasks)
    
    async def broadcast_system_message(
        self,
        message: str,
        message_type: str = "info"
    ):
        """
        Broadcast a system message to all clients
        
        Args:
            message: System message
            message_type: Message type (info, warning, error)
        """
        await self.broadcast({
            "type": "system",
            "message_type": message_type,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        }, channel="system")

# Initialize connection manager
manager = ConnectionManager()

# WebSocket endpoint
async def websocket_endpoint(
    websocket: WebSocket,
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint for real-time communication
    
    Args:
        websocket: WebSocket connection
        db: Database session
    """
    # Authenticate user
    try:
        user = await get_current_user_ws(websocket, db)
        
        # Get initial channels from query parameters
        channels_param = websocket.query_params.get("channels", "notifications")
        channels = [c.strip() for c in channels_param.split(",") if c.strip()]
        
        # Connect
        await manager.connect(websocket, user.id, channels)
        
        # Handle messages
        try:
            while True:
                # Wait for message
                data = await websocket.receive_text()
                
                try:
                    # Parse message
                    message = json.loads(data)
                    message_type = message.get("type")
                    
                    # Handle different message types
                    if message_type == "ping":
                        # Ping/pong for keepalive
                        await manager.send_message(websocket, {"type": "pong"})
                    
                    elif message_type == "subscribe":
                        # Subscribe to channels
                        channels = message.get("channels", [])
                        if not isinstance(channels, list):
                            channels = [channels]
                        
                        subscribed = await manager.subscribe(websocket, channels)
                        await manager.send_message(websocket, {
                            "type": "subscribed",
                            "channels": subscribed,
                            "message": f"Subscribed to channels: {', '.join(channels)}"
                        })
                    
                    elif message_type == "unsubscribe":
                        # Unsubscribe from channels
                        channels = message.get("channels", [])
                        if not isinstance(channels, list):
                            channels = [channels]
                        
                        subscribed = await manager.unsubscribe(websocket, channels)
                        await manager.send_message(websocket, {
                            "type": "unsubscribed",
                            "channels": subscribed,
                            "message": f"Unsubscribed from channels: {', '.join(channels)}"
                        })
                    
                    elif message_type == "query_execute":
                        # Execute SQL query
                        await handle_query_execute(websocket, message, user, db)
                    
                    else:
                        # Unknown message type
                        await manager.send_message(websocket, {
                            "type": "error",
                            "message": f"Unknown message type: {message_type}"
                        })
                
                except json.JSONDecodeError:
                    # Invalid JSON
                    await manager.send_message(websocket, {
                        "type": "error",
                        "message": "Invalid JSON message"
                    })
                
                except Exception as e:
                    # Other errors
                    logger.error(f"Error handling WebSocket message: {e}", exc_info=True)
                    await manager.send_message(websocket, {
                        "type": "error",
                        "message": f"Error processing message: {str(e)}"
                    })
        
        except WebSocketDisconnect:
            # Client disconnected
            manager.disconnect(websocket)
        
        except Exception as e:
            # Error handling messages
            logger.error(f"WebSocket error: {e}", exc_info=True)
            manager.disconnect(websocket)
    
    except HTTPException:
        # Authentication failed
        try:
            await websocket.accept()
            await websocket.send_json({
                "type": "error",
                "message": "Authentication failed"
            })
            await websocket.close()
        except:
            pass
    
    except Exception as e:
        # Other errors
        logger.error(f"WebSocket connection error: {e}", exc_info=True)
        try:
            await websocket.accept()
            await websocket.send_json({
                "type": "error",
                "message": "Internal server error"
            })
            await websocket.close()
        except:
            pass

async def handle_query_execute(
    websocket: WebSocket,
    message: Dict[str, Any],
    user: User,
    db: Session
):
    """
    Handle query execution WebSocket message
    
    Args:
        websocket: WebSocket connection
        message: Message data
        user: User
        db: Database session
    """
    from app.services.query_service import query_service
    
    # Get query parameters
    sql_text = message.get("sql")
    server_id = message.get("server_id")
    params = message.get("params")
    
    if not sql_text or not server_id:
        await manager.send_message(websocket, {
            "type": "error",
            "message": "Missing required parameters: sql, server_id"
        })
        return
    
    # Send query started message
    query_id = str(uuid.uuid4())
    await manager.send_message(websocket, {
        "type": "query_started",
        "query_id": query_id,
        "sql": sql_text,
        "server_id": server_id,
        "timestamp": datetime.utcnow().isoformat()
    })
    
    try:
        # Execute query
        result = await query_service.execute_query(
            server_id=server_id,
            sql_text=sql_text,
            params=params,
            user_id=user.id,
            db=db
        )
        
        # Send query result
        await manager.send_message(websocket, {
            "type": "query_result",
            "query_id": query_id,
            "success": result.get("success", False),
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    except Exception as e:
        # Send query error
        logger.error(f"Error executing query: {e}", exc_info=True)
        await manager.send_message(websocket, {
            "type": "query_error",
            "query_id": query_id,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        })

# Function to broadcast notification (used by notification service)
async def broadcast_notification(
    user_id: int,
    notification: Dict[str, Any]
):
    """
    Broadcast a notification to a user
    
    Args:
        user_id: User ID
        notification: Notification data
    """
    message = {
        "type": "notification",
        "notification": notification,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    await manager.broadcast_to_user(user_id, message, channel="notifications")

# Son güncelleme: 2025-05-21 07:11:02
# Güncelleyen: Teeksss