"""
Query Optimization Service for SQL Proxy

This module provides functionality for analyzing and optimizing SQL queries.

Last updated: 2025-05-21 07:11:02
Updated by: Teeksss
"""

import logging
import re
import time
from typing import Dict, List, Any, Optional, Tuple
import sqlparse
from sqlalchemy.orm import Session

from app.models.server import Server
from app.services.security_service import security_service
from app.services.query_service import query_service

logger = logging.getLogger(__name__)

class QueryOptimizationService:
    """
    Service for analyzing and optimizing SQL queries
    
    Provides functionality for SQL query analysis, suggestion generation,
    and performance optimization.
    """
    
    def __init__(self):
        """Initialize query optimization service"""
        self.optimization_rules = self._initialize_optimization_rules()
    
    def _initialize_optimization_rules(self) -> List[Dict[str, Any]]:
        """
        Initialize query optimization rules
        
        Returns:
            List of optimization rules
        """
        return [
            {
                "name": "missing_where_clause",
                "pattern": r"SELECT\s+.+\s+FROM\s+(\w+)(?!\s+WHERE)",
                "message": "Query missing WHERE clause may return too many rows",
                "severity": "warning",
                "suggestion": "Add a WHERE clause to limit returned rows"
            },
            {
                "name": "select_star",
                "pattern": r"SELECT\s+\*\s+FROM",
                "message": "Using SELECT * may retrieve unnecessary columns",
                "severity": "info",
                "suggestion": "Specify only needed columns: SELECT col1, col2, ..."
            },
            {
                "name": "implicit_conversion",
                "pattern": r"WHERE\s+\w+\s*=\s*CONVERT\(",
                "message": "Implicit conversion may prevent index usage",
                "severity": "warning",
                "suggestion": "Ensure consistent data types in comparisons"
            },
            {
                "name": "non_sargable",
                "pattern": r"WHERE\s+\w+\s*LIKE\s*['\"]%",
                "message": "Leading wildcard in LIKE prevents index usage",
                "severity": "warning",
                "suggestion": "Consider using full-text search or remove leading %"
            },
            {
                "name": "nested_subqueries",
                "pattern": r"SELECT.+\(SELECT.+\(SELECT",
                "message": "Multiple nested subqueries may impact performance",
                "severity": "warning",
                "suggestion": "Consider using CTEs or JOINs instead of nested subqueries"
            },
            {
                "name": "large_in_clause",
                "pattern": r"IN\s*\([^)]{300,}\)",
                "message": "Large IN clause may impact performance",
                "severity": "warning",
                "suggestion": "Use temporary table or JOIN instead of large IN list"
            },
            {
                "name": "cross_join",
                "pattern": r"FROM\s+\w+\s*,\s*\w+\s+WHERE",
                "message": "Implicit cross join detected",
                "severity": "warning",
                "suggestion": "Use explicit JOIN syntax for better readability"
            },
            {
                "name": "order_by_rand",
                "pattern": r"ORDER\s+BY\s+RAND\(\)",
                "message": "ORDER BY RAND() is extremely inefficient",
                "severity": "error",
                "suggestion": "Use application-side randomization or indexed column"
            },
            {
                "name": "cursor_usage",
                "pattern": r"DECLARE\s+.+\s+CURSOR",
                "message": "Cursor usage is usually less efficient than set-based operations",
                "severity": "warning",
                "suggestion": "Consider set-based operations instead of cursors"
            },
            {
                "name": "function_on_column",
                "pattern": r"WHERE\s+\w+\(\w+\)",
                "message": "Function on column prevents index usage",
                "severity": "warning",
                "suggestion": "Move function to the right side of the comparison"
            }
        ]
    
    async def analyze_query(
        self,
        sql_text: str,
        server_id: Optional[str] = None,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """
        Analyze an SQL query for potential issues and optimization opportunities
        
        Args:
            sql_text: SQL query text
            server_id: Optional server ID for context-aware analysis
            db: Optional database session
            
        Returns:
            Query analysis results
        """
        # Start time for performance measurement
        start_time = time.time()
        
        # Clean and format the query
        formatted_sql = self.format_query(sql_text)
        
        # Apply optimization rules
        issues = self.apply_optimization_rules(formatted_sql)
        
        # Get query complexity metrics
        complexity = self.calculate_complexity(formatted_sql)
        
        # Get potential performance impact
        performance_impact = self.estimate_performance_impact(complexity, issues)
        
        # Get optimization suggestions
        suggestions = self.generate_optimization_suggestions(formatted_sql, issues, server_id, db)
        
        # Calculate analysis time
        analysis_time = time.time() - start_time
        
        # Create analysis result
        result = {
            "formatted_sql": formatted_sql,
            "issues": issues,
            "complexity": complexity,
            "performance_impact": performance_impact,
            "suggestions": suggestions,
            "analysis_time_ms": round(analysis_time * 1000, 2)
        }
        
        return result
    
    def format_query(self, sql_text: str) -> str:
        """
        Format and normalize an SQL query
        
        Args:
            sql_text: SQL query text
            
        Returns:
            Formatted SQL query
        """
        try:
            # Parse SQL
            parsed = sqlparse.parse(sql_text)
            
            if not parsed:
                return sql_text
            
            # Format query with consistent capitalization and indentation
            formatted = sqlparse.format(
                sql_text,
                keyword_case='upper',
                identifier_case='lower',
                reindent=True,
                indent_width=4
            )
            
            return formatted
        except Exception as e:
            logger.error(f"Error formatting query: {e}", exc_info=True)
            return sql_text
    
    def apply_optimization_rules(self, sql_text: str) -> List[Dict[str, Any]]:
        """
        Apply optimization rules to detect issues in SQL query
        
        Args:
            sql_text: SQL query text
            
        Returns:
            List of detected issues
        """
        issues = []
        
        # Normalize SQL for rule matching
        normalized_sql = " ".join(sql_text.upper().split())
        
        # Apply each rule
        for rule in self.optimization_rules:
            if re.search(rule["pattern"], normalized_sql, re.IGNORECASE):
                issue = {
                    "rule": rule["name"],
                    "message": rule["message"],
                    "severity": rule["severity"],
                    "suggestion": rule["suggestion"]
                }
                issues.append(issue)
        
        return issues
    
    def calculate_complexity(self, sql_text: str) -> Dict[str, Any]:
        """
        Calculate complexity metrics for an SQL query
        
        Args:
            sql_text: SQL query text
            
        Returns:
            Complexity metrics
        """
        # Normalize SQL
        normalized_sql = " ".join(sql_text.upper().split())
        
        # Count basic metrics
        table_count = len(re.findall(r"FROM\s+(\w+)|JOIN\s+(\w+)", normalized_sql))
        join_count = len(re.findall(r"JOIN", normalized_sql))
        where_conditions = len(re.findall(r"AND|OR", normalized_sql)) + (1 if "WHERE" in normalized_sql else 0)
        subquery_count = len(re.findall(r"\(\s*SELECT", normalized_sql))
        aggregation_count = len(re.findall(r"SUM\(|AVG\(|MIN\(|MAX\(|COUNT\(", normalized_sql))
        order_by = "ORDER BY" in normalized_sql
        group_by = "GROUP BY" in normalized_sql
        having = "HAVING" in normalized_sql
        
        # Calculate overall complexity score (0-100)
        complexity_score = min(100, (
            table_count * 5 +
            join_count * 10 +
            where_conditions * 3 +
            subquery_count * 15 +
            aggregation_count * 5 +
            (10 if order_by else 0) +
            (15 if group_by else 0) +
            (20 if having else 0)
        ))
        
        return {
            "table_count": table_count,
            "join_count": join_count,
            "where_conditions": where_conditions,
            "subquery_count": subquery_count,
            "aggregation_count": aggregation_count,
            "has_order_by": order_by,
            "has_group_by": group_by,
            "has_having": having,
            "score": complexity_score
        }
    
    def estimate_performance_impact(
        self,
        complexity: Dict[str, Any],
        issues: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Estimate performance impact based on complexity and issues
        
        Args:
            complexity: Query complexity metrics
            issues: Detected issues
            
        Returns:
            Performance impact estimation
        """
        # Calculate severity score from issues
        severity_score = 0
        for issue in issues:
            if issue["severity"] == "error":
                severity_score += 30
            elif issue["severity"] == "warning":
                severity_score += 10
            elif issue["severity"] == "info":
                severity_score += 2
        
        # Calculate overall impact score (0-100)
        impact_score = min(100, (
            complexity["score"] * 0.6 +
            severity_score * 0.4
        ))
        
        # Determine impact level
        if impact_score >= 70:
            impact_level = "high"
        elif impact_score >= 40:
            impact_level = "medium"
        else:
            impact_level = "low"
        
        return {
            "score": round(impact_score),
            "level": impact_level,
            "description": self.get_impact_description(impact_level)
        }
    
    def get_impact_description(self, impact_level: str) -> str:
        """
        Get description for a performance impact level
        
        Args:
            impact_level: Impact level (low, medium, high)
            
        Returns:
            Impact description
        """
        if impact_level == "high":
            return "This query may have significant performance issues and should be optimized before using in production."
        elif impact_level == "medium":
            return "This query has some potential performance issues that could be improved."
        else:
            return "This query appears to be relatively efficient with minor or no issues detected."
    
    async def generate_optimization_suggestions(
        self,
        sql_text: str,
        issues: List[Dict[str, Any]],
        server_id: Optional[str] = None,
        db: Optional[Session] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate specific optimization suggestions for an SQL query
        
        Args:
            sql_text: SQL query text
            issues: Detected issues
            server_id: Optional server ID for context-aware suggestions
            db: Optional database session
            
        Returns:
            List of optimization suggestions
        """
        suggestions = []
        
        # Add basic suggestions from issues
        for issue in issues:
            suggestions.append({
                "type": issue["rule"],
                "description": issue["suggestion"],
                "priority": "high" if issue["severity"] == "error" else (
                    "medium" if issue["severity"] == "warning" else "low"
                )
            })
        
        # Add general optimization suggestions
        if "SELECT *" in sql_text:
            suggestions.append({
                "type": "column_selection",
                "description": "Specify only needed columns instead of SELECT * to reduce I/O and network traffic",
                "priority": "medium"
            })
        
        if "ORDER BY" in sql_text and "LIMIT" not in sql_text and "TOP" not in sql_text:
            suggestions.append({
                "type": "pagination",
                "description": "Add LIMIT/TOP clause when using ORDER BY to improve performance for large result sets",
                "priority": "medium"
            })
        
        # Add database-specific suggestions if server context available
        if server_id and db:
            try:
                server = db.query(Server).filter(Server.id == server_id).first()
                if server:
                    db_type = server.db_type.lower()
                    
                    if db_type == "sqlserver":
                        # SQL Server specific suggestions
                        if "SELECT TOP" not in sql_text and "OFFSET" not in sql_text:
                            suggestions.append({
                                "type": "sqlserver_pagination",
                                "description": "Use OFFSET/FETCH or TOP for pagination in SQL Server",
                                "priority": "medium"
                            })
                    
                    elif db_type == "postgresql":
                        # PostgreSQL specific suggestions
                        if "ilike" in sql_text.lower():
                            suggestions.append({
                                "type": "postgresql_ilike",
                                "description": "Consider using pg_trgm indexes for ILIKE operations",
                                "priority": "medium"
                            })
                    
                    elif db_type == "mysql":
                        # MySQL specific suggestions
                        if "order by" in sql_text.lower() and "limit" not in sql_text.lower():
                            suggestions.append({
                                "type": "mysql_limit",
                                "description": "Add LIMIT clause when using ORDER BY in MySQL for better performance",
                                "priority": "medium"
                            })
            except Exception as e:
                logger.error(f"Error generating database-specific suggestions: {e}", exc_info=True)
        
        return suggestions
    
    async def execute_with_analysis(
        self,
        sql_text: str,
        server_id: str,
        user_id: int,
        db: Session,
        analyze_only: bool = False
    ) -> Dict[str, Any]:
        """
        Execute a query with performance analysis
        
        Args:
            sql_text: SQL query text
            server_id: Server ID
            user_id: User ID
            db: Database session
            analyze_only: Whether to only analyze without executing
            
        Returns:
            Execution result with analysis
        """
        # Analyze query
        analysis = await self.analyze_query(sql_text, server_id, db)
        
        # Check if execution should be skipped
        if analyze_only:
            return {
                "analysis": analysis,
                "executed": False
            }
        
        # Get optimized query if possible
        optimized_sql = await self.get_optimized_query(sql_text, analysis)
        
        # Execute query
        start_time = time.time()
        result = await query_service.execute_query(
            server_id=server_id,
            sql_text=optimized_sql or sql_text,
            user_id=user_id,
            db=db
        )
        execution_time = time.time() - start_time
        
        # Combine results
        return {
            "result": result,
            "analysis": analysis,
            "optimized_sql": optimized_sql,
            "executed": True,
            "execution_time_ms": round(execution_time * 1000, 2),
            "used_optimized_query": optimized_sql is not None
        }
    
    async def get_optimized_query(
        self,
        sql_text: str,
        analysis: Dict[str, Any]
    ) -> Optional[str]:
        """
        Get optimized version of a query if possible
        
        Args:
            sql_text: Original SQL query text
            analysis: Query analysis results
            
        Returns:
            Optimized SQL query text or None if no optimization applied
        """
        # Currently, we don't implement automatic optimization
        # This would be a complex feature requiring SQL parsing and transformation
        # For now, return None to indicate no optimization was applied
        return None
    
    async def benchmark_query(
        self,
        sql_text: str,
        server_id: str,
        user_id: int,
        db: Session,
        iterations: int = 3
    ) -> Dict[str, Any]:
        """
        Benchmark a query to measure performance
        
        Args:
            sql_text: SQL query text
            server_id: Server ID
            user_id: User ID
            db: Database session
            iterations: Number of iterations to run
            
        Returns:
            Benchmark results
        """
        # Analyze query
        analysis = await self.analyze_query(sql_text, server_id, db)
        
        # Run initial query to warm up
        await query_service.execute_query(
            server_id=server_id,
            sql_text=sql_text,
            user_id=user_id,
            db=db
        )
        
        # Run benchmark iterations
        execution_times = []
        for i in range(iterations):
            start_time = time.time()
            result = await query_service.execute_query(
                server_id=server_id,
                sql_text=sql_text,
                user_id=user_id,
                db=db
            )
            execution_time = time.time() - start_time
            execution_times.append(round(execution_time * 1000, 2))  # ms
        
        # Calculate statistics
        avg_time = sum(execution_times) / len(execution_times)
        min_time = min(execution_times)
        max_time = max(execution_times)
        
        # Get result metadata
        row_count = len(result.get("rows", [])) if result.get("success", False) else 0
        
        return {
            "analysis": analysis,
            "benchmark": {
                "iterations": iterations,
                "execution_times_ms": execution_times,
                "avg_execution_time_ms": round(avg_time, 2),
                "min_execution_time_ms": min_time,
                "max_execution_time_ms": max_time,
                "row_count": row_count
            }
        }

# Initialize query optimization service
query_optimization_service = QueryOptimizationService()

# Son güncelleme: 2025-05-21 07:11:02
# Güncelleyen: Teeksss