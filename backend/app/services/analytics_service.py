"""
Analytics Service for SQL Proxy

This module provides analytics and reporting functionality for
query usage patterns and database performance.

Last updated: 2025-05-21 05:32:06
Updated by: Teeksss
"""

import logging
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np
from collections import Counter, defaultdict

from app.db.session import get_db
from app.models.query import QueryLog, SavedQuery
from app.models.server import ServerConfig
from app.models.user import User
from app.utils.performance_analyzer import get_performance_summary

logger = logging.getLogger(__name__)

class AnalyticsService:
    """
    Service for gathering and analyzing SQL proxy usage data
    
    Provides analytics and reporting functionality for queries, users,
    and database performance.
    """
    
    async def get_query_analytics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        server_id: Optional[str] = None,
        user_id: Optional[int] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Get query analytics data
        
        Args:
            start_date: Start date for analytics
            end_date: End date for analytics
            server_id: Filter by server ID
            user_id: Filter by user ID
            limit: Maximum number of items to return
            
        Returns:
            Query analytics data
        """
        try:
            db = next(get_db())
            
            # Set default dates if not provided
            if not end_date:
                end_date = datetime.utcnow()
            if not start_date:
                start_date = end_date - timedelta(days=30)
            
            # Query logs with filters
            query = db.query(QueryLog)
            
            if start_date:
                query = query.filter(QueryLog.executed_at >= start_date)
            if end_date:
                query = query.filter(QueryLog.executed_at <= end_date)
            if server_id:
                query = query.filter(QueryLog.server_id == server_id)
            if user_id:
                query = query.filter(QueryLog.user_id == user_id)
            
            # Order by execution time, descending
            query = query.order_by(QueryLog.executed_at.desc())
            
            # Limit the results
            query_logs = query.limit(limit).all()
            
            # Get total query count for the period
            total_count = query.count()
            
            # Calculate metrics
            execution_times = [log.execution_time for log in query_logs if log.execution_time]
            
            avg_execution_time = np.mean(execution_times) if execution_times else 0
            max_execution_time = max(execution_times) if execution_times else 0
            
            # Count queries by status
            status_counts = Counter([log.status for log in query_logs])
            
            # Count queries by server
            server_counts = Counter([log.server_id for log in query_logs])
            
            # Count queries by user
            user_counts = Counter([log.user_id for log in query_logs])
            
            # Get top users
            top_users = []
            
            for user_id, count in user_counts.most_common(10):
                user = db.query(User).filter(User.id == user_id).first()
                if user:
                    top_users.append({
                        "user_id": user_id,
                        "username": user.username,
                        "query_count": count
                    })
            
            # Get top servers
            top_servers = []
            
            for server_id, count in server_counts.most_common(10):
                server = db.query(ServerConfig).filter(ServerConfig.id == server_id).first()
                if server:
                    top_servers.append({
                        "server_id": server_id,
                        "server_name": server.alias or server.host,
                        "query_count": count
                    })
            
            # Get recent logs with user and server info
            recent_logs = []
            
            for log in query_logs[:20]:  # Limit to top 20 for detailed view
                user = db.query(User).filter(User.id == log.user_id).first() if log.user_id else None
                server = db.query(ServerConfig).filter(ServerConfig.id == log.server_id).first() if log.server_id else None
                
                recent_logs.append({
                    "id": log.id,
                    "query_text": log.query_text,
                    "status": log.status,
                    "execution_time": log.execution_time,
                    "executed_at": log.executed_at.isoformat() if log.executed_at else None,
                    "rows_affected": log.rows_affected,
                    "user": user.username if user else None,
                    "server": server.alias or server.host if server else None
                })
            
            # Calculate query patterns (e.g., keywords)
            keywords = ["SELECT", "INSERT", "UPDATE", "DELETE", "JOIN", "WHERE", "GROUP BY", "ORDER BY", "LIMIT"]
            keyword_counts = defaultdict(int)
            
            for log in query_logs:
                if not log.query_text:
                    continue
                
                query_upper = log.query_text.upper()
                for keyword in keywords:
                    if keyword in query_upper:
                        keyword_counts[keyword] += 1
            
            # Get performance metrics
            performance_summary = get_performance_summary()
            
            # Compile results
            results = {
                "total_queries": total_count,
                "date_range": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                },
                "execution_metrics": {
                    "average_time": avg_execution_time,
                    "max_time": max_execution_time,
                    "status_counts": dict(status_counts)
                },
                "top_users": top_users,
                "top_servers": top_servers,
                "query_patterns": {k: v for k, v in sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)},
                "recent_logs": recent_logs,
                "performance_summary": performance_summary
            }
            
            return results
            
        except Exception as e:
            logger.error(f"Error getting query analytics: {e}", exc_info=True)
            raise
    
    async def get_user_activity(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Get user activity analytics
        
        Args:
            start_date: Start date for analytics
            end_date: End date for analytics
            limit: Maximum number of users to return
            
        Returns:
            User activity data
        """
        try:
            db = next(get_db())
            
            # Set default dates if not provided
            if not end_date:
                end_date = datetime.utcnow()
            if not start_date:
                start_date = end_date - timedelta(days=30)
            
            # Query user activity
            query = db.query(
                User.id, 
                User.username,
                User.email,
                User.is_active,
                db.func.count(QueryLog.id).label("query_count"),
                db.func.max(QueryLog.executed_at).label("last_activity")
            )
            
            # Join with query logs
            query = query.outerjoin(QueryLog, User.id == QueryLog.user_id)
            
            # Apply date filters to query logs
            query = query.filter(QueryLog.executed_at.between(start_date, end_date))
            
            # Group by user
            query = query.group_by(User.id)
            
            # Order by query count, descending
            query = query.order_by(db.func.count(QueryLog.id).desc())
            
            # Limit the results
            user_activities = query.limit(limit).all()
            
            # Format results
            results = {
                "date_range": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                },
                "users": []
            }
            
            for user in user_activities:
                results["users"].append({
                    "user_id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "is_active": user.is_active,
                    "query_count": user.query_count,
                    "last_activity": user.last_activity.isoformat() if user.last_activity else None
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Error getting user activity: {e}", exc_info=True)
            raise
    
    async def get_server_usage(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get server usage analytics
        
        Args:
            start_date: Start date for analytics
            end_date: End date for analytics
            
        Returns:
            Server usage data
        """
        try:
            db = next(get_db())
            
            # Set default dates if not provided
            if not end_date:
                end_date = datetime.utcnow()
            if not start_date:
                start_date = end_date - timedelta(days=30)
            
            # Query server usage
            query = db.query(
                ServerConfig.id,
                ServerConfig.alias,
                ServerConfig.host,
                ServerConfig.database,
                ServerConfig.server_type,
                db.func.count(QueryLog.id).label("query_count"),
                db.func.avg(QueryLog.execution_time).label("avg_execution_time"),
                db.func.max(QueryLog.execution_time).label("max_execution_time"),
                db.func.min(QueryLog.execution_time).label("min_execution_time"),
                db.func.max(QueryLog.executed_at).label("last_activity")
            )
            
            # Join with query logs
            query = query.outerjoin(QueryLog, ServerConfig.id == QueryLog.server_id)
            
            # Apply date filters to query logs
            query = query.filter(QueryLog.executed_at.between(start_date, end_date))
            
            # Group by server
            query = query.group_by(ServerConfig.id)
            
            # Order by query count, descending
            query = query.order_by(db.func.count(QueryLog.id).desc())
            
            # Execute query
            server_usages = query.all()
            
            # Format results
            results = {
                "date_range": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                },
                "servers": []
            }
            
            for server in server_usages:
                results["servers"].append({
                    "server_id": server.id,
                    "server_name": server.alias or server.host,
                    "host": server.host,
                    "database": server.database,
                    "server_type": server.server_type,
                    "query_count": server.query_count,
                    "avg_execution_time": server.avg_execution_time,
                    "max_execution_time": server.max_execution_time,
                    "min_execution_time": server.min_execution_time,
                    "last_activity": server.last_activity.isoformat() if server.last_activity else None
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Error getting server usage: {e}", exc_info=True)
            raise
    
    async def generate_report(
        self,
        report_type: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        server_id: Optional[str] = None,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate a report
        
        Args:
            report_type: Type of report (query_analytics, user_activity, server_usage)
            start_date: Start date for report
            end_date: End date for report
            server_id: Filter by server ID
            user_id: Filter by user ID
            
        Returns:
            Report data
        """
        try:
            # Set default dates if not provided
            if not end_date:
                end_date = datetime.utcnow()
            if not start_date:
                start_date = end_date - timedelta(days=30)
            
            # Generate report based on type
            if report_type == "query_analytics":
                report_data = await self.get_query_analytics(
                    start_date=start_date,
                    end_date=end_date,
                    server_id=server_id,
                    user_id=user_id
                )
            elif report_type == "user_activity":
                report_data = await self.get_user_activity(
                    start_date=start_date,
                    end_date=end_date
                )
            elif report_type == "server_usage":
                report_data = await self.get_server_usage(
                    start_date=start_date,
                    end_date=end_date
                )
            else:
                raise ValueError(f"Unsupported report type: {report_type}")
            
            # Add report metadata
            report = {
                "report_type": report_type,
                "generated_at": datetime.utcnow().isoformat(),
                "date_range": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                },
                "filters": {
                    "server_id": server_id,
                    "user_id": user_id
                },
                "data": report_data
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating report: {e}", exc_info=True)
            raise

# Initialize analytics service
analytics_service = AnalyticsService()

# Son güncelleme: 2025-05-21 05:32:06
# Güncelleyen: Teeksss