"""
Query Analytics and History Analysis Service for SQL Proxy

This module provides advanced analytics for SQL queries, including
usage patterns, optimization suggestions, and trend analysis.

Last updated: 2025-05-20 10:40:14
Updated by: Teeksss
"""

import logging
import json
import re
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime, timedelta
from collections import defaultdict
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.query import AuditLog
from app.services.query_similarity import query_similarity_service
from app.core.config import settings

logger = logging.getLogger(__name__)

class QueryAnalyzer:
    """
    Query analytics and history analysis service
    
    Provides insights into query patterns, performance, and optimization
    opportunities based on historical data.
    """
    
    def __init__(self):
        """Initialize the query analyzer"""
        self.similarity_threshold = settings.ANALYTICS_SIMILARITY_THRESHOLD
        self.min_query_count = settings.ANALYTICS_MIN_QUERY_COUNT
        self.slow_query_threshold_ms = settings.ANALYTICS_SLOW_QUERY_THRESHOLD_MS
        
        # Common inefficient query patterns to detect
        self.inefficient_patterns = [
            {
                "pattern": r"SELECT\s+\*\s+FROM",
                "description": "Using SELECT * instead of specific columns",
                "suggestion": "Specify only needed columns to reduce data transfer"
            },
            {
                "pattern": r"SELECT.*\bDISTINCT\b",
                "description": "Using DISTINCT may be inefficient for large result sets",
                "suggestion": "Consider if DISTINCT is really necessary, or use GROUP BY"
            },
            {
                "pattern": r"SELECT.*\bLIKE\s+['%].*?['%]",
                "description": "Leading wildcard in LIKE may prevent index usage",
                "suggestion": "Avoid leading wildcards (%) in LIKE patterns"
            },
            {
                "pattern": r"FROM\s+\w+\s+\w+\s+LEFT\s+JOIN.*?RIGHT\s+JOIN",
                "description": "Mixing LEFT and RIGHT JOINs is often confusing",
                "suggestion": "Standardize on either LEFT or RIGHT JOIN for readability"
            },
            {
                "pattern": r"WHERE\s+\w+\s*!=\s*NULL",
                "description": "Comparing with NULL using != won't work as expected",
                "suggestion": "Use 'IS NOT NULL' instead of '!= NULL'"
            },
            {
                "pattern": r"WHERE\s+\w+\s*=\s*NULL",
                "description": "Comparing with NULL using = won't work as expected",
                "suggestion": "Use 'IS NULL' instead of '= NULL'"
            },
            {
                "pattern": r"WHERE\s+.*?\s+OR\s+.*?\s*=",
                "description": "OR conditions may prevent index usage",
                "suggestion": "Consider using UNION or restructuring query"
            },
            {
                "pattern": r"ORDER\s+BY\s+RAND\(\)",
                "description": "ORDER BY RAND() is very inefficient",
                "suggestion": "Consider alternative methods for random selection"
            },
            {
                "pattern": r"SELECT\s+COUNT\(\*\)\s+FROM.*?GROUP\s+BY",
                "description": "COUNT(*) with GROUP BY can be inefficient",
                "suggestion": "Consider separate counts or denormalization"
            },
            {
                "pattern": r"SELECT.*?FROM.*?WHERE.*?IN\s*\(\s*SELECT",
                "description": "Subqueries in IN clauses may be inefficient",
                "suggestion": "Consider using JOIN instead of IN with subquery"
            }
        ]
        
        logger.info("Query analyzer initialized")
    
    def analyze_query_history(
        self, 
        db: Session,
        days: int = 30,
        server_alias: Optional[str] = None,
        username: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze query history for patterns and insights
        
        Args:
            db: Database session
            days: Number of days to analyze
            server_alias: Optional server to filter by
            username: Optional username to filter by
            
        Returns:
            Analysis results
        """
        try:
            # Calculate date range
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # Get query history
            query = db.query(AuditLog).filter(
                AuditLog.created_at >= start_date,
                AuditLog.created_at <= end_date
            )
            
            if server_alias:
                query = query.filter(AuditLog.target_server == server_alias)
            
            if username:
                query = query.filter(AuditLog.username == username)
            
            # Get query execution data
            query_data = query.order_by(AuditLog.created_at).all()
            
            if not query_data:
                return {
                    "message": "No query data found for the specified criteria",
                    "query_count": 0
                }
            
            # Analyze patterns
            result = {
                "query_count": len(query_data),
                "date_range": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "days": days
                },
                "query_type_distribution": self._analyze_query_types(query_data),
                "performance_metrics": self._analyze_performance(query_data),
                "hourly_distribution": self._analyze_time_patterns(query_data),
                "server_distribution": self._analyze_server_usage(query_data),
                "user_distribution": self._analyze_user_activity(query_data),
                "similar_query_clusters": self._find_similar_queries(query_data),
                "error_analysis": self._analyze_errors(query_data),
                "inefficient_queries": self._find_inefficient_queries(query_data),
                "optimization_opportunities": self._identify_optimization_opportunities(query_data, db)
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing query history: {str(e)}")
            return {
                "error": str(e)
            }
    
    def _analyze_query_types(self, query_data: List[AuditLog]) -> Dict[str, Any]:
        """
        Analyze distribution of query types
        
        Args:
            query_data: List of query audit logs
            
        Returns:
            Analysis of query types
        """
        # Count query types
        query_types = {}
        total_count = len(query_data)
        
        for log in query_data:
            query_type = log.query_type or "unknown"
            query_types[query_type] = query_types.get(query_type, 0) + 1
        
        # Calculate percentages
        percentages = {}
        for query_type, count in query_types.items():
            percentages[query_type] = round((count / total_count) * 100, 2)
        
        # Calculate read/write ratio
        read_queries = sum(query_types.get(qt, 0) for qt in ['SELECT'])
        write_queries = sum(query_types.get(qt, 0) for qt in ['INSERT', 'UPDATE', 'DELETE'])
        
        read_write_ratio = read_queries / write_queries if write_queries > 0 else float('inf')
        
        return {
            "counts": query_types,
            "percentages": percentages,
            "read_queries": read_queries,
            "write_queries": write_queries,
            "read_write_ratio": read_write_ratio
        }
    
    def _analyze_performance(self, query_data: List[AuditLog]) -> Dict[str, Any]:
        """
        Analyze query performance metrics
        
        Args:
            query_data: List of query audit logs
            
        Returns:
            Performance analysis
        """
        # Initialize metrics
        performance = {
            "execution_time": {
                "min": float('inf'),
                "max": 0,
                "avg": 0,
                "p90": 0,
                "p95": 0,
                "p99": 0
            },
            "slow_queries": {
                "count": 0,
                "percentage": 0,
                "samples": []
            },
            "rowcount": {
                "min": float('inf'),
                "max": 0,
                "avg": 0
            }
        }
        
        # Collect execution times
        execution_times = []
        
        for log in query_data:
            if log.execution_time_ms is not None:
                execution_times.append(log.execution_time_ms)
                
                # Update min/max times
                performance["execution_time"]["min"] = min(performance["execution_time"]["min"], log.execution_time_ms)
                performance["execution_time"]["max"] = max(performance["execution_time"]["max"], log.execution_time_ms)
                
                # Check for slow queries
                if log.execution_time_ms > self.slow_query_threshold_ms:
                    performance["slow_queries"]["count"] += 1
                    
                    # Add sample if we don't have too many
                    if len(performance["slow_queries"]["samples"]) < 10:
                        performance["slow_queries"]["samples"].append({
                            "id": log.id,
                            "query_text": log.query_text[:200] + "..." if len(log.query_text) > 200 else log.query_text,
                            "execution_time_ms": log.execution_time_ms,
                            "created_at": log.created_at.isoformat() if log.created_at else None
                        })
            
            # Update rowcount metrics
            if log.rowcount is not None and log.rowcount > 0:
                performance["rowcount"]["min"] = min(performance["rowcount"]["min"], log.rowcount)
                performance["rowcount"]["max"] = max(performance["rowcount"]["max"], log.rowcount)
        
        # Calculate averages and percentiles
        if execution_times:
            performance["execution_time"]["avg"] = sum(execution_times) / len(execution_times)
            
            # Sort for percentiles
            execution_times.sort()
            
            # Calculate percentiles
            p90_index = int(len(execution_times) * 0.9)
            p95_index = int(len(execution_times) * 0.95)
            p99_index = int(len(execution_times) * 0.99)
            
            performance["execution_time"]["p90"] = execution_times[p90_index]
            performance["execution_time"]["p95"] = execution_times[p95_index]
            performance["execution_time"]["p99"] = execution_times[p99_index]
            
            # Calculate slow query percentage
            performance["slow_queries"]["percentage"] = (performance["slow_queries"]["count"] / len(execution_times)) * 100
        else:
            # No execution time data
            performance["execution_time"]["min"] = 0
        
        # Calculate average rowcount
        rowcount_data = [log.rowcount for log in query_data if log.rowcount is not None and log.rowcount > 0]
        if rowcount_data:
            performance["rowcount"]["avg"] = sum(rowcount_data) / len(rowcount_data)
        else:
            performance["rowcount"]["min"] = 0
        
        return performance
    
    def _analyze_time_patterns(self, query_data: List[AuditLog]) -> Dict[str, Any]:
        """
        Analyze query execution time patterns
        
        Args:
            query_data: List of query audit logs
            
        Returns:
            Time-based pattern analysis
        """
        # Initialize counters
        hourly_counts = {hour: 0 for hour in range(24)}
        weekday_counts = {day: 0 for day in range(7)}  # 0=Monday, 6=Sunday
        
        for log in query_data:
            if log.created_at:
                hour = log.created_at.hour
                weekday = log.created_at.weekday()
                
                hourly_counts[hour] += 1
                weekday_counts[weekday] += 1
        
        # Format for output
        hourly_distribution = [
            {"hour": hour, "count": count}
            for hour, count in hourly_counts.items()
        ]
        
        weekday_distribution = [
            {"weekday": weekday, "count": count}
            for weekday, count in weekday_counts.items()
        ]
        
        # Find peak times
        max_hour = max(hourly_counts.items(), key=lambda x: x[1])[0]
        max_weekday = max(weekday_counts.items(), key=lambda x: x[1])[0]
        
        # Map weekday number to name
        weekday_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        
        return {
            "hourly_distribution": hourly_distribution,
            "weekday_distribution": weekday_distribution,
            "peak_hour": max_hour,
            "peak_weekday": weekday_names[max_weekday],
            "business_hours_percentage": self._calculate_business_hours_percentage(hourly_counts),
            "weekend_percentage": self._calculate_weekend_percentage(weekday_counts)
        }
    
    def _calculate_business_hours_percentage(self, hourly_counts: Dict[int, int]) -> float:
        """
        Calculate percentage of queries during business hours (9am-5pm)
        
        Args:
            hourly_counts: Dictionary of query counts by hour
            
        Returns:
            Percentage of queries during business hours
        """
        business_hours_count = sum(hourly_counts.get(hour, 0) for hour in range(9, 18))
        total_count = sum(hourly_counts.values())
        
        if total_count == 0:
            return 0
        
        return (business_hours_count / total_count) * 100
    
    def _calculate_weekend_percentage(self, weekday_counts: Dict[int, int]) -> float:
        """
        Calculate percentage of queries during weekends
        
        Args:
            weekday_counts: Dictionary of query counts by weekday
            
        Returns:
            Percentage of queries during weekends
        """
        weekend_count = weekday_counts.get(5, 0) + weekday_counts.get(6, 0)  # Saturday(5) and Sunday(6)
        total_count = sum(weekday_counts.values())
        
        if total_count == 0:
            return 0
        
        return (weekend_count / total_count) * 100
    
    def _analyze_server_usage(self, query_data: List[AuditLog]) -> Dict[str, Any]:
        """
        Analyze server usage patterns
        
        Args:
            query_data: List of query audit logs
            
        Returns:
            Server usage analysis
        """
        # Count queries by server
        server_counts = {}
        
        for log in query_data:
            server = log.target_server or "unknown"
            server_counts[server] = server_counts.get(server, 0) + 1
        
        # Calculate percentages
        total_count = len(query_data)
        server_percentages = {}
        
        for server, count in server_counts.items():
            server_percentages[server] = round((count / total_count) * 100, 2)
        
        # Format for output
        server_distribution = [
            {"server": server, "count": count, "percentage": server_percentages[server]}
            for server, count in server_counts.items()
        ]
        
        # Sort by count (descending)
        server_distribution.sort(key=lambda x: x["count"], reverse=True)
        
        # Find most and least used servers
        most_used = server_distribution[0]["server"] if server_distribution else None
        least_used = server_distribution[-1]["server"] if server_distribution else None
        
        return {
            "server_distribution": server_distribution,
            "most_used_server": most_used,
            "least_used_server": least_used,
            "server_count": len(server_counts)
        }
    
    def _analyze_user_activity(self, query_data: List[AuditLog]) -> Dict[str, Any]:
        """
        Analyze user activity patterns
        
        Args:
            query_data: List of query audit logs
            
        Returns:
            User activity analysis
        """
        # Count queries by user
        user_counts = {}
        user_query_types = {}
        
        for log in query_data:
            user = log.username or "unknown"
            query_type = log.query_type or "unknown"
            
            # Update user counts
            user_counts[user] = user_counts.get(user, 0) + 1
            
            # Update query types per user
            if user not in user_query_types:
                user_query_types[user] = {}
            
            user_query_types[user][query_type] = user_query_types[user].get(query_type, 0) + 1
        
        # Calculate percentages
        total_count = len(query_data)
        user_percentages = {}
        
        for user, count in user_counts.items():
            user_percentages[user] = round((count / total_count) * 100, 2)
        
        # Format for output
        user_distribution = [
            {
                "username": user,
                "count": count,
                "percentage": user_percentages[user],
                "query_types": user_query_types[user]
            }
            for user, count in user_counts.items()
        ]
        
        # Sort by count (descending)
        user_distribution.sort(key=lambda x: x["count"], reverse=True)
        
        # Calculate user diversity
        user_count = len(user_counts)
        diversity_index = 0
        
        if user_count > 0:
            # Calculate diversity using Shannon entropy
            for percentage in user_percentages.values():
                p = percentage / 100
                if p > 0:
                    diversity_index -= p * (np.log(p))
            
            # Normalize to 0-1 range
            max_entropy = np.log(user_count)
            if max_entropy > 0:
                diversity_index /= max_entropy
        
        return {
            "user_distribution": user_distribution,
            "user_count": user_count,
            "most_active_users": user_distribution[:5] if user_distribution else [],
            "user_diversity_index": diversity_index
        }
    
    def _find_similar_queries(self, query_data: List[AuditLog]) -> List[Dict[str, Any]]:
        """
        Find clusters of similar queries
        
        Args:
            query_data: List of query audit logs
            
        Returns:
            List of query clusters
        """
        # Extract query texts and ids
        queries = [
            {"id": log.id, "text": log.query_text, "created_at": log.created_at}
            for log in query_data
            if log.query_text
        ]
        
        # Use similarity service to cluster similar queries
        clusters = []
        processed_ids = set()
        
        for i, query in enumerate(queries):
            if query["id"] in processed_ids:
                continue
            
            # Find similar queries
            similar_queries = []
            
            for j, other_query in enumerate(queries):
                if i == j or other_query["id"] in processed_ids:
                    continue
                
                # Calculate similarity
                similarity = query_similarity_service.calculate_similarity(
                    query["text"],
                    other_query["text"]
                )
                
                if similarity >= self.similarity_threshold:
                    similar_queries.append({
                        "id": other_query["id"],
                        "text": other_query["text"],
                        "created_at": other_query["created_at"].isoformat() if other_query["created_at"] else None,
                        "similarity": similarity
                    })
                    processed_ids.add(other_query["id"])
            
            # If we found similar queries, create a cluster
            if similar_queries:
                processed_ids.add(query["id"])
                
                clusters.append({
                    "representative_query": {
                        "id": query["id"],
                        "text": query["text"],
                        "created_at": query["created_at"].isoformat() if query["created_at"] else None
                    },
                    "similar_queries": similar_queries,
                    "count": len(similar_queries) + 1
                })
        
        # Sort clusters by size (descending)
        clusters.sort(key=lambda x: x["count"], reverse=True)
        
        # Limit to reasonable number of clusters
        return clusters[:10]
    
    def _analyze_errors(self, query_data: List[AuditLog]) -> Dict[str, Any]:
        """
        Analyze query errors
        
        Args:
            query_data: List of query audit logs
            
        Returns:
            Error analysis
        """
        # Count errors
        error_count = 0
        error_types = {}
        error_samples = []
        
        for log in query_data:
            if log.execution_status != 'success' and log.error_message:
                error_count += 1
                
                # Extract error type
                error_type = self._categorize_error(log.error_message)
                error_types[error_type] = error_types.get(error_type, 0) + 1
                
                # Add sample if we don't have too many
                if len(error_samples) < 10:
                    error_samples.append({
                        "id": log.id,
                        "query_text": log.query_text[:200] + "..." if len(log.query_text) > 200 else log.query_text,
                        "error_message": log.error_message,
                        "created_at": log.created_at.isoformat() if log.created_at else None,
                        "error_type": error_type
                    })
        
        # Calculate error rate
        total_count = len(query_data)
        error_rate = (error_count / total_count) * 100 if total_count > 0 else 0
        
        # Format error types for output
        error_distribution = [
            {"type": error_type, "count": count}
            for error_type, count in error_types.items()
        ]
        
        # Sort by count (descending)
        error_distribution.sort(key=lambda x: x["count"], reverse=True)
        
        return {
            "error_count": error_count,
            "error_rate": error_rate,
            "error_distribution": error_distribution,
            "error_samples": error_samples
        }
    
    def _categorize_error(self, error_message: str) -> str:
        """
        Categorize an error message
        
        Args:
            error_message: Error message to categorize
            
        Returns:
            Error category
        """
        if not error_message:
            return "Unknown"
        
        error_message = error_message.lower()
        
        # Define error categories with keywords
        categories = {
            "Syntax Error": ["syntax error", "parsing error", "unexpected token", "expected"],
            "Permission Error": ["permission denied", "access denied", "privilege", "unauthorized"],
            "Connection Error": ["connection", "timed out", "network", "host", "unreachable"],
            "Resource Error": ["out of memory", "resource", "limit exceeded"],
            "Constraint Violation": ["constraint", "duplicate key", "unique", "foreign key", "reference"],
            "Type Error": ["data type", "conversion failed", "invalid input", "cannot cast"],
            "Timeout Error": ["timeout", "query cancelled", "execution time"],
            "Table/Column Error": ["no such table", "column does not exist", "relation", "attribute"]
        }
        
        # Match error message against categories
        for category, keywords in categories.items():
            if any(keyword in error_message for keyword in keywords):
                return category
        
        return "Other"
    
    def _find_inefficient_queries(self, query_data: List[AuditLog]) -> List[Dict[str, Any]]:
        """
        Find potentially inefficient queries
        
        Args:
            query_data: List of query audit logs
            
        Returns:
            List of inefficient queries with suggestions
        """
        inefficient_queries = []
        
        for log in query_data:
            if not log.query_text:
                continue
            
            query_text = log.query_text.upper()
            found_issues = []
            
            # Check against inefficient patterns
            for pattern_info in self.inefficient_patterns:
                if re.search(pattern_info["pattern"], query_text, re.IGNORECASE):
                    found_issues.append({
                        "description": pattern_info["description"],
                        "suggestion": pattern_info["suggestion"]
                    })
            
            # If issues found, add to list
            if found_issues:
                inefficient_queries.append({
                    "id": log.id,
                    "query_text": log.query_text[:200] + "..." if len(log.query_text) > 200 else log.query_text,
                    "execution_time_ms": log.execution_time_ms,
                    "created_at": log.created_at.isoformat() if log.created_at else None,
                    "issues": found_issues
                })
        
        # Sort by execution time (descending)
        inefficient_queries.sort(
            key=lambda x: x["execution_time_ms"] if x["execution_time_ms"] is not None else 0,
            reverse=True
        )
        
        # Limit to reasonable number of queries
        return inefficient_queries[:20]
    
    def _identify_optimization_opportunities(
        self, 
        query_data: List[AuditLog],
        db: Session
    ) -> Dict[str, Any]:
        """
        Identify optimization opportunities
        
        Args:
            query_data: List of query audit logs
            db: Database session
            
        Returns:
            Optimization recommendations
        """
        opportunities = {
            "cacheable_queries": self._find_cacheable_queries(query_data),
            "parameterization": self._check_parameterization(query_data),
            "whitelist_candidates": self._find_whitelist_candidates(query_data),
            "index_recommendations": self._recommend_indexes(query_data, db)
        }
        
        return opportunities
    
    def _find_cacheable_queries(self, query_data: List[AuditLog]) -> List[Dict[str, Any]]:
        """
        Find queries that could benefit from caching
        
        Args:
            query_data: List of query audit logs
            
        Returns:
            List of cacheable queries
        """
        # Group similar queries
        query_groups = defaultdict(list)
        
        for log in query_data:
            if log.query_type != 'SELECT' or not log.query_text:
                continue
            
            # Normalize query to group similar queries
            normalized_query = query_similarity_service.normalize_query(log.query_text)
            query_groups[normalized_query].append(log)
        
        # Find frequent queries that are good caching candidates
        cacheable_queries = []
        
        for normalized_query, logs in query_groups.items():
            if len(logs) < self.min_query_count:
                continue
            
            # Calculate average execution time
            total_time = sum(log.execution_time_ms for log in logs if log.execution_time_ms is not None)
            avg_time = total_time / len(logs) if len(logs) > 0 else 0
            
            # Calculate time span
            created_times = [log.created_at for log in logs if log.created_at is not None]
            time_span = (max(created_times) - min(created_times)).total_seconds() if created_times else 0
            
            # Calculate frequency (executions per hour)
            frequency = (len(logs) / (time_span / 3600)) if time_span > 0 else 0
            
            # If the query is frequent or expensive, consider it cacheable
            if frequency >= 1 or avg_time >= 100:  # More than once per hour or >100ms
                cacheable_queries.append({
                    "query_text": logs[0].query_text[:200] + "..." if len(logs[0].query_text) > 200 else logs[0].query_text,
                    "execution_count": len(logs),
                    "avg_execution_time_ms": avg_time,
                    "frequency_per_hour": frequency,
                    "potential_savings_ms_per_hour": avg_time * frequency
                })
        
        # Sort by potential savings (descending)
        cacheable_queries.sort(key=lambda x: x["potential_savings_ms_per_hour"], reverse=True)
        
        # Limit to reasonable number of queries
        return cacheable_queries[:10]
    
    def _check_parameterization(self, query_data: List[AuditLog]) -> Dict[str, Any]:
        """
        Check for query parameterization opportunities
        
        Args:
            query_data: List of query audit logs
            
        Returns:
            Parameterization recommendations
        """
        # Count parameterized vs non-parameterized queries
        parameterized_count = 0
        non_parameterized_count = 0
        parameterization_candidates = []
        
        for log in query_data:
            if not log.query_text:
                continue
            
            # Check if query is parameterized (has named parameters)
            has_parameters = False
            if log.query_params:
                has_parameters = True
            elif re.search(r'(?:%s|:\w+|\$\d+|\?)', log.query_text):
                has_parameters = True
            
            if has_parameters:
                parameterized_count += 1
            else:
                non_parameterized_count += 1
                
                # Check if query has literal values that could be parameterized
                if self._has_parameterization_opportunity(log.query_text):
                    if len(parameterization_candidates) < 10:
                        parameterization_candidates.append({
                            "id": log.id,
                            "query_text": log.query_text[:200] + "..." if len(log.query_text) > 200 else log.query_text,
                            "created_at": log.created_at.isoformat() if log.created_at else None,
                            "suggested_parameters": self._extract_potential_parameters(log.query_text)
                        })
        
        # Calculate parameterization rate
        total_count = parameterized_count + non_parameterized_count
        parameterization_rate = (parameterized_count / total_count) * 100 if total_count > 0 else 0
        
        return {
            "parameterized_count": parameterized_count,
            "non_parameterized_count": non_parameterized_count,
            "parameterization_rate": parameterization_rate,
            "parameterization_candidates": parameterization_candidates
        }
    
    def _has_parameterization_opportunity(self, query_text: str) -> bool:
        """
        Check if a query has literal values that could be parameterized
        
        Args:
            query_text: Query text to check
            
        Returns:
            True if query has parameterization opportunities
        """
        if not query_text:
            return False
        
        # Check for string literals
        has_string_literals = bool(re.search(r"'[^']*'", query_text))
        
        # Check for numeric literals in WHERE clause
        has_numeric_literals = bool(re.search(r"WHERE.*?(?:=|>|<|>=|<=|<>|!=)\s*\d+", query_text, re.IGNORECASE))
        
        return has_string_literals or has_numeric_literals
    
    def _extract_potential_parameters(self, query_text: str) -> List[Dict[str, str]]:
        """
        Extract potential parameters from a query
        
        Args:
            query_text: Query text to analyze
            
        Returns:
            List of potential parameters
        """
        parameters = []
        
        # Extract string literals
        string_literals = re.findall(r"'([^']*)'", query_text)
        for i, literal in enumerate(string_literals):
            if len(literal) <= 50:  # Ignore very long strings
                parameters.append({
                    "type": "string",
                    "value": literal,
                    "suggested_name": f"param{i+1}"
                })
        
        # Extract numeric literals in conditions
        numeric_matches = re.finditer(r"(\w+)\s*(?:=|>|<|>=|<=|<>|!=)\s*(\d+(?:\.\d+)?)", query_text, re.IGNORECASE)
        for match in numeric_matches:
            column_name = match.group(1)
            value = match.group(2)
            
            parameters.append({
                "type": "numeric",
                "value": value,
                "suggested_name": column_name
            })
        
        return parameters
    
    def _find_whitelist_candidates(self, query_data: List[AuditLog]) -> List[Dict[str, Any]]:
        """
        Find queries that are good candidates for whitelisting
        
        Args:
            query_data: List of query audit logs
            
        Returns:
            List of whitelist candidates
        """
        # Group similar queries
        query_groups = defaultdict(list)
        
        for log in query_data:
            if not log.query_text:
                continue
            
            # Normalize query to group similar queries
            normalized_query = query_similarity_service.normalize_query(log.query_text)
            query_groups[normalized_query].append(log)
        
        # Find frequently executed queries
        whitelist_candidates = []
        
        for normalized_query, logs in query_groups.items():
            if len(logs) < self.min_query_count:
                continue
            
            # Calculate success rate
            success_count = sum(1 for log in logs if log.execution_status == 'success')
            success_rate = (success_count / len(logs)) * 100 if len(logs) > 0 else 0
            
            # If the query is frequent and reliable, consider it for whitelisting
            if success_rate >= 90:  # At least 90% success rate
                whitelist_candidates.append({
                    "query_text": logs[0].query_text,
                    "execution_count": len(logs),
                    "success_rate": success_rate,
                    "last_executed": max(log.created_at for log in logs if log.created_at is not None).isoformat() if logs else None,
                    "users": list(set(log.username for log in logs if log.username))
                })
        
        # Sort by execution count (descending)
        whitelist_candidates.sort(key=lambda x: x["execution_count"], reverse=True)
        
        # Limit to reasonable number of queries
        return whitelist_candidates[:10]
    
    def _recommend_indexes(
        self, 
        query_data: List[AuditLog],
        db: Session
    ) -> List[Dict[str, Any]]:
        """
        Recommend indexes based on query patterns
        
        Args:
            query_data: List of query audit logs
            db: Database session
            
        Returns:
            List of index recommendations
        """
        # Analyze WHERE clauses to find commonly filtered columns
        filtered_columns = {}
        
        for log in query_data:
            if log.query_type != 'SELECT' or not log.query_text:
                continue
            
            # Extract tables and conditions from query
            tables, conditions = self._extract_tables_and_conditions(log.query_text)
            
            for table, table_conditions in conditions.items():
                for column in table_conditions:
                    key = f"{table}.{column}"
                    filtered_columns[key] = filtered_columns.get(key, 0) + 1
        
        # Find most frequently filtered columns
        frequently_filtered = [
            {"table_column": tc, "frequency": freq}
            for tc, freq in filtered_columns.items()
            if freq >= self.min_query_count
        ]
        
        # Sort by frequency (descending)
        frequently_filtered.sort(key=lambda x: x["frequency"], reverse=True)
        
        # Generate index recommendations
        recommendations = []
        for item in frequently_filtered[:20]:  # Limit to top 20
            table_column = item["table_column"].split('.')
            if len(table_column) == 2:
                table, column = table_column
                
                recommendations.append({
                    "table": table,
                    "column": column,
                    "frequency": item["frequency"],
                    "recommended_index": f"CREATE INDEX idx_{table}_{column} ON {table}({column})"
                })
        
        return recommendations
    
    def _extract_tables_and_conditions(self, query_text: str) -> Tuple[List[str], Dict[str, List[str]]]:
        """
        Extract tables and conditions from a query
        
        Args:
            query_text: Query text to analyze
            
        Returns:
            Tuple of (tables, conditions_by_table)
        """
        tables = []
        conditions_by_table = {}
        
        # Extract tables from FROM clause
        from_match = re.search(r'FROM\s+(.*?)(?:WHERE|ORDER BY|GROUP BY|LIMIT|$)', query_text, re.IGNORECASE | re.DOTALL)
        if from_match:
            from_clause = from_match.group(1).strip()
            
            # Handle simple case
            table_matches = re.findall(r'([a-zA-Z0-9_]+)(?:\s+AS\s+[a-zA-Z0-9_]+)?', from_clause, re.IGNORECASE)
            tables.extend(table_matches)
        
        # Extract conditions from WHERE clause
        where_match = re.search(r'WHERE\s+(.*?)(?:ORDER BY|GROUP BY|LIMIT|$)', query_text, re.IGNORECASE | re.DOTALL)
        if where_match:
            where_clause = where_match.group(1).strip()
            
            # Extract conditions for each table
            for table in tables:
                # Look for table.column conditions
                table_conditions = re.findall(rf'{table}\.([a-zA-Z0-9_]+)\s*(?:=|>|<|>=|<=|<>|!=|LIKE|IN)', where_clause, re.IGNORECASE)
                
                # Also look for just column conditions (assuming they're from this table)
                if not table_conditions:
                    column_conditions = re.findall(r'(?<!\w\.)([a-zA-Z0-9_]+)\s*(?:=|>|<|>=|<=|<>|!=|LIKE|IN)', where_clause, re.IGNORECASE)
                    table_conditions = column_conditions
                
                if table_conditions:
                    conditions_by_table[table] = table_conditions
        
        return tables, conditions_by_table

    def get_query_insights(
        self,
        db: Session,
        query_id: int
    ) -> Dict[str, Any]:
        """
        Get detailed insights for a specific query
        
        Args:
            db: Database session
            query_id: ID of the query to analyze
            
        Returns:
            Detailed query insights
        """
        try:
            # Get query
            query = db.query(AuditLog).filter(AuditLog.id == query_id).first()
            
            if not query:
                return {
                    "error": f"Query with ID {query_id} not found"
                }
            
            # Find similar queries in history
            similar_queries = []
            if query.query_text:
                similar_logs = db.query(AuditLog).filter(
                    AuditLog.id != query_id,
                    AuditLog.query_type == query.query_type
                ).order_by(AuditLog.created_at.desc()).limit(100).all()
                
                for log in similar_logs:
                    if not log.query_text:
                        continue
                    
                    similarity = query_similarity_service.calculate_similarity(
                        query.query_text,
                        log.query_text
                    )
                    
                    if similarity >= self.similarity_threshold:
                        similar_queries.append({
                            "id": log.id,
                            "query_text": log.query_text,
                            "execution_time_ms": log.execution_time_ms,
                            "created_at": log.created_at.isoformat() if log.created_at else None,
                            "similarity": similarity,
                            "username": log.username
                        })
            
            # Sort by similarity (descending)
            similar_queries.sort(key=lambda x: x["similarity"], reverse=True)
            
            # Analyze execution time trends
            execution_time_trends = None
            if query.query_hash:
                # Find queries with same hash
                hash_logs = db.query(AuditLog).filter(
                    AuditLog.query_hash == query.query_hash
                ).order_by(AuditLog.created_at).all()
                
                if hash_logs:
                    execution_times = [
                        {
                            "id": log.id,
                            "execution_time_ms": log.execution_time_ms,
                            "created_at": log.created_at.isoformat() if log.created_at else None
                        }
                        for log in hash_logs
                        if log.execution_time_ms is not None
                    ]
                    
                    avg_time = sum(item["execution_time_ms"] for item in execution_times) / len(execution_times) if execution_times else 0
                    
                    execution_time_trends = {
                        "execution_times": execution_times,
                        "average_time": avg_time,
                        "count": len(execution_times)
                    }
            
            # Get query inefficiency analysis
            inefficiencies = []
            if query.query_text:
                query_text = query.query_text.upper()
                
                for pattern_info in self.inefficient_patterns:
                    if re.search(pattern_info["pattern"], query_text, re.IGNORECASE):
                        inefficiencies.append({
                            "description": pattern_info["description"],
                            "suggestion": pattern_info["suggestion"]
                        })
            
            # Format result
            result = {
                "query": {
                    "id": query.id,
                    "query_text": query.query_text,
                    "query_type": query.query_type,
                    "query_hash": query.query_hash,
                    "execution_time_ms": query.execution_time_ms,
                    "rowcount": query.rowcount,
                    "created_at": query.created_at.isoformat() if query.created_at else None,
                    "username": query.username,
                    "target_server": query.target_server,
                    "execution_status": query.execution_status,
                    "error_message": query.error_message
                },
                "similar_queries": similar_queries[:10],  # Limit to 10
                "execution_time_trends": execution_time_trends,
                "inefficiencies": inefficiencies,
                "parameterization_opportunity": self._has_parameterization_opportunity(query.query_text),
                "potential_parameters": self._extract_potential_parameters(query.query_text) if query.query_text else []
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting query insights: {str(e)}")
            return {
                "error": str(e)
            }

# Create singleton instance
query_analyzer = QueryAnalyzer()

# Son güncelleme: 2025-05-20 10:40:14
# Güncelleyen: Teeksss