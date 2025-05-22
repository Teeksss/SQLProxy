from typing import Dict, List
from datetime import datetime
from .models import UserQueryProfile, QueryHistory
from .session_manager import QuerySessionManager

class UserQueryManager:
    def __init__(self, session_manager: QuerySessionManager):
        self.session_manager = session_manager
        self.user_profiles = {}  # user_id -> profile
        
    async def get_user_profile(self, user_id: str) -> UserQueryProfile:
        """Kullanıcı query profilini getirir."""
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = await self._create_profile(user_id)
            
        return self.user_profiles[user_id]
        
    async def track_query(self, user_id: str,
                         session_id: str,
                         query: str,
                         result: Dict) -> None:
        """Query'yi kullanıcı history'sine ekler."""
        profile = await self.get_user_profile(user_id)
        
        # Add to history
        history_entry = QueryHistory(
            query=query,
            session_id=session_id,
            execution_time=result['execution_time'],
            affected_rows=result['affected_rows'],
            timestamp=datetime.utcnow()
        )
        
        profile.query_history.append(history_entry)
        
        # Update statistics
        profile.total_queries += 1
        profile.total_execution_time += result['execution_time']
        
        # Update last activity
        profile.last_activity = datetime.utcnow()
        
    async def get_user_statistics(self, user_id: str,
                                timeframe: str = '24h') -> Dict:
        """Kullanıcı istatistiklerini getirir."""
        profile = await self.get_user_profile(user_id)
        
        return {
            'query_count': profile.total_queries,
            'avg_execution_time': (
                profile.total_execution_time / profile.total_queries
                if profile.total_queries > 0 else 0
            ),
            'active_sessions': len(profile.active_sessions),
            'recent_queries': profile.query_history[-10:],
            'last_activity': profile.last_activity
        }
        
    async def get_favorite_queries(self, user_id: str) -> List[Dict]:
        """Kullanıcının en sık kullandığı query'leri getirir."""
        profile = await self.get_user_profile(user_id)
        
        # Analyze query patterns
        query_counts = {}
        for entry in profile.query_history:
            query_counts[entry.query] = query_counts.get(entry.query, 0) + 1
            
        # Sort by frequency
        favorites = sorted(
            query_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return [
            {
                'query': query,
                'usage_count': count,
                'last_used': max(
                    e.timestamp
                    for e in profile.query_history
                    if e.query == query
                )
            }
            for query, count in favorites[:10]
        ]