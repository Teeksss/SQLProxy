import asyncio
import logging
import socket
import struct
from threading import Thread
from typing import Dict, Optional, Tuple, List
import time
import re
import hashlib

import jwt
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.core.config import settings
from app.models.query import AuditLog, QueryWhitelist, ServerConfig
from app.query.validator import QueryValidator
from app.query.parser import SQLAnalyzer
from app.proxy.sql_proxy import SQLProxy
from app.services.rate_limiter import RateLimiter
from app.core.redis import get_redis_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize dependencies
sql_analyzer = SQLAnalyzer()
query_validator = QueryValidator(sql_analyzer)
sql_proxy = SQLProxy()
redis_client = get_redis_client()
rate_limiter = RateLimiter(redis_client)

class SQLProxyServer:
    def __init__(self, host: str = '0.0.0.0', port: int = 1433):
        self.host = host
        self.port = port
        self.server_socket = None
        self.clients = {}  # client_id -> connection
        
    async def start(self):
        """Start the SQL proxy server."""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(100)
        self.server_socket.setblocking(False)
        
        logger.info(f"SQL Proxy Server started on {self.host}:{self.port}")
        
        loop = asyncio.get_event_loop()
        
        while True:
            client_socket, address = await loop.sock_accept(self.server_socket)
            logger.info(f"New connection from {address}")
            
            # Create a new task for each client
            loop.create_task(self.handle_client(client_socket, address))
    
    async def handle_client(self, client_socket: socket.socket, address: Tuple[str, int]):
        """Handle a client connection."""
        client_id = f"{address[0]}:{address[1]}"
        self.clients[client_id] = client_socket
        
        # Get DB session
        db = SessionLocal()
        
        try:
            # First message should be authentication
            auth_message = await self.receive_message(client_socket)
            auth_data = self.parse_auth_message(auth_message)
            
            if not auth_data:
                await self.send_error(client_socket, "Invalid authentication message")
                return
            
            # Validate JWT token
            user_data = self.validate_token(auth_data.get('token', ''))
            
            if not user_data:
                await self.send_error(client_socket, "Invalid or expired token")
                return
            
            # Acknowledge successful authentication
            await self.send_message(client_socket, {
                "status": "authenticated",
                "username": user_data['username'],
                "role": user_data['role']
            })
            
            # Main communication loop
            while True:
                message = await self.receive_message(client_socket)
                
                if not message:
                    logger.info(f"Client {client_id} disconnected")
                    break
                
                # Process the client message
                response = await self.process_message(
                    message, 
                    user_data, 
                    client_id, 
                    address[0],
                    db
                )
                
                # Send response back to client
                await self.send_message(client_socket, response)
        
        except Exception as e:
            logger.error(f"Error handling client {client_id}: {str(e)}")
        
        finally:
            # Cleanup
            if client_id in self.clients:
                del self.clients[client_id]
            
            client_socket.close()
            db.close()
    
    def parse_auth_message(self, message: bytes) -> Optional[Dict]:
        """Parse authentication message from client."""
        try:
            # Authentication message format: JWT token
            message_str = message.decode('utf-8')
            
            # Simple JSON format: {"token": "jwt_token_here"}
            if message_str.startswith('{') and message_str.endswith('}'):
                import json
                data = json.loads(message_str)
                return data
            
            # Simple token format: "Bearer jwt_token_here"
            elif message_str.startswith('Bearer '):
                token = message_str[7:]  # Remove "Bearer " prefix
                return {"token": token}
            
            return None
        
        except Exception as e:
            logger.error(f"Error parsing auth message: {str(e)}")
            return None
    
    def validate_token(self, token: str) -> Optional[Dict]:
        """Validate JWT token and extract user data."""
        try:
            payload = jwt.decode(
                token, 
                settings.SECRET_KEY, 
                algorithms=[settings.ALGORITHM]
            )
            
            if 'sub' not in payload:
                return None
            
            return {
                'username': payload['sub'],
                'role': payload.get('role', 'readonly'),
                'email': payload.get('email')
            }
        
        except jwt.PyJWTError as e:
            logger.error(f"JWT validation error: {str(e)}")
            return None
    
    async def process_message(
        self, 
        message: bytes, 
        user_data: Dict, 
        client_id: str,
        client_ip: str,
        db: Session
    ) -> Dict:
        """Process client message and execute query."""
        try:
            # Parse message as JSON
            import json
            data = json.loads(message.decode('utf-8'))
            
            # Extract query and server
            sql_query = data.get('query')
            target_server = data.get('server')
            
            if not sql_query or not target_server:
                return {
                    "status": "error",
                    "message": "Missing query or server in request"
                }
            
            # Check rate limit
            is_allowed, limit_info = rate_limiter.check_rate_limit(
                identifier=user_data['username'],
                role=user_data['role']
            )
            
            if not is_allowed:
                # Create audit log for rate limit rejection
                audit_log = AuditLog(
                    username=user_data['username'],
                    user_role=user_data['role'],
                    client_ip=client_ip,
                    query_text=sql_query,
                    query_hash=query_validator.hash_query(sql_query),
                    target_server=target_server,
                    execution_status='rejected',
                    error_message='Rate limit exceeded'
                )
                
                db.add(audit_log)
                db.commit()
                
                return {
                    "status": "error",
                    "message": "Rate limit exceeded",
                    "rate_limit": limit_info
                }
            
            # Get server config
            server = db.query(ServerConfig).filter(
                ServerConfig.server_alias == target_server,
                ServerConfig.is_active == True
            ).first()
            
            if not server:
                return {
                    "status": "error",
                    "message": f"Server {target_server} not found or is inactive"
                }
            
            # Check if user role is allowed for this server
            if user_data['role'] not in server.allowed_roles:
                return {
                    "status": "error",
                    "message": f"Your role ({user_data['role']}) does not have