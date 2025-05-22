from typing import Dict, List
from datetime import datetime
import asyncio
from .models import QuerySession, SessionState
from .connection_manager import SQLServerManager

class QuerySessionManager:
    def __init__(self, conn_manager: SQLServerManager):
        self.conn_manager = conn_manager
        self.active_sessions = {}  # session_id -> session
        
    async def create_session(self, user_id: str,
                           server_id: str,
                           database: str) -> QuerySession:
        """Yeni query session oluşturur."""
        session = QuerySession(
            id=self._generate_session_id(),
            user_id=user_id,
            server_id=server_id,
            database=database,
            created_at=datetime.utcnow(),
            state=SessionState.ACTIVE
        )
        
        self.active_sessions[session.id] = session
        
        return session
        
    async def execute_query(self, session_id: str,
                          query: str) -> Dict:
        """Session içinde query çalıştırır."""
        session = self.active_sessions.get(session_id)
        if not session:
            raise ValueError(f"Invalid session: {session_id}")
            
        try:
            async with self.conn_manager.get_connection(
                session.server_id,
                session.database
            ) as conn:
                # Execute query
                cursor = conn.cursor()
                start_time = datetime.utcnow()
                cursor.execute(query)
                
                # Get results
                columns = [col[0] for col in cursor.description]
                rows = cursor.fetchall()
                
                end_time = datetime.utcnow()
                
                # Update session stats
                session.last_query = query
                session.last_query_time = end_time
                session.query_count += 1
                
                return {
                    'status': 'success',
                    'columns': columns,
                    'rows': rows,
                    'execution_time': (end_time - start_time).total_seconds(),
                    'affected_rows': cursor.rowcount
                }
                
        except Exception as e:
            # Log error
            session.errors.append({
                'query': query,
                'error': str(e),
                'timestamp': datetime.utcnow()
            })
            
            raise
            
    async def close_session(self, session_id: str) -> Dict:
        """Session'ı kapatır."""
        session = self.active_sessions.get(session_id)
        if not session:
            raise ValueError(f"Invalid session: {session_id}")
            
        try:
            # Update session state
            session.state = SessionState.CLOSED
            session.closed_at = datetime.utcnow()
            
            # Remove from active sessions
            del self.active_sessions[session_id]
            
            # Save session history
            await self._save_session_history(session)
            
            return {
                'status': 'success',
                'session_id': session_id,
                'duration': (session.closed_at - session.created_at).total_seconds(),
                'query_count': session.query_count
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }