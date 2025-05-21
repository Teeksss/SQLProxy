"""
Automatic Scaling Engine for SQL Proxy

This module provides automatic scaling capabilities for SQL Proxy,
dynamically adjusting connection pools, server resources,
and load balancing based on traffic patterns.

Last updated: 2025-05-20 10:30:03
Updated by: Teeksss
"""

import logging
import time
import threading
import asyncio
import json
from typing import List, Dict, Any, Optional, Set, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.server import ServerConfig, ServerGroup, ServerHealthLog
from app.models.scaler import ScalingEvent, ScalingPolicy, ScalingMetric
from app.services.db_connector import db_connector_service
from app.db.session import SessionLocal
from app.core.config import settings

logger = logging.getLogger(__name__)

class AutoScaler:
    """
    Automatic scaling engine for SQL Proxy
    
    Monitors query load and server metrics to automatically adjust
    connection pools, load balancing, and potentially cloud resources.
    """
    
    def __init__(self):
        """Initialize the auto-scaler"""
        self.active = False
        self.monitoring_thread = None
        self.lock = threading.RLock()
        self.scaling_events = []
        self.load_history = {}
        self.scaling_in_progress = False
        
        # Metrics tracking
        self.metrics = {
            "query_rate": {},      # Queries per minute by server
            "error_rate": {},      # Error percentage by server
            "cpu_usage": {},       # CPU usage percentage by server
            "memory_usage": {},    # Memory usage percentage by server
            "connection_count": {} # Active connections by server
        }
        
        logger.info("Auto-scaler initialized")
    
    def start(self):
        """Start the auto-scaling engine"""
        with self.lock:
            if self.active:
                logger.warning("Auto-scaler is already running")
                return
            
            self.active = True
            
            # Start monitoring thread
            self.monitoring_thread = threading.Thread(
                target=self._monitoring_loop,
                daemon=True
            )
            self.monitoring_thread.start()
            
            logger.info("Auto-scaler started")
    
    def stop(self):
        """Stop the auto-scaling engine"""
        with self.lock:
            if not self.active:
                logger.warning("Auto-scaler is not running")
                return
            
            self.active = False
            
            # Wait for monitoring thread to finish
            if self.monitoring_thread:
                self.monitoring_thread.join(timeout=5)
                self.monitoring_thread = None
            
            logger.info("Auto-scaler stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop for auto-scaling"""
        logger.info("Auto-scaling monitoring loop started")
        
        while self.active:
            try:
                # Create a new database session
                db = SessionLocal()
                
                # Collect metrics
                self._collect_metrics(db)
                
                # Evaluate scaling policies
                if not self.scaling_in_progress:
                    self._evaluate_scaling_policies(db)
                
                # Clean up
                db.close()
                
            except Exception as e:
                logger.error(f"Error in auto-scaling monitoring loop: {str(e)}")
            
            # Sleep before next iteration
            time.sleep(settings.AUTOSCALING_CHECK_INTERVAL_SECONDS)
    
    def _collect_metrics(self, db: Session):
        """
        Collect metrics for scaling decisions
        
        Args:
            db: Database session
        """
        try:
            # Get all active server configurations
            servers = db.query(ServerConfig).filter(
                ServerConfig.is_active == True
            ).all()
            
            # Get the latest health logs for each server
            health_logs = {}
            for server in servers:
                latest_log = db.query(ServerHealthLog).filter(
                    ServerHealthLog.server_id == server.id
                ).order_by(ServerHealthLog.checked_at.desc()).first()
                
                if latest_log:
                    health_logs[server.id] = latest_log
            
            # Get query rate from audit logs (queries in last minute)
            current_time = datetime.utcnow()
            one_minute_ago = current_time - timedelta(minutes=1)
            
            query_rate_sql = """
            SELECT
                target_server,
                COUNT(*) as query_count
            FROM
                audit_logs
            WHERE
                created_at >= :start_time
            GROUP BY
                target_server
            """
            
            query_rate_result = db.execute(query_rate_sql, {
                "start_time": one_minute_ago
            }).fetchall()
            
            # Get error rate from audit logs (last 5 minutes)
            five_minutes_ago = current_time - timedelta(minutes=5)
            
            error_rate_sql = """
            SELECT
                target_server,
                COUNT(*) as total_count,
                SUM(CASE WHEN execution_status != 'success' THEN 1 ELSE 0 END) as error_count
            FROM
                audit_logs
            WHERE
                created_at >= :start_time
            GROUP BY
                target_server
            """
            
            error_rate_result = db.execute(error_rate_sql, {
                "start_time": five_minutes_ago
            }).fetchall()
            
            # Get connection pool statistics from DB connector service
            connection_stats = db_connector_service.get_connection_pool_stats()
            
            # Update metrics
            with self.lock:
                # Query rate
                for row in query_rate_result:
                    server_alias = row[0]
                    query_count = row[1]
                    
                    self.metrics["query_rate"][server_alias] = query_count
                    
                    # Update load history for trend analysis
                    if server_alias not in self.load_history:
                        self.load_history[server_alias] = []
                    
                    self.load_history[server_alias].append({
                        "timestamp": current_time.timestamp(),
                        "query_count": query_count
                    })
                    
                    # Keep only last 60 data points (1 hour at 1-minute intervals)
                    if len(self.load_history[server_alias]) > 60:
                        self.load_history[server_alias].pop(0)
                
                # Error rate
                for row in error_rate_result:
                    server_alias = row[0]
                    total_count = row[1]
                    error_count = row[2]
                    
                    if total_count > 0:
                        error_rate = error_count / total_count * 100
                    else:
                        error_rate = 0
                    
                    self.metrics["error_rate"][server_alias] = error_rate
                
                # Connection count
                for server_alias, stats in connection_stats.items():
                    self.metrics["connection_count"][server_alias] = stats.get("active_connections", 0)
                
                # CPU and memory usage (would come from external monitoring in a real implementation)
                # Here we're using placeholder values
                for server in servers:
                    # In a real implementation, these would come from monitoring systems
                    # such as Prometheus, CloudWatch, etc.
                    self.metrics["cpu_usage"][server.server_alias] = 50  # Placeholder: 50% CPU usage
                    self.metrics["memory_usage"][server.server_alias] = 40  # Placeholder: 40% memory usage
            
            # Persist metrics to database for historical analysis
            self._persist_metrics(db, current_time)
            
        except Exception as e:
            logger.error(f"Error collecting metrics: {str(e)}")
    
    def _persist_metrics(self, db: Session, timestamp: datetime):
        """
        Persist collected metrics to database
        
        Args:
            db: Database session
            timestamp: Timestamp for the metrics
        """
        try:
            # Save metrics for each server
            with self.lock:
                for metric_type, server_metrics in self.metrics.items():
                    for server_alias, value in server_metrics.items():
                        metric = ScalingMetric(
                            metric_type=metric_type,
                            server_alias=server_alias,
                            value=float(value),
                            timestamp=timestamp
                        )
                        
                        db.add(metric)
            
            db.commit()
            
        except Exception as e:
            logger.error(f"Error persisting metrics: {str(e)}")
            db.rollback()
    
    def _evaluate_scaling_policies(self, db: Session):
        """
        Evaluate scaling policies to determine if scaling is needed
        
        Args:
            db: Database session
        """
        try:
            # Get all active scaling policies
            policies = db.query(ScalingPolicy).filter(
                ScalingPolicy.is_active == True
            ).all()
            
            # Group policies by server
            server_policies = {}
            for policy in policies:
                if policy.server_alias not in server_policies:
                    server_policies[policy.server_alias] = []
                
                server_policies[policy.server_alias].append(policy)
            
            # Evaluate policies for each server
            for server_alias, server_policies in server_policies.items():
                for policy in server_policies:
                    # Check if policy should be triggered
                    should_trigger = self._check_policy_trigger(policy, server_alias)
                    
                    if should_trigger:
                        # Execute scaling action
                        self._execute_scaling_action(policy, server_alias, db)
            
        except Exception as e:
            logger.error(f"Error evaluating scaling policies: {str(e)}")
    
    def _check_policy_trigger(self, policy: ScalingPolicy, server_alias: str) -> bool:
        """
        Check if a scaling policy should be triggered
        
        Args:
            policy: Scaling policy to check
            server_alias: Server alias to check against
            
        Returns:
            True if policy should be triggered, False otherwise
        """
        with self.lock:
            # Get the relevant metric
            metric_value = self.metrics.get(policy.metric_type, {}).get(server_alias)
            
            if metric_value is None:
                return False
            
            # Determine if threshold is exceeded
            if policy.scale_direction == "up":
                # For scale up, check if metric is above threshold
                return metric_value >= policy.threshold_value
            else:
                # For scale down, check if metric is below threshold
                return metric_value <= policy.threshold_value
    
    async def _execute_scaling_action(self, policy: ScalingPolicy, server_alias: str, db: Session):
        """
        Execute a scaling action based on policy
        
        Args:
            policy: Scaling policy to execute
            server_alias: Server alias to scale
            db: Database session
        """
        try:
            # Mark that scaling is in progress
            self.scaling_in_progress = True
            
            # Get server configuration
            server = db.query(ServerConfig).filter(
                ServerConfig.server_alias == server_alias
            ).first()
            
            if not server:
                logger.error(f"Server not found: {server_alias}")
                self.scaling_in_progress = False
                return
            
            # Determine scaling action
            action_type = policy.action_type
            action_config = json.loads(policy.action_config) if policy.action_config else {}
            
            # Log scaling event
            event = ScalingEvent(
                server_alias=server_alias,
                policy_id=policy.id,
                action_type=action_type,
                scale_direction=policy.scale_direction,
                status="in_progress",
                metric_type=policy.metric_type,
                metric_value=self.metrics.get(policy.metric_type, {}).get(server_alias),
                threshold_value=policy.threshold_value,
                action_config=policy.action_config
            )
            
            db.add(event)
            db.commit()
            db.refresh(event)
            
            # Execute action based on type
            success = False
            error_message = None
            
            if action_type == "connection_pool":
                success, error_message = await self._scale_connection_pool(
                    server, policy.scale_direction, action_config
                )
            elif action_type == "server_resource":
                success, error_message = await self._scale_server_resources(
                    server, policy.scale_direction, action_config
                )
            elif action_type == "load_balancing":
                success, error_message = await self._adjust_load_balancing(
                    server, policy.scale_direction, action_config
                )
            else:
                error_message = f"Unknown scaling action type: {action_type}"
            
            # Update scaling event
            event.status = "success" if success else "failed"
            event.completed_at = datetime.utcnow()
            event.error_message = error_message
            
            db.commit()
            
            # Add to scaling events history
            with self.lock:
                self.scaling_events.append({
                    "id": event.id,
                    "server_alias": server_alias,
                    "action_type": action_type,
                    "scale_direction": policy.scale_direction,
                    "status": event.status,
                    "timestamp": datetime.utcnow().isoformat(),
                    "metric_type": policy.metric_type,
                    "metric_value": self.metrics.get(policy.metric_type, {}).get(server_alias),
                    "threshold_value": policy.threshold_value
                })
                
                # Keep only the last 100 events
                if len(self.scaling_events) > 100:
                    self.scaling_events = self.scaling_events[-100:]
            
            # Cooldown period (avoid rapid scaling)
            await asyncio.sleep(policy.cooldown_seconds)
            
        except Exception as e:
            logger.error(f"Error executing scaling action: {str(e)}")
        finally:
            # Mark that scaling is no longer in progress
            self.scaling_in_progress = False
    
    async def _scale_connection_pool(
        self,
        server: ServerConfig,
        direction: str,
        config: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """
        Scale a server's connection pool
        
        Args:
            server: Server to scale
            direction: "up" or "down"
            config: Scaling configuration
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Get configuration
            step_size = config.get("step_size", 5)
            max_size = config.get("max_size", 50)
            min_size = config.get("min_size", 5)
            
            # Calculate new connection pool size
            current_size = server.max_connections
            
            if direction == "up":
                new_size = min(current_size + step_size, max_size)
            else:
                new_size = max(current_size - step_size, min_size)
            
            # No change needed
            if new_size == current_size:
                return True, None
            
            # Update server configuration
            server.max_connections = new_size
            
            # Apply the change to the connection pool
            await db_connector_service.update_connection_pool(
                server_alias=server.server_alias,
                max_connections=new_size
            )
            
            logger.info(f"Scaled connection pool for {server.server_alias} from {current_size} to {new_size}")
            
            return True, None
            
        except Exception as e:
            error_message = f"Error scaling connection pool: {str(e)}"
            logger.error(error_message)
            return False, error_message
    
    async def _scale_server_resources(
        self,
        server: ServerConfig,
        direction: str,
        config: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """
        Scale a server's compute resources (for cloud databases)
        
        Args:
            server: Server to scale
            direction: "up" or "down"
            config: Scaling configuration
            
        Returns:
            Tuple of (success, error_message)
        """
        # In a real implementation, this would connect to a cloud provider API
        # to scale the database instance up or down.
        
        # For this example, we'll just simulate success
        logger.info(f"Simulated resource scaling for {server.server_alias} direction={direction}")
        
        # Simulate some delay for the scaling operation
        await asyncio.sleep(2)
        
        return True, None
    
    async def _adjust_load_balancing(
        self,
        server: ServerConfig,
        direction: str,
        config: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """
        Adjust load balancing weight for a server
        
        Args:
            server: Server to adjust
            direction: "up" or "down"
            config: Adjustment configuration
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Get configuration
            weight_step = config.get("weight_step", 0.2)
            max_weight = config.get("max_weight", 10.0)
            min_weight = config.get("min_weight", 0.1)
            
            # Calculate new weight
            current_weight = server.weight
            
            if direction == "up":
                new_weight = min(current_weight + weight_step, max_weight)
            else:
                new_weight = max(current_weight - weight_step, min_weight)
            
            # No change needed
            if new_weight == current_weight:
                return True, None
            
            # Update server configuration
            server.weight = new_weight
            
            logger.info(f"Adjusted load balancing weight for {server.server_alias} from {current_weight} to {new_weight}")
            
            return True, None
            
        except Exception as e:
            error_message = f"Error adjusting load balancing: {str(e)}"
            logger.error(error_message)
            return False, error_message
    
    def get_metrics(self, server_alias: Optional[str] = None) -> Dict[str, Any]:
        """
        Get current metrics for a server or all servers
        
        Args:
            server_alias: Optional server alias to filter metrics
            
        Returns:
            Dictionary of metrics
        """
        with self.lock:
            if server_alias:
                # Return metrics for specific server
                result = {}
                for metric_type, server_metrics in self.metrics.items():
                    if server_alias in server_metrics:
                        result[metric_type] = server_metrics[server_alias]
                return result
            else:
                # Return all metrics
                return json.loads(json.dumps(self.metrics))
    
    def get_scaling_events(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get recent scaling events
        
        Args:
            limit: Maximum number of events to return
            
        Returns:
            List of scaling events
        """
        with self.lock:
            return self.scaling_events[-limit:]
    
    def get_load_trends(
        self, 
        server_alias: Optional[str] = None, 
        hours: int = 1
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get load trend data for visualization
        
        Args:
            server_alias: Optional server alias to filter trends
            hours: Number of hours of history to include
            
        Returns:
            Dictionary of server load trends
        """
        with self.lock:
            # Get current time for filtering
            current_time = time.time()
            cutoff_time = current_time - (hours * 3600)
            
            # Filter and format load history
            result = {}
            
            for server, history in self.load_history.items():
                if server_alias and server != server_alias:
                    continue
                
                # Filter by time
                filtered_history = [
                    point for point in history 
                    if point["timestamp"] >= cutoff_time
                ]
                
                # Convert to proper format for charting
                formatted_history = [
                    {
                        "timestamp": datetime.fromtimestamp(point["timestamp"]).isoformat(),
                        "query_count": point["query_count"]
                    }
                    for point in filtered_history
                ]
                
                result[server] = formatted_history
            
            return result
    
    def get_historical_metrics(
        self,
        db: Session,
        server_alias: Optional[str] = None,
        metric_type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        interval: str = "1h"
    ) -> Dict[str, Any]:
        """
        Get historical metrics from database
        
        Args:
            db: Database session
            server_alias: Optional server alias to filter metrics
            metric_type: Optional metric type to filter
            start_time: Start time for metrics (defaults to 24h ago)
            end_time: End time for metrics (defaults to now)
            interval: Time interval for aggregation
            
        Returns:
            Dictionary of historical metrics
        """
        try:
            # Set default time range if not provided
            if not end_time:
                end_time = datetime.utcnow()
            
            if not start_time:
                start_time = end_time - timedelta(hours=24)
            
            # Build query
            query = """
            SELECT
                server_alias,
                metric_type,
                time_bucket(:interval, timestamp) as time_bucket,
                AVG(value) as avg_value,
                MIN(value) as min_value,
                MAX(value) as max_value
            FROM
                scaling_metrics
            WHERE
                timestamp BETWEEN :start_time AND :end_time
            """
            
            params = {
                "interval": interval,
                "start_time": start_time,
                "end_time": end_time
            }
            
            # Add filters
            if server_alias:
                query += " AND server_alias = :server_alias"
                params["server_alias"] = server_alias
            
            if metric_type:
                query += " AND metric_type = :metric_type"
                params["metric_type"] = metric_type
            
            # Add group by and order by
            query += """
            GROUP BY
                server_alias, metric_type, time_bucket
            ORDER BY
                server_alias, metric_type, time_bucket
            """
            
            # Execute query
            result = db.execute(query, params).fetchall()
            
            # Format results
            metrics = {}
            
            for row in result:
                server = row[0]
                metric = row[1]
                bucket = row[2].isoformat()
                avg_value = row[3]
                min_value = row[4]
                max_value = row[5]
                
                # Initialize nested dictionaries if needed
                if server not in metrics:
                    metrics[server] = {}
                
                if metric not in metrics[server]:
                    metrics[server][metric] = []
                
                # Add data point
                metrics[server][metric].append({
                    "timestamp": bucket,
                    "avg": avg_value,
                    "min": min_value,
                    "max": max_value
                })
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting historical metrics: {str(e)}")
            return {}

# Create a singleton instance
auto_scaler = AutoScaler()

# Son güncelleme: 2025-05-20 10:30:03
# Güncelleyen: Teeksss