"""
Distributed Query Engine for SQL Proxy

This module provides distributed query processing capabilities,
allowing SQL queries to be executed across multiple database instances
for improved performance and scalability.

Last updated: 2025-05-20 10:25:32
Updated by: Teeksss
"""

import logging
import time
import threading
import asyncio
import uuid
import json
from typing import List, Dict, Any, Optional, Tuple, Union, Set
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from sqlalchemy.orm import Session

from app.models.server import ServerConfig, ServerGroup
from app.models.query import AuditLog
from app.core.config import settings
from app.services.db_connector import db_connector_service
from app.services.query_router import query_router
from app.utils.query_parser import parse_query, get_query_type

logger = logging.getLogger(__name__)

class DistributedQueryEngine:
    """
    Distributed Query Engine for executing queries across multiple databases
    
    This engine provides:
    - Query distribution across server groups
    - Query splitting and parallel execution
    - Result aggregation
    - Load balancing
    - Failover handling
    """
    
    def __init__(self):
        """Initialize the distributed query engine"""
        self.executor = ThreadPoolExecutor(max_workers=settings.DISTRIBUTED_MAX_WORKERS)
        self.active_queries = {}
        self.server_stats = {}
        self.lock = threading.RLock()
        
        logger.info("Distributed Query Engine initialized")
    
    async def execute_distributed_query(
        self,
        query: str,
        server_group: str,
        username: str,
        user_role: str,
        params: Optional[Dict[str, Any]] = None,
        timeout: int = 60,
        db: Session = None
    ) -> Dict[str, Any]:
        """
        Execute a query across multiple servers in a server group
        
        Args:
            query: SQL query to execute
            server_group: Server group to execute query on
            username: Username executing the query
            user_role: Role of the user
            params: Query parameters
            timeout: Query timeout in seconds
            db: Database session
            
        Returns:
            Query results
        """
        if not db:
            logger.error("Database session required for distributed query execution")
            return {"error": "Internal error: No database session"}
        
        try:
            # Parse query to determine if it can be distributed
            query_info = parse_query(query)
            query_type = query_info.get("query_type", "unknown").upper()
            
            # Get server group information
            group = db.query(ServerGroup).filter(
                ServerGroup.group_name == server_group,
                ServerGroup.is_active == True
            ).first()
            
            if not group:
                return {
                    "error": f"Server group not found: {server_group}"
                }
            
            # Get servers in the group
            servers = self._get_active_servers_in_group(group.id, db)
            
            if not servers:
                return {
                    "error": f"No active servers found in group: {server_group}"
                }
            
            # Generate unique ID for this distributed query
            query_id = str(uuid.uuid4())
            
            # Log the distributed query
            log_entry = AuditLog(
                query_text=query,
                query_type=query_type,
                username=username,
                user_role=user_role,
                target_server=f"group:{server_group}",
                client_ip="internal",  # This would be replaced with the actual client IP
                query_params=params,
                execution_status="pending",
                is_distributed=True,
                distributed_id=query_id
            )
            
            db.add(log_entry)
            db.commit()
            db.refresh(log_entry)
            
            # Track the query
            with self.lock:
                self.active_queries[query_id] = {
                    "query": query,
                    "server_group": server_group,
                    "username": username,
                    "start_time": time.time(),
                    "timeout": timeout,
                    "status": "running",
                    "servers": [s.server_alias for s in servers],
                    "completed": set(),
                    "failed": set(),
                    "log_id": log_entry.id
                }
            
            # Determine distribution strategy based on query type
            if query_type == "SELECT":
                result = await self._distribute_select_query(
                    query_id, query, params, servers, timeout
                )
            elif query_type in ["INSERT", "UPDATE", "DELETE"]:
                result = await self._distribute_write_query(
                    query_id, query, params, servers, timeout
                )
            else:
                result = await self._distribute_general_query(
                    query_id, query, params, servers, timeout
                )
            
            # Update the log entry with results
            self._update_audit_log(
                log_entry.id,
                result.get("success", False),
                result.get("error", None),
                result.get("rowcount", 0),
                db
            )
            
            # Remove the query from active queries
            with self.lock:
                if query_id in self.active_queries:
                    del self.active_queries[query_id]
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing distributed query: {str(e)}")
            return {
                "error": f"Error executing distributed query: {str(e)}",
                "success": False
            }
    
    async def _distribute_select_query(
        self,
        query_id: str,
        query: str,
        params: Dict[str, Any],
        servers: List[ServerConfig],
        timeout: int
    ) -> Dict[str, Any]:
        """
        Distribute a SELECT query across multiple servers
        
        Args:
            query_id: Unique ID for this distributed query
            query: SQL query to execute
            params: Query parameters
            servers: List of servers to execute on
            timeout: Query timeout in seconds
            
        Returns:
            Aggregated query results
        """
        # For SELECT queries, we can either:
        # 1. Send the same query to all servers and pick the first result (for redundancy)
        # 2. Send the query to one server based on load balancing
        # 3. Split the query and aggregate results (more complex)
        
        # For simplicity, we'll use approach #2 - load balanced execution
        selected_server = self._select_server_by_load(servers)
        
        # Execute query on selected server
        try:
            server_result = await self._execute_on_server(
                query_id, selected_server, query, params, timeout
            )
            
            if server_result.get("error"):
                # If primary fails, try another server
                servers.remove(selected_server)
                if servers:
                    backup_server = self._select_server_by_load(servers)
                    logger.info(f"Primary server failed, trying backup: {backup_server.server_alias}")
                    
                    server_result = await self._execute_on_server(
                        query_id, backup_server, query, params, timeout
                    )
            
            # Mark query as completed for this server
            with self.lock:
                if query_id in self.active_queries:
                    if server_result.get("error"):
                        self.active_queries[query_id]["failed"].add(selected_server.server_alias)
                    else:
                        self.active_queries[query_id]["completed"].add(selected_server.server_alias)
            
            # Return the result
            return {
                "success": not server_result.get("error"),
                "error": server_result.get("error"),
                "data": server_result.get("data", []),
                "columns": server_result.get("columns", []),
                "rowcount": server_result.get("rowcount", 0),
                "execution_time": server_result.get("execution_time", 0),
                "server": selected_server.server_alias,
                "is_distributed": True,
                "distribution_info": {
                    "strategy": "load_balanced",
                    "servers_total": len(servers) + 1,  # Including the removed server
                    "servers_used": 1,
                    "query_id": query_id
                }
            }
            
        except Exception as e:
            logger.error(f"Error in distributed SELECT query: {str(e)}")
            return {
                "success": False,
                "error": f"Error in distributed query execution: {str(e)}",
                "is_distributed": True,
                "distribution_info": {
                    "strategy": "load_balanced",
                    "servers_total": len(servers) + 1,
                    "servers_used": 0,
                    "query_id": query_id
                }
            }
    
    async def _distribute_write_query(
        self,
        query_id: str,
        query: str,
        params: Dict[str, Any],
        servers: List[ServerConfig],
        timeout: int
    ) -> Dict[str, Any]:
        """
        Distribute a write query (INSERT, UPDATE, DELETE) across multiple servers
        
        Args:
            query_id: Unique ID for this distributed query
            query: SQL query to execute
            params: Query parameters
            servers: List of servers to execute on
            timeout: Query timeout in seconds
            
        Returns:
            Aggregated query results
        """
        # For write queries, we need to send the query to all servers
        # to keep them in sync
        
        # Execute queries in parallel
        tasks = []
        for server in servers:
            tasks.append(
                self._execute_on_server(query_id, server, query, params, timeout)
            )
        
        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        success_count = 0
        error_count = 0
        error_messages = []
        affected_rows = 0
        execution_time = 0
        
        for i, result in enumerate(results):
            server = servers[i]
            
            # Handle exceptions
            if isinstance(result, Exception):
                error_count += 1
                error_messages.append(f"{server.server_alias}: {str(result)}")
                
                with self.lock:
                    if query_id in self.active_queries:
                        self.active_queries[query_id]["failed"].add(server.server_alias)
                continue
            
            # Handle errors
            if result.get("error"):
                error_count += 1
                error_messages.append(f"{server.server_alias}: {result['error']}")
                
                with self.lock:
                    if query_id in self.active_queries:
                        self.active_queries[query_id]["failed"].add(server.server_alias)
                continue
            
            # Track successful execution
            success_count += 1
            affected_rows += result.get("rowcount", 0)
            execution_time = max(execution_time, result.get("execution_time", 0))
            
            with self.lock:
                if query_id in self.active_queries:
                    self.active_queries[query_id]["completed"].add(server.server_alias)
        
        # Determine overall success based on configured policy
        min_success_servers = max(1, len(servers) // 2)  # At least half of servers must succeed
        overall_success = success_count >= min_success_servers
        
        # Construct response
        response = {
            "success": overall_success,
            "error": "\n".join(error_messages) if error_messages else None,
            "rowcount": affected_rows // success_count if success_count > 0 else 0,
            "execution_time": execution_time,
            "is_distributed": True,
            "distribution_info": {
                "strategy": "all_servers",
                "servers_total": len(servers),
                "servers_succeeded": success_count,
                "servers_failed": error_count,
                "query_id": query_id
            }
        }
        
        return response
    
    async def _distribute_general_query(
        self,
        query_id: str,
        query: str,
        params: Dict[str, Any],
        servers: List[ServerConfig],
        timeout: int
    ) -> Dict[str, Any]:
        """
        Distribute a general query (non-SELECT, non-write) across servers
        
        Args:
            query_id: Unique ID for this distributed query
            query: SQL query to execute
            params: Query parameters
            servers: List of servers to execute on
            timeout: Query timeout in seconds
            
        Returns:
            Query results
        """
        # For general queries (DDL, etc.), we'll execute on all servers
        # Similar to write queries
        
        # Execute queries in parallel
        tasks = []
        for server in servers:
            tasks.append(
                self._execute_on_server(query_id, server, query, params, timeout)
            )
        
        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results (similar to write queries)
        success_count = 0
        error_count = 0
        error_messages = []
        execution_time = 0
        
        for i, result in enumerate(results):
            server = servers[i]
            
            # Handle exceptions
            if isinstance(result, Exception):
                error_count += 1
                error_messages.append(f"{server.server_alias}: {str(result)}")
                
                with self.lock:
                    if query_id in self.active_queries:
                        self.active_queries[query_id]["failed"].add(server.server_alias)
                continue
            
            # Handle errors
            if result.get("error"):
                error_count += 1
                error_messages.append(f"{server.server_alias}: {result['error']}")
                
                with self.lock:
                    if query_id in self.active_queries:
                        self.active_queries[query_id]["failed"].add(server.server_alias)
                continue
            
            # Track successful execution
            success_count += 1
            execution_time = max(execution_time, result.get("execution_time", 0))
            
            with self.lock:
                if query_id in self.active_queries:
                    self.active_queries[query_id]["completed"].add(server.server_alias)
        
        # Determine overall success
        min_success_servers = max(1, len(servers) // 2)  # At least half of servers must succeed
        overall_success = success_count >= min_success_servers
        
        # Construct response
        response = {
            "success": overall_success,
            "error": "\n".join(error_messages) if error_messages else None,
            "execution_time": execution_time,
            "is_distributed": True,
            "distribution_info": {
                "strategy": "all_servers",
                "servers_total": len(servers),
                "servers_succeeded": success_count,
                "servers_failed": error_count,
                "query_id": query_id
            }
        }
        
        return response
    
    async def _execute_on_server(
        self,
        query_id: str,
        server: ServerConfig,
        query: str,
        params: Dict[str, Any],
        timeout: int
    ) -> Dict[str, Any]:
        """
        Execute a query on a specific server
        
        Args:
            query_id: Unique ID for this distributed query
            server: Server to execute on
            query: SQL query to execute
            params: Query parameters
            timeout: Query timeout in seconds
            
        Returns:
            Query results
        """
        # Update server stats for load balancing
        with self.lock:
            if server.server_alias not in self.server_stats:
                self.server_stats[server.server_alias] = {
                    "active_queries": 0,
                    "total_queries": 0,
                    "total_time": 0,
                    "errors": 0,
                    "last_error_time": None
                }
            
            self.server_stats[server.server_alias]["active_queries"] += 1
            self.server_stats[server.server_alias]["total_queries"] += 1
        
        try:
            # Execute query using db connector service
            start_time = time.time()
            result = await db_connector_service.execute_query(
                query=query,
                server_alias=server.server_alias,
                params=params,
                timeout=timeout
            )
            execution_time = time.time() - start_time
            
            # Update server stats
            with self.lock:
                self.server_stats[server.server_alias]["active_queries"] -= 1
                self.server_stats[server.server_alias]["total_time"] += execution_time
                
                if result.get("error"):
                    self.server_stats[server.server_alias]["errors"] += 1
                    self.server_stats[server.server_alias]["last_error_time"] = time.time()
            
            # Add execution time to result
            result["execution_time"] = execution_time
            
            return result
            
        except Exception as e:
            # Update server stats
            with self.lock:
                self.server_stats[server.server_alias]["active_queries"] -= 1
                self.server_stats[server.server_alias]["errors"] += 1
                self.server_stats[server.server_alias]["last_error_time"] = time.time()
            
            # Propagate the exception
            raise
    
    def _select_server_by_load(self, servers: List[ServerConfig]) -> ServerConfig:
        """
        Select a server based on load balancing
        
        Args:
            servers: List of available servers
            
        Returns:
            Selected server
        """
        if not servers:
            raise ValueError("No servers available")
        
        if len(servers) == 1:
            return servers[0]
        
        # Calculate a score for each server based on current load
        server_scores = []
        
        with self.lock:
            for server in servers:
                alias = server.server_alias
                
                # Initialize stats if not present
                if alias not in self.server_stats:
                    self.server_stats[alias] = {
                        "active_queries": 0,
                        "total_queries": 0,
                        "total_time": 0,
                        "errors": 0,
                        "last_error_time": None
                    }
                
                stats = self.server_stats[alias]
                
                # Calculate a score (lower is better)
                # - Active queries: More active queries = higher score
                # - Error rate: More errors = higher score
                # - Recent errors: More recent errors = higher score
                
                active_score = stats["active_queries"] * 10
                
                error_rate = stats["errors"] / max(stats["total_queries"], 1) * 100
                error_score = error_rate * 5
                
                recency_score = 0
                if stats["last_error_time"]:
                    seconds_since_error = time.time() - stats["last_error_time"]
                    if seconds_since_error < 300:  # 5 minutes
                        recency_score = (300 - seconds_since_error) / 30
                
                total_score = active_score + error_score + recency_score
                
                server_scores.append((server, total_score))
        
        # Sort by score (lower is better)
        server_scores.sort(key=lambda x: x[1])
        
        # Return the server with the lowest score
        return server_scores[0][0]
    
    def _get_active_servers_in_group(
        self, 
        group_id: int, 
        db: Session
    ) -> List[ServerConfig]:
        """
        Get all active servers in a server group
        
        Args:
            group_id: ID of the server group
            db: Database session
            
        Returns:
            List of active servers in the group
        """
        # Query servers in the group
        servers = db.query(ServerConfig).filter(
            ServerConfig.group_id == group_id,
            ServerConfig.is_active == True
        ).all()
        
        return servers
    
    def _update_audit_log(
        self,
        log_id: int,
        success: bool,
        error: Optional[str],
        rowcount: int,
        db: Session
    ) -> None:
        """
        Update the audit log with execution results
        
        Args:
            log_id: ID of the audit log entry
            success: Whether the query was successful
            error: Error message, if any
            rowcount: Number of affected rows
            db: Database session
        """
        try:
            # Get the log entry
            log_entry = db.query(AuditLog).filter(AuditLog.id == log_id).first()
            
            if not log_entry:
                logger.error(f"Audit log entry not found: {log_id}")
                return
            
            # Update the log entry
            log_entry.execution_status = "success" if success else "error"
            log_entry.error_message = error
            log_entry.rowcount = rowcount
            log_entry.completed_at = datetime.utcnow()
            
            # Calculate execution time
            if log_entry.created_at:
                execution_time = (datetime.utcnow() - log_entry.created_at).total_seconds() * 1000
                log_entry.execution_time_ms = execution_time
            
            db.commit()
            
        except Exception as e:
            logger.error(f"Error updating audit log: {str(e)}")
    
    def get_active_distributed_queries(self) -> List[Dict[str, Any]]:
        """
        Get list of currently active distributed queries
        
        Returns:
            List of active query information
        """
        active_queries = []
        
        with self.lock:
            current_time = time.time()
            
            for query_id, query_info in self.active_queries.items():
                duration = current_time - query_info["start_time"]
                
                active_queries.append({
                    "query_id": query_id,
                    "server_group": query_info["server_group"],
                    "username": query_info["username"],
                    "duration_seconds": round(duration, 2),
                    "timeout": query_info["timeout"],
                    "status": query_info["status"],
                    "servers_total": len(query_info["servers"]),
                    "servers_completed": len(query_info["completed"]),
                    "servers_failed": len(query_info["failed"]),
                    "log_id": query_info.get("log_id")
                })
        
        return active_queries
    
    def get_server_stats(self) -> Dict[str, Dict[str, Any]]:
        """
        Get current server statistics
        
        Returns:
            Dictionary of server statistics
        """
        with self.lock:
            # Create a copy of server stats to avoid race conditions
            return json.loads(json.dumps(self.server_stats))
    
    def cancel_distributed_query(self, query_id: str) -> bool:
        """
        Cancel a running distributed query
        
        Args:
            query_id: ID of the distributed query
            
        Returns:
            True if query was found and canceled, False otherwise
        """
        with self.lock:
            if query_id not in self.active_queries:
                return False
            
            # Mark query as canceled
            self.active_queries[query_id]["status"] = "canceled"
        
        # Note: actual cancellation of the individual server queries
        # would require additional implementation with the database connector
        
        return True

# Create a singleton instance
distributed_query_engine = DistributedQueryEngine()

# Son güncelleme: 2025-05-20 10:25:32
# Güncelleyen: Teeksss