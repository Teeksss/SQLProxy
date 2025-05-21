"""
Machine Learning Query Suggestion Service for SQL Proxy

This module provides ML-powered SQL query suggestions based on 
historical queries and user patterns.

Last updated: 2025-05-21 07:20:45
Updated by: Teeksss
"""

import logging
import re
import json
import pickle
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import Counter
from sqlalchemy.orm import Session
import os
import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans
import joblib
import threading
import time

from app.models.user import User
from app.models.query import QueryHistory
from app.services.cache_service import cache_service
from app.core.config import settings

logger = logging.getLogger(__name__)

class MLQuerySuggestionService:
    """
    Service for providing ML-powered SQL query suggestions
    
    Uses machine learning to analyze query patterns and suggest
    SQL queries based on user history and context.
    """
    
    def __init__(self):
        """Initialize ML query suggestion service"""
        self.model_path = "app/ml_models"
        self.vectorizer = None
        self.kmeans = None
        self.query_embeddings = {}
        self.user_clusters = {}
        self.last_training_time = None
        self.training_interval = timedelta(hours=24)  # Train once a day
        self.training_lock = threading.Lock()
        self.min_training_queries = 50
        self.initialized = False
        
        # Create model directory if it doesn't exist
        os.makedirs(self.model_path, exist_ok=True)
        
        # Try to load existing models
        self._load_models()
    
    def _load_models(self):
        """Load trained models if they exist"""
        try:
            vectorizer_path = os.path.join(self.model_path, "tfidf_vectorizer.pkl")
            kmeans_path = os.path.join(self.model_path, "kmeans_model.pkl")
            embeddings_path = os.path.join(self.model_path, "query_embeddings.pkl")
            user_clusters_path = os.path.join(self.model_path, "user_clusters.pkl")
            
            if (os.path.exists(vectorizer_path) and
                os.path.exists(kmeans_path) and
                os.path.exists(embeddings_path) and
                os.path.exists(user_clusters_path)):
                
                self.vectorizer = joblib.load(vectorizer_path)
                self.kmeans = joblib.load(kmeans_path)
                self.query_embeddings = joblib.load(embeddings_path)
                self.user_clusters = joblib.load(user_clusters_path)
                
                # Get the last modified time of the kmeans model as the last training time
                self.last_training_time = datetime.fromtimestamp(os.path.getmtime(kmeans_path))
                self.initialized = True
                
                logger.info("ML query suggestion models loaded successfully")
                return True
        except Exception as e:
            logger.error(f"Error loading ML models: {e}", exc_info=True)
            
        return False
    
    def _save_models(self):
        """Save trained models to disk"""
        try:
            joblib.dump(self.vectorizer, os.path.join(self.model_path, "tfidf_vectorizer.pkl"))
            joblib.dump(self.kmeans, os.path.join(self.model_path, "kmeans_model.pkl"))
            joblib.dump(self.query_embeddings, os.path.join(self.model_path, "query_embeddings.pkl"))
            joblib.dump(self.user_clusters, os.path.join(self.model_path, "user_clusters.pkl"))
            
            logger.info("ML query suggestion models saved successfully")
            return True
        except Exception as e:
            logger.error(f"Error saving ML models: {e}", exc_info=True)
            return False
    
    async def get_query_suggestions(
        self,
        user_id: int,
        server_id: Optional[str] = None,
        current_query: Optional[str] = None,
        limit: int = 5,
        db: Optional[Session] = None
    ) -> List[Dict[str, Any]]:
        """
        Get query suggestions for a user
        
        Args:
            user_id: User ID
            server_id: Optional server ID for context
            current_query: Optional current query being typed
            limit: Maximum number of suggestions to return
            db: Database session
            
        Returns:
            List of query suggestions
        """
        # Check if models need training
        await self._check_training_needed(db)
        
        # If ML models not ready, fall back to basic suggestions
        if not self.initialized:
            return await self._get_basic_suggestions(
                user_id=user_id,
                server_id=server_id,
                current_query=current_query,
                limit=limit,
                db=db
            )
        
        try:
            # Try to use ML suggestions with fallback to basic
            ml_suggestions = await self._get_ml_suggestions(
                user_id=user_id,
                server_id=server_id,
                current_query=current_query,
                limit=limit
            )
            
            # If we got less than the requested limit, add basic suggestions
            if len(ml_suggestions) < limit and db:
                basic_suggestions = await self._get_basic_suggestions(
                    user_id=user_id,
                    server_id=server_id,
                    current_query=current_query,
                    limit=limit - len(ml_suggestions),
                    db=db
                )
                
                # Filter out duplicates
                combined_suggestions = ml_suggestions.copy()
                for suggestion in basic_suggestions:
                    if suggestion["sql_text"] not in [s["sql_text"] for s in combined_suggestions]:
                        combined_suggestions.append(suggestion)
                
                return combined_suggestions[:limit]
            
            return ml_suggestions
        except Exception as e:
            logger.error(f"Error getting ML query suggestions: {e}", exc_info=True)
            
            # Fall back to basic suggestions
            if db:
                return await self._get_basic_suggestions(
                    user_id=user_id,
                    server_id=server_id,
                    current_query=current_query,
                    limit=limit,
                    db=db
                )
            
            return []
    
    async def _get_ml_suggestions(
        self,
        user_id: int,
        server_id: Optional[str] = None,
        current_query: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get ML-powered query suggestions
        
        Args:
            user_id: User ID
            server_id: Optional server ID for context
            current_query: Optional current query being typed
            limit: Maximum number of suggestions to return
            
        Returns:
            List of ML-powered query suggestions
        """
        suggestions = []
        
        # Get user's cluster if available
        user_cluster = self.user_clusters.get(user_id)
        
        # If current query is provided, use it to find similar queries
        if current_query and len(current_query.strip()) > 5:
            # Preprocess query
            processed_query = self._preprocess_query(current_query)
            
            # Vectorize the query
            query_vector = self.vectorizer.transform([processed_query])
            
            # Find similar queries
            similarities = []
            for query_id, embedding in self.query_embeddings.items():
                # Only consider embeddings from queries with the same server_id if provided
                query_server_id = query_id.split("_")[1] if "_" in query_id else None
                if server_id and query_server_id and query_server_id != server_id:
                    continue
                
                # Calculate similarity
                similarity = cosine_similarity(query_vector, embedding).item()
                similarities.append((query_id, similarity))
            
            # Sort by similarity
            similarities.sort(key=lambda x: x[1], reverse=True)
            
            # Add top similar queries to suggestions
            for query_id, similarity in similarities[:limit]:
                parts = query_id.split("_", 2)
                if len(parts) < 3:
                    continue
                    
                query_user_id = int(parts[0])
                query_server_id = parts[1]
                query_text = parts[2]
                
                # Don't suggest the exact same query
                if current_query.strip().lower() == query_text.strip().lower():
                    continue
                
                suggestions.append({
                    "sql_text": query_text,
                    "similarity": similarity,
                    "source": "similar_query",
                    "server_id": query_server_id,
                    "relevance_score": similarity * 100  # Convert to 0-100 scale
                })
        
        # If we need more suggestions and user has a cluster, recommend from cluster
        if len(suggestions) < limit and user_cluster is not None:
            # Get cluster queries
            cluster_queries = []
            for query_id, embedding in self.query_embeddings.items():
                parts = query_id.split("_", 2)
                if len(parts) < 3:
                    continue
                    
                query_user_id = int(parts[0])
                query_server_id = parts[1]
                query_text = parts[2]
                
                # Only consider queries from the same server if specified
                if server_id and query_server_id != server_id:
                    continue
                
                # Get this query's cluster
                query_vector = self.query_embeddings[query_id]
                query_cluster = self.kmeans.predict(query_vector)[0]
                
                # If query is in the same cluster as the user
                if query_cluster == user_cluster:
                    # Don't duplicate suggestions
                    if query_text not in [s["sql_text"] for s in suggestions]:
                        cluster_queries.append({
                            "sql_text": query_text,
                            "source": "user_cluster",
                            "server_id": query_server_id,
                            "relevance_score": 75  # High relevance for cluster-based suggestions
                        })
            
            # Add cluster queries to suggestions (prioritize other users' queries)
            for query in cluster_queries:
                if len(suggestions) >= limit:
                    break
                suggestions.append(query)
        
        # Sort by relevance_score
        suggestions.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
        
        return suggestions[:limit]
    
    async def _get_basic_suggestions(
        self,
        user_id: int,
        server_id: Optional[str] = None,
        current_query: Optional[str] = None,
        limit: int = 5,
        db: Session = None
    ) -> List[Dict[str, Any]]:
        """
        Get basic (non-ML) query suggestions
        
        Args:
            user_id: User ID
            server_id: Optional server ID for context
            current_query: Optional current query being typed
            limit: Maximum number of suggestions to return
            db: Database session
            
        Returns:
            List of basic query suggestions
        """
        if not db:
            return []
        
        suggestions = []
        
        # Build query
        query = db.query(QueryHistory).filter(QueryHistory.user_id == user_id)
        
        # Add server filter if provided
        if server_id:
            query = query.filter(QueryHistory.server_id == server_id)
        
        # Add status filter
        query = query.filter(QueryHistory.status == "success")
        
        # Get user's recent successful queries
        recent_queries = query.order_by(QueryHistory.executed_at.desc()).limit(20).all()
        
        # Process recent queries
        for history_item in recent_queries:
            # Skip if suggestion already exists
            if history_item.sql_text in [s["sql_text"] for s in suggestions]:
                continue
            
            # Add suggestion
            suggestions.append({
                "sql_text": history_item.sql_text,
                "source": "recent_query",
                "server_id": history_item.server_id,
                "relevance_score": 50  # Medium relevance for recent queries
            })
            
            # Break if we have enough suggestions
            if len(suggestions) >= limit:
                break
        
        # If current query is provided and we need more suggestions, try to suggest completions
        if current_query and len(suggestions) < limit:
            # Simplified SQL completion suggestions
            common_clauses = [
                "SELECT * FROM",
                "WHERE",
                "GROUP BY",
                "ORDER BY",
                "INNER JOIN",
                "LEFT JOIN",
                "RIGHT JOIN",
                "HAVING",
                "LIMIT",
                "OFFSET",
                "WITH"
            ]
            
            current_query_lower = current_query.lower()
            
            for clause in common_clauses:
                clause_lower = clause.lower()
                
                # If the clause is not in the query but would be a relevant next part
                if clause_lower not in current_query_lower:
                    # Check if this would be a logical next clause
                    if (clause_lower == "where" and "from" in current_query_lower or
                        clause_lower == "group by" and "where" in current_query_lower or
                        clause_lower == "having" and "group by" in current_query_lower or
                        clause_lower == "order by" and ("where" in current_query_lower or "group by" in current_query_lower) or
                        clause_lower == "limit" and "order by" in current_query_lower):
                        
                        suggestion_text = f"{current_query} {clause} "
                        
                        # Add completion suggestion
                        suggestions.append({
                            "sql_text": suggestion_text,
                            "source": "completion",
                            "relevance_score": 40  # Lower relevance for basic completions
                        })
                        
                        # Break if we have enough suggestions
                        if len(suggestions) >= limit:
                            break
        
        # Sort by relevance_score
        suggestions.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
        
        return suggestions[:limit]
    
    async def _check_training_needed(self, db: Optional[Session]):
        """
        Check if model training is needed and trigger if necessary
        
        Args:
            db: Database session
        """
        # Skip if no DB session provided
        if not db:
            return
        
        # Check if models exist and are recent enough
        if (self.last_training_time is None or 
            datetime.utcnow() - self.last_training_time > self.training_interval):
            
            # Check if there are enough queries to train
            query_count = db.query(QueryHistory).count()
            
            if query_count >= self.min_training_queries:
                # Train in a separate thread to avoid blocking
                thread = threading.Thread(target=self._train_models_async, args=(db,))
                thread.daemon = True
                thread.start()
    
    def _train_models_async(self, db: Session):
        """
        Train models asynchronously
        
        Args:
            db: Database session
        """
        # Use a lock to prevent multiple simultaneous trainings
        if not self.training_lock.acquire(blocking=False):
            logger.info("Model training already in progress")
            return
        
        try:
            # Create a new session for this thread
            from app.db.session import SessionLocal
            thread_db = SessionLocal()
            
            try:
                # Perform training
                logger.info("Starting ML model training")
                self._train_models(thread_db)
                logger.info("ML model training completed")
            finally:
                thread_db.close()
        except Exception as e:
            logger.error(f"Error in async model training: {e}", exc_info=True)
        finally:
            self.training_lock.release()
    
    def _train_models(self, db: Session):
        """
        Train the ML models
        
        Args:
            db: Database session
        """
        try:
            # Get successful queries from the past year
            one_year_ago = datetime.utcnow() - timedelta(days=365)
            query_history = db.query(QueryHistory).filter(
                QueryHistory.status == "success",
                QueryHistory.executed_at >= one_year_ago
            ).all()
            
            if len(query_history) < self.min_training_queries:
                logger.info(f"Not enough queries for training: {len(query_history)} < {self.min_training_queries}")
                return
            
            # Prepare data
            queries = []
            query_ids = []
            user_ids = []
            
            for item in query_history:
                # Process query text
                processed_query = self._preprocess_query(item.sql_text)
                
                # Skip if query is too short after processing
                if len(processed_query.split()) < 3:
                    continue
                
                queries.append(processed_query)
                query_ids.append(f"{item.user_id}_{item.server_id}_{item.sql_text}")
                user_ids.append(item.user_id)
            
            if len(queries) < self.min_training_queries:
                logger.info(f"Not enough valid queries for training: {len(queries)} < {self.min_training_queries}")
                return
            
            # Create and fit TF-IDF vectorizer
            self.vectorizer = TfidfVectorizer(
                analyzer='word',
                lowercase=True,
                max_features=1000,
                stop_words='english'
            )
            query_vectors = self.vectorizer.fit_transform(queries)
            
            # Store embeddings
            self.query_embeddings = {}
            for i, query_id in enumerate(query_ids):
                self.query_embeddings[query_id] = query_vectors[i]
            
            # Train KMeans clustering
            num_clusters = min(10, len(queries) // 5)  # Limit to 10 clusters or 1/5 of data size
            self.kmeans = KMeans(n_clusters=num_clusters, random_state=42)
            self.kmeans.fit(query_vectors)
            
            # Assign users to clusters based on their queries
            user_clusters = {}
            user_vectors = {}
            
            for i, user_id in enumerate(user_ids):
                if user_id not in user_vectors:
                    user_vectors[user_id] = []
                user_vectors[user_id].append(query_vectors[i])
            
            for user_id, vectors in user_vectors.items():
                # Create a centroid for this user's queries
                if len(vectors) == 1:
                    user_centroid = vectors[0]
                else:
                    user_centroid = np.mean(vectors, axis=0)
                
                # Assign to the nearest cluster
                user_cluster = self.kmeans.predict(user_centroid)[0]
                user_clusters[user_id] = user_cluster
            
            self.user_clusters = user_clusters
            
            # Save the trained models
            self._save_models()
            
            # Update training time
            self.last_training_time = datetime.utcnow()
            self.initialized = True
            
            logger.info(f"ML model training completed with {len(queries)} queries and {num_clusters} clusters")
        except Exception as e:
            logger.error(f"Error training ML models: {e}", exc_info=True)
    
    def _preprocess_query(self, query: str) -> str:
        """
        Preprocess SQL query for ML analysis
        
        Args:
            query: SQL query text
            
        Returns:
            Preprocessed query
        """
        # Convert to lowercase
        query = query.lower()
        
        # Remove comments
        query = re.sub(r'--.*?$', ' ', query, flags=re.MULTILINE)  # Single-line comments
        query = re.sub(r'/\*.*?\*/', ' ', query, flags=re.DOTALL)  # Multi-line comments
        
        # Remove string literals
        query = re.sub(r"'.*?'", "'STRING_LITERAL'", query)
        query = re.sub(r'".*?"', '"STRING_LITERAL"', query)
        
        # Remove numbers
        query = re.sub(r'\b\d+\b', 'NUMBER', query)
        
        # Replace newlines and extra whitespace
        query = re.sub(r'\s+', ' ', query)
        
        # Normalize SQL keywords
        keywords = [
            "SELECT", "FROM", "WHERE", "GROUP BY", "ORDER BY", "HAVING",
            "INNER JOIN", "LEFT JOIN", "RIGHT JOIN", "FULL JOIN", "JOIN",
            "UNION", "INTERSECT", "EXCEPT", "WITH", "INSERT", "UPDATE", "DELETE",
            "CREATE", "ALTER", "DROP", "TRUNCATE", "GRANT", "REVOKE", "COMMIT", "ROLLBACK"
        ]
        
        normalized_query = query
        for keyword in keywords:
            pattern = r'\b' + keyword.lower() + r'\b'
            normalized_query = re.sub(pattern, keyword, normalized_query)
        
        return normalized_query.strip()
    
    async def track_query_execution(
        self,
        query_history_item: QueryHistory,
        db: Session
    ) -> None:
        """
        Track query execution for future suggestions
        
        Args:
            query_history_item: Query history item
            db: Database session
        """
        # Check if we need to retrain the models
        await self._check_training_needed(db)
        
        # If the models are initialized, we can update query embeddings
        if self.initialized and query_history_item.status == "success":
            try:
                # Process query
                processed_query = self._preprocess_query(query_history_item.sql_text)
                
                # Skip if query is too short after processing
                if len(processed_query.split()) < 3:
                    return
                
                # Vectorize the query
                query_vector = self.vectorizer.transform([processed_query])
                
                # Create query ID
                query_id = f"{query_history_item.user_id}_{query_history_item.server_id}_{query_history_item.sql_text}"
                
                # Store embedding
                self.query_embeddings[query_id] = query_vector
                
                # Update user's cluster
                if query_history_item.user_id not in self.user_clusters:
                    # Assign to a cluster
                    user_cluster = self.kmeans.predict(query_vector)[0]
                    self.user_clusters[query_history_item.user_id] = user_cluster
            except Exception as e:
                logger.error(f"Error tracking query execution: {e}", exc_info=True)

# Initialize ML query suggestion service
ml_query_suggestion_service = MLQuerySuggestionService()

# Son güncelleme: 2025-05-21 07:20:45
# Güncelleyen: Teeksss