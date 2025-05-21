"""
Machine Learning Based Query Suggestions Service for SQL Proxy

This module provides functionality for analyzing query patterns and
generating intelligent SQL query suggestions based on user history.

Last updated: 2025-05-21 07:25:48
Updated by: Teeksss
"""

import logging
import re
import json
import time
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np
from sqlalchemy.orm import Session
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import joblib
import os
from pathlib import Path

from app.models.user import User
from app.models.query_history import QueryHistory
from app.services.cache_service import cache_service

logger = logging.getLogger(__name__)

class MLSuggestionsService:
    """
    Service for machine learning based query suggestions
    
    Provides functionality for analyzing SQL query patterns and generating
    intelligent suggestions based on user history and context.
    """
    
    def __init__(self):
        """Initialize ML suggestions service"""
        self.models_dir = Path("app/ml_models")
        self.models_dir.mkdir(exist_ok=True, parents=True)
        
        self.vectorizer_path = self.models_dir / "query_vectorizer.joblib"
        self.vectorizer = self._load_vectorizer()
        
        self.similarity_threshold = 0.65
        self.max_suggestions = 10
        self.min_query_history = 20
        self.background_task = None
        self.analysis_running = False
        
        # Tokenization patterns for SQL
        self.sql_tokens_pattern = re.compile(r'''
            \b(?:SELECT|FROM|WHERE|JOIN|GROUP\s+BY|ORDER\s+BY|HAVING|LIMIT|OFFSET|
               INSERT|UPDATE|DELETE|CREATE|ALTER|DROP|TRUNCATE|WITH|UNION|INTERSECT|
               EXCEPT|CASE|WHEN|THEN|ELSE|END|AND|OR|NOT|IN|LIKE|BETWEEN|IS|NULL|
               EXISTS|ALL|ANY|SOME|DISTINCT|ON|AS|ASC|DESC|INNER|OUTER|LEFT|RIGHT|FULL|
               NATURAL|CROSS)\b|
            [(),;.]|
            \b\w+\b
        ''', re.IGNORECASE | re.VERBOSE)
    
    def _load_vectorizer(self) -> Optional[TfidfVectorizer]:
        """
        Load TF-IDF vectorizer model
        
        Returns:
            TF-IDF vectorizer model
        """
        try:
            if self.vectorizer_path.exists():
                return joblib.load(self.vectorizer_path)
            else:
                # Create new vectorizer if none exists
                return TfidfVectorizer(
                    analyzer='word',
                    ngram_range=(1, 3),
                    max_features=5000,
                    stop_words=None
                )
        except Exception as e:
            logger.error(f"Error loading vectorizer model: {e}", exc_info=True)
            return TfidfVectorizer(
                analyzer='word',
                ngram_range=(1, 3),
                max_features=5000,
                stop_words=None
            )
    
    def _save_vectorizer(self):
        """Save TF-IDF vectorizer model"""
        try:
            if self.vectorizer:
                joblib.dump(self.vectorizer, self.vectorizer_path)
                logger.info("Vectorizer model saved successfully")
        except Exception as e:
            logger.error(f"Error saving vectorizer model: {e}", exc_info=True)
    
    def start_background_analysis(self):
        """Start background query analysis task"""
        if self.background_task is None:
            self.background_task = asyncio.create_task(self._background_analysis_loop())
            logger.info("Background query analysis started")
    
    def stop_background_analysis(self):
        """Stop background query analysis task"""
        if self.background_task is not None:
            self.background_task.cancel()
            self.background_task = None
            logger.info("Background query analysis stopped")
    
    async def _background_analysis_loop(self):
        """Background analysis loop to periodically analyze queries"""
        try:
            while True:
                # Run analysis at night (3 AM)
                now = datetime.now()
                target_time = now.replace(hour=3, minute=0, second=0, microsecond=0)
                
                if now > target_time:
                    target_time = target_time + timedelta(days=1)
                
                seconds_until_target = (target_time - now).total_seconds()
                
                # Wait until target time
                await asyncio.sleep(seconds_until_target)
                
                # Run analysis if not already running
                if not self.analysis_running:
                    from app.db.session import SessionLocal
                    db = SessionLocal()
                    try:
                        await self.analyze_query_patterns(db)
                    finally:
                        db.close()
        except asyncio.CancelledError:
            logger.info("Background query analysis task cancelled")
        except Exception as e:
            logger.error(f"Error in background query analysis: {e}", exc_info=True)
    
    async def analyze_query_patterns(self, db: Session) -> bool:
        """
        Analyze query patterns and update suggestion models
        
        Args:
            db: Database session
            
        Returns:
            Success status
        """
        if self.analysis_running:
            logger.info("Query pattern analysis already running")
            return False
        
        try:
            self.analysis_running = True
            logger.info("Starting query pattern analysis")
            
            # Get all queries from history (last 90 days)
            ninety_days_ago = datetime.utcnow() - timedelta(days=90)
            queries = db.query(QueryHistory) \
                .filter(QueryHistory.executed_at > ninety_days_ago) \
                .filter(QueryHistory.status == 'success') \
                .all()
            
            if not queries or len(queries) < self.min_query_history:
                logger.info(f"Not enough query history for analysis. Found {len(queries) if queries else 0} queries.")
                return False
            
            # Prepare data for vectorization
            query_texts = [self._normalize_query(q.sql_text) for q in queries]
            
            # Create or update vectorizer
            self.vectorizer.fit(query_texts)
            self._save_vectorizer()
            
            logger.info(f"Query pattern analysis completed successfully. Analyzed {len(queries)} queries.")
            return True
        
        except Exception as e:
            logger.error(f"Error analyzing query patterns: {e}", exc_info=True)
            return False
        
        finally:
            self.analysis_running = False
    
    def _normalize_query(self, sql_text: str) -> str:
        """
        Normalize SQL query for analysis
        
        Args:
            sql_text: SQL query text
            
        Returns:
            Normalized SQL query
        """
        # Convert to lowercase
        normalized = sql_text.lower()
        
        # Remove comments
        normalized = re.sub(r'--.*$', ' ', normalized, flags=re.MULTILINE)
        normalized = re.sub(r'/\*.*?\*/', ' ', normalized, flags=re.DOTALL)
        
        # Replace literal values with placeholders
        normalized = re.sub(r"'[^']*'", "'?'", normalized)
        normalized = re.sub(r'"[^"]*"', '"?"', normalized)
        normalized = re.sub(r'\b\d+\b', '?', normalized)
        
        # Normalize whitespace
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
    
    def _tokenize_query(self, sql_text: str) -> List[str]:
        """
        Tokenize SQL query into component parts
        
        Args:
            sql_text: SQL query text
            
        Returns:
            List of SQL tokens
        """
        return self.sql_tokens_pattern.findall(sql_text.lower())
    
    async def get_query_suggestions(
        self,
        user_id: int,
        server_id: Optional[str] = None,
        context: Optional[str] = None,
        limit: int = 5,
        db: Session = None
    ) -> List[Dict[str, Any]]:
        """
        Get query suggestions for a user
        
        Args:
            user_id: User ID
            server_id: Optional server ID for context
            context: Optional current query context
            limit: Maximum number of suggestions
            db: Database session
            
        Returns:
            List of query suggestions
        """
        # Check if we have cached suggestions
        cache_key = f"query_suggestions:{user_id}:{server_id or 'all'}"
        cached_suggestions = await cache_service.get(cache_key)
        
        if cached_suggestions and not context:
            # If no context provided, return cached suggestions
            return cached_suggestions[:limit]
        
        try:
            # Get user's query history
            if not db:
                # If no DB session provided, return cached or empty
                return cached_suggestions[:limit] if cached_suggestions else []
            
            # Query filters
            filters = [
                QueryHistory.user_id == user_id,
                QueryHistory.status == 'success'
            ]
            
            if server_id:
                filters.append(QueryHistory.server_id == server_id)
            
            # Get user's query history (last 30 days)
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            user_queries = db.query(QueryHistory) \
                .filter(*filters) \
                .filter(QueryHistory.executed_at > thirty_days_ago) \
                .order_by(QueryHistory.executed_at.desc()) \
                .limit(500) \
                .all()
            
            if not user_queries:
                logger.info(f"No query history found for user {user_id}")
                return []
            
            # Generate suggestions
            suggestions = await self._generate_suggestions(
                user_queries=user_queries,
                context=context,
                limit=limit
            )
            
            # Cache suggestions for 1 hour if no context
            if not context:
                await cache_service.set(cache_key, suggestions, ttl=3600)
            
            return suggestions
        
        except Exception as e:
            logger.error(f"Error getting query suggestions: {e}", exc_info=True)
            # Return cached suggestions as fallback
            return cached_suggestions[:limit] if cached_suggestions else []
    
    async def _generate_suggestions(
        self,
        user_queries: List[QueryHistory],
        context: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Generate query suggestions based on user history
        
        Args:
            user_queries: User's query history
            context: Optional current query context
            limit: Maximum number of suggestions
            
        Returns:
            List of query suggestions
        """
        if not user_queries:
            return []
        
        try:
            # If context is provided, find similar queries
            if context and len(context.strip()) > 3:
                return await self._get_context_based_suggestions(user_queries, context, limit)
            
            # Otherwise, return frequently used and recent queries
            return self._get_frequency_based_suggestions(user_queries, limit)
        
        except Exception as e:
            logger.error(f"Error generating suggestions: {e}", exc_info=True)
            return []
    
    async def _get_context_based_suggestions(
        self,
        user_queries: List[QueryHistory],
        context: str,
        limit: int
    ) -> List[Dict[str, Any]]:
        """
        Get context-based query suggestions
        
        Args:
            user_queries: User's query history
            context: Current query context
            limit: Maximum number of suggestions
            
        Returns:
            List of context-based suggestions
        """
        # Normalize context
        normalized_context = self._normalize_query(context)
        
        if not self.vectorizer:
            # Fallback to simple matching if vectorizer not available
            return self._get_simple_context_suggestions(user_queries, normalized_context, limit)
        
        try:
            # Get unique queries (avoid duplicates)
            unique_queries = {}
            for query in user_queries:
                normalized_sql = self._normalize_query(query.sql_text)
                if normalized_sql.startswith(normalized_context) and normalized_sql != normalized_context:
                    # Direct prefix matches get priority
                    unique_queries[normalized_sql] = {
                        "query": query,
                        "score": 0.95  # High score for prefix matches
                    }
                else:
                    unique_queries[normalized_sql] = {
                        "query": query,
                        "score": 0.0  # Will be updated with similarity score
                    }
            
            if not unique_queries:
                return []
            
            # Skip vectorization for very few queries
            if len(unique_queries) < 3:
                return [
                    {
                        "id": query_data["query"].id,
                        "sql_text": query_data["query"].sql_text,
                        "score": query_data["score"],
                        "type": "context",
                        "tables": self._extract_tables(query_data["query"].sql_text)
                    }
                    for query_data in sorted(
                        unique_queries.values(),
                        key=lambda x: x["score"],
                        reverse=True
                    )[:limit]
                ]
            
            # Convert to list of normalized SQL texts
            query_texts = list(unique_queries.keys())
            
            # Transform queries and context to TF-IDF vectors
            query_vectors = self.vectorizer.transform(query_texts)
            context_vector = self.vectorizer.transform([normalized_context])
            
            # Calculate cosine similarity between context and all queries
            similarities = cosine_similarity(context_vector, query_vectors).flatten()
            
            # Update scores in unique_queries
            for i, query_text in enumerate(query_texts):
                if similarities[i] > unique_queries[query_text]["score"]:
                    unique_queries[query_text]["score"] = float(similarities[i])
            
            # Sort by score and take top matches
            sorted_suggestions = sorted(
                unique_queries.values(),
                key=lambda x: x["score"],
                reverse=True
            )
            
            # Filter out low-scoring suggestions
            filtered_suggestions = [
                s for s in sorted_suggestions 
                if s["score"] >= self.similarity_threshold
            ][:limit]
            
            return [
                {
                    "id": suggestion["query"].id,
                    "sql_text": suggestion["query"].sql_text,
                    "score": suggestion["score"],
                    "type": "context",
                    "tables": self._extract_tables(suggestion["query"].sql_text)
                }
                for suggestion in filtered_suggestions
            ]
        
        except Exception as e:
            logger.error(f"Error in context-based suggestion: {e}", exc_info=True)
            return self._get_simple_context_suggestions(user_queries, normalized_context, limit)
    
    def _get_simple_context_suggestions(
        self,
        user_queries: List[QueryHistory],
        context: str,
        limit: int
    ) -> List[Dict[str, Any]]:
        """
        Get simple context suggestions using string matching
        
        Args:
            user_queries: User's query history
            context: Normalized query context
            limit: Maximum number of suggestions
            
        Returns:
            List of simple context suggestions
        """
        # Find queries that start with or contain the context
        prefix_matches = []
        contains_matches = []
        
        for query in user_queries:
            normalized_sql = self._normalize_query(query.sql_text)
            
            if normalized_sql.startswith(context) and normalized_sql != context:
                prefix_matches.append({
                    "query": query,
                    "score": 0.95  # High score for prefix matches
                })
            elif context in normalized_sql and normalized_sql != context:
                contains_matches.append({
                    "query": query,
                    "score": 0.7  # Lower score for contains matches
                })
        
        # Combine and limit results
        matches = (prefix_matches + contains_matches)[:limit]
        
        return [
            {
                "id": match["query"].id,
                "sql_text": match["query"].sql_text,
                "score": match["score"],
                "type": "context",
                "tables": self._extract_tables(match["query"].sql_text)
            }
            for match in matches
        ]
    
    def _get_frequency_based_suggestions(
        self,
        user_queries: List[QueryHistory],
        limit: int
    ) -> List[Dict[str, Any]]:
        """
        Get query suggestions based on frequency and recency
        
        Args:
            user_queries: User's query history
            limit: Maximum number of suggestions
            
        Returns:
            List of frequency-based suggestions
        """
        # Count query frequency
        query_frequency = {}
        query_recency = {}
        query_objects = {}
        
        for query in user_queries:
            normalized_sql = self._normalize_query(query.sql_text)
            
            # Skip very short queries
            if len(normalized_sql) < 10:
                continue
            
            # Update frequency
            query_frequency[normalized_sql] = query_frequency.get(normalized_sql, 0) + 1
            
            # Update recency (keep most recent timestamp)
            current_recency = query_recency.get(normalized_sql, datetime.min)
            if query.executed_at > current_recency:
                query_recency[normalized_sql] = query.executed_at
                query_objects[normalized_sql] = query
        
        # Calculate combined score (frequency and recency)
        now = datetime.utcnow()
        query_scores = {}
        
        for sql, freq in query_frequency.items():
            recency = query_recency[sql]
            days_old = (now - recency).days
            
            # Recency score decreases with age (1.0 for today, 0.0 for 30+ days old)
            recency_score = max(0, 1.0 - (days_old / 30.0))
            
            # Normalize frequency (cap at 10)
            freq_score = min(1.0, freq / 10.0)
            
            # Combined score (70% frequency, 30% recency)
            combined_score = (0.7 * freq_score) + (0.3 * recency_score)
            
            query_scores[sql] = combined_score
        
        # Sort by score and take top results
        top_queries = sorted(
            query_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )[:limit]
        
        return [
            {
                "id": query_objects[sql].id,
                "sql_text": query_objects[sql].sql_text,
                "score": score,
                "type": "frequent",
                "tables": self._extract_tables(query_objects[sql].sql_text)
            }
            for sql, score in top_queries
        ]
    
    def _extract_tables(self, sql_text: str) -> List[str]:
        """
        Extract table names from SQL query
        
        Args:
            sql_text: SQL query text
            
        Returns:
            List of table names
        """
        try:
            # Simple regex-based table extraction
            # This is a simplified approach and might not catch all cases
            from_pattern = re.compile(
                r'FROM\s+([a-zA-Z0-9_\.]+)(?:\s+(?:AS\s+)?([a-zA-Z0-9_]+))?|'
                r'JOIN\s+([a-zA-Z0-9_\.]+)(?:\s+(?:AS\s+)?([a-zA-Z0-9_]+))?',
                re.IGNORECASE
            )
            
            tables = []
            for match in from_pattern.finditer(sql_text):
                # FROM clause
                if match.group(1):
                    tables.append(match.group(1))
                # JOIN clause
                elif match.group(3):
                    tables.append(match.group(3))
            
            return list(set(tables))  # Remove duplicates
        
        except Exception as e:
            logger.error(f"Error extracting tables: {e}", exc_info=True)
            return []
    
    async def get_table_suggestions(
        self,
        user_id: int,
        server_id: str,
        db: Session
    ) -> List[Dict[str, Any]]:
        """
        Get table usage suggestions for a user
        
        Args:
            user_id: User ID
            server_id: Server ID
            db: Database session
            
        Returns:
            List of table suggestions
        """
        try:
            # Get user's query history for this server
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            user_queries = db.query(QueryHistory) \
                .filter(QueryHistory.user_id == user_id) \
                .filter(QueryHistory.server_id == server_id) \
                .filter(QueryHistory.status == 'success') \
                .filter(QueryHistory.executed_at > thirty_days_ago) \
                .all()
            
            if not user_queries:
                return []
            
            # Extract tables from all queries
            table_usage = {}
            for query in user_queries:
                tables = self._extract_tables(query.sql_text)
                
                for table in tables:
                    table_usage[table] = table_usage.get(table, 0) + 1
            
            # Sort by usage frequency
            sorted_tables = sorted(
                table_usage.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]  # Top 10 tables
            
            return [
                {
                    "table_name": table,
                    "frequency": freq,
                    "server_id": server_id
                }
                for table, freq in sorted_tables
            ]
        
        except Exception as e:
            logger.error(f"Error getting table suggestions: {e}", exc_info=True)
            return []
    
    async def get_completion_suggestions(
        self,
        partial_query: str,
        user_id: int,
        server_id: Optional[str] = None,
        db: Session = None
    ) -> List[Dict[str, Any]]:
        """
        Get code completion suggestions based on partial query
        
        Args:
            partial_query: Partial SQL query
            user_id: User ID
            server_id: Optional server ID
            db: Database session
            
        Returns:
            List of completion suggestions
        """
        try:
            # Get last SQL token from partial query
            tokens = self._tokenize_query(partial_query)
            current_token = tokens[-1] if tokens else ""
            
            # If we have a short token, return syntax suggestions
            if len(current_token) < 3:
                return self._get_syntax_suggestions(partial_query, current_token)
            
            # Get context-based suggestions
            context_suggestions = await self.get_query_suggestions(
                user_id=user_id,
                server_id=server_id,
                context=partial_query,
                limit=5,
                db=db
            )
            
            # Extract completion suggestions from context suggestions
            completions = []
            
            for suggestion in context_suggestions:
                sql = suggestion["sql_text"]
                
                # Find where the partial query ends in the suggestion
                idx = sql.lower().find(partial_query.lower())
                
                if idx >= 0:
                    remainder = sql[idx + len(partial_query):]
                    
                    # Extract next token or phrase
                    match = re.search(r'^\s*(\S+(?:\s+\S+){0,5})', remainder)
                    if match:
                        completion = match.group(1).strip()
                        if completion and len(completion) > 0:
                            completions.append({
                                "text": completion,
                                "score": suggestion["score"],
                                "type": "completion"
                            })
            
            # Add token-based suggestions
            token_suggestions = self._get_token_suggestions(current_token)
            
            # Combine and deduplicate
            combined_suggestions = completions + token_suggestions
            deduplicated = {}
            
            for suggestion in combined_suggestions:
                text = suggestion["text"]
                if text not in deduplicated or suggestion["score"] > deduplicated[text]["score"]:
                    deduplicated[text] = suggestion
            
            # Return top suggestions
            return list(deduplicated.values())[:5]
        
        except Exception as e:
            logger.error(f"Error getting completion suggestions: {e}", exc_info=True)
            return self._get_syntax_suggestions(partial_query, current_token if 'current_token' in locals() else "")
    
    def _get_syntax_suggestions(
        self,
        partial_query: str,
        current_token: str
    ) -> List[Dict[str, Any]]:
        """
        Get SQL syntax suggestions
        
        Args:
            partial_query: Partial SQL query
            current_token: Current token being typed
            
        Returns:
            List of syntax suggestions
        """
        # Common SQL keywords for suggestions
        keywords = {
            "": ["SELECT", "FROM", "WHERE", "JOIN", "GROUP BY", "ORDER BY", "HAVING", 
                 "INSERT INTO", "UPDATE", "DELETE FROM", "CREATE TABLE", "ALTER TABLE", 
                 "DROP TABLE", "TRUNCATE TABLE", "WITH"],
            
            "S": ["SELECT", "SET", "SUM(", "SUBSTRING("],
            "SE": ["SELECT", "SET"],
            "SEL": ["SELECT"],
            
            "F": ["FROM", "FULL JOIN", "FOREIGN KEY", "FUNCTION"],
            "FR": ["FROM"],
            "FRO": ["FROM"],
            
            "W": ["WHERE", "WITH", "WHEN", "WINDOW"],
            "WH": ["WHERE", "WHEN"],
            "WHE": ["WHERE"],
            
            "I": ["INSERT", "INTO", "IS NULL", "IS NOT NULL", "INNER JOIN"],
            "IN": ["INSERT", "INTO", "INNER JOIN", "IS NULL", "IS NOT NULL"],
            
            "J": ["JOIN"],
            "JO": ["JOIN"],
            
            "G": ["GROUP BY"],
            "GR": ["GROUP BY"],
            "GRO": ["GROUP BY"],
            
            "O": ["ORDER BY", "OFFSET", "ON"],
            "OR": ["ORDER BY", "OR"],
            
            "L": ["LEFT JOIN", "LIMIT", "LIKE"],
            "LI": ["LIKE", "LIMIT"],
            
            "U": ["UPDATE", "UNION", "USING"],
            "UP": ["UPDATE"],
            
            "C": ["CREATE", "COUNT(", "CASE", "CONVERT(", "CROSS JOIN"],
            "CR": ["CREATE"],
            "CRE": ["CREATE"],
            
            "A": ["ALTER", "AND", "AVG(", "ALL", "ASC"],
            "AL": ["ALTER", "ALL"],
            "ALT": ["ALTER"],
            
            "D": ["DELETE", "DROP", "DESC", "DISTINCT", "DEFAULT"],
            "DE": ["DELETE", "DESC", "DEFAULT"],
            "DEL": ["DELETE"],
            
            "T": ["TABLE", "TRUNCATE", "TOP", "TRIGGER"],
            "TA": ["TABLE"],
            
            "B": ["BY", "BETWEEN"],
            "BE": ["BETWEEN"],
            
            "H": ["HAVING"],
            "HA": ["HAVING"],
            
            "R": ["RIGHT JOIN", "ROLLBACK", "REPLACE", "REFERENCES"],
            "RI": ["RIGHT JOIN"],
            
            "K": ["KEY"],
            "KE": ["KEY"],
            
            "V": ["VALUES", "VIEW"],
            "VA": ["VALUES"],
            
            "M": ["MAX(", "MIN(", "MERGE"],
            "MA": ["MAX("],
            "MI": ["MIN("]
        }
        
        # Lowercase the token for case-insensitive matching
        token_lower = current_token.lower()
        
        # Get matching keywords
        suggestions = []
        
        if current_token in keywords:
            # Exact match for current_token
            suggestions = [
                {
                    "text": keyword,
                    "score": 0.9,
                    "type": "keyword"
                }
                for keyword in keywords[current_token]
            ]
        else:
            # Try to find suggestions for tokens that start with current_token
            matching_keywords = []
            
            for prefix, words in keywords.items():
                if prefix.lower().startswith(token_lower) or token_lower.startswith(prefix.lower()):
                    matching_keywords.extend(words)
            
            # Filter keywords that match the token
            suggestions = [
                {
                    "text": keyword,
                    "score": 0.8,
                    "type": "keyword"
                }
                for keyword in matching_keywords
                if keyword.lower().startswith(token_lower)
            ]
        
        return suggestions[:5]  # Limit to top 5
    
    def _get_token_suggestions(
        self,
        token: str
    ) -> List[Dict[str, Any]]:
        """
        Get token-based suggestions
        
        Args:
            token: Current token
            
        Returns:
            List of token-based suggestions
        """
        # Common SQL expressions and functions
        expressions = {
            # Aggregation functions
            "COUNT": ["COUNT(*)", "COUNT(DISTINCT column)"],
            "SUM": ["SUM(column)"],
            "AVG": ["AVG(column)"],
            "MIN": ["MIN(column)"],
            "MAX": ["MAX(column)"],
            
            # String functions
            "CONCAT": ["CONCAT(str1, str2)"],
            "SUBSTRING": ["SUBSTRING(column, start, length)"],
            "TRIM": ["TRIM(column)"],
            "UPPER": ["UPPER(column)"],
            "LOWER": ["LOWER(column)"],
            
            # Date functions
            "DATE": ["DATE(column)"],
            "DATEADD": ["DATEADD(day, 1, column)"],
            "DATEDIFF": ["DATEDIFF(day, start_date, end_date)"],
            "GETDATE": ["GETDATE()"],
            "CONVERT": ["CONVERT(VARCHAR, column, 120)"],
            
            # Numeric functions
            "ROUND": ["ROUND(column, 2)"],
            "CAST": ["CAST(column AS type)"],
            "COALESCE": ["COALESCE(column, 0)"],
            
            # Conditional expressions
            "CASE": ["CASE WHEN condition THEN result ELSE else_result END"],
            "IIF": ["IIF(condition, true_value, false_value)"],
            "NULLIF": ["NULLIF(column, 0)"],
            
            # Joins
            "JOIN": ["JOIN table ON table.column = other_table.column"],
            "LEFT": ["LEFT JOIN table ON condition"],
            "RIGHT": ["RIGHT JOIN table ON condition"],
            "INNER": ["INNER JOIN table ON condition"],
            
            # Common clauses
            "GROUP": ["GROUP BY column"],
            "ORDER": ["ORDER BY column DESC"],
            "HAVING": ["HAVING aggregate_function(column) > value"],
            "WHERE": ["WHERE column = value"],
            "LIMIT": ["LIMIT 10 OFFSET 0"]
        }
        
        # Check if token matches any keys in expressions
        suggestions = []
        
        for key, exprs in expressions.items():
            if key.startswith(token.upper()):
                for expr in exprs:
                    suggestions.append({
                        "text": expr,
                        "score": 0.7,
                        "type": "expression"
                    })
        
        return suggestions

# Initialize ML suggestions service
ml_suggestions_service = MLSuggestionsService()

# Start background analysis on app startup
def start_ml_analysis():
    ml_suggestions_service.start_background_analysis()

# Shutdown background analysis on app shutdown
def shutdown_ml_analysis():
    ml_suggestions_service.stop_background_analysis()

# Son güncelleme: 2025-05-21 07:25:48
# Güncelleyen: Teeksss