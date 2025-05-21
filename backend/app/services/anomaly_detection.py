"""
Anomaly detection service for SQL Proxy

This module provides functionality to detect abnormal patterns in query execution,
user behavior, and system performance that might indicate potential security issues
or performance problems.

Last updated: 2025-05-20 06:01:10
Updated by: Teeksss
"""

import logging
import time
import datetime
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from collections import defaultdict, deque

from fastapi import BackgroundTasks
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.anomaly import AnomalyAlert, AnomalyRule
from app.models.query import AuditLog
from app.services.notification_service import notification_service
from app.db.session import get_db

logger = logging.getLogger(__name__)

class AnomalyDetectionService:
    """Service for detecting anomalies in SQL Proxy usage patterns"""
    
    def __init__(self):
        """Initialize the anomaly detection service"""
        # In-memory caches and counters
        self._query_count_per_user = defaultdict(lambda: deque(maxlen=1000))
        self._query_count_per_server = defaultdict(lambda: deque(maxlen=1000))
        self._error_count_per_user = defaultdict(lambda: deque(maxlen=1000))
        self._execution_times = defaultdict(lambda: deque(maxlen=1000))
        
        # Time windows for analysis (in seconds)
        self._time_windows = [60, 300, 900, 3600]  # 1min, 5min, 15min, 1hour
        
        # Threshold configurations
        self._thresholds = {
            'query_spike': 3.0,  # Factor increase over baseline
            'error_rate': 0.2,   # 20% error rate
            'slow_query': 5.0,   # Factor increase over baseline execution time
            'failed_login': 5,   # Number of consecutive failures
            'unusual_hour': 0.05 # Probability threshold for unusual hour
        }
        
        # Load anomaly rules from database
        self._rules = []
        self._load_rules()
        
        logger.info("Anomaly detection service initialized")
    
    def _load_rules(self):
        """Load anomaly detection rules from the database"""
        try:
            # Get DB session
            with next(get_db()) as db:
                self._rules = db.query(AnomalyRule).filter(AnomalyRule.is_active == True).all()
                logger.info(f"Loaded {len(self._rules)} anomaly detection rules")
        except Exception as e:
            logger.error(f"Error loading anomaly rules: {str(e)}")
            # Default rules if database load fails
            self._rules = [
                {
                    'id': 1,
                    'name': 'Query Volume Spike',
                    'description': 'Detects sudden increases in query volume',
                    'rule_type': 'query_volume',
                    'threshold': 3.0,
                    'time_window': 300,
                    'is_active': True,
                    'severity': 'medium',
                    'actions': ['notify_admin', 'log']
                },
                {
                    'id': 2,
                    'name': 'High Error Rate',
                    'description': 'Detects abnormal error rates',
                    'rule_type': 'error_rate',
                    'threshold': 0.2,
                    'time_window': 300, 
                    'is_active': True,
                    'severity': 'high',
                    'actions': ['notify_admin', 'log']
                },
                {
                    'id': 3,
                    'name': 'Unusual Access Hour',
                    'description': 'Detects access during unusual hours',
                    'rule_type': 'unusual_time',
                    'threshold': 0.05,
                    'time_window': 3600,
                    'is_active': True,
                    'severity': 'low',
                    'actions': ['log']
                }
            ]
    
    def process_query_execution(self, audit_log: AuditLog, background_tasks: BackgroundTasks):
        """
        Process a query execution event to detect anomalies
        
        Args:
            audit_log: The audit log entry for the query execution
            background_tasks: FastAPI background tasks
        """
        # Add to background tasks to avoid blocking the request
        background_tasks.add_task(self._analyze_query_execution, audit_log)
    
    async def _analyze_query_execution(self, audit_log: AuditLog):
        """
        Analyze a query execution for anomalies
        
        Args:
            audit_log: The audit log entry for the query execution
        """
        try:
            now = time.time()
            timestamp = now
            
            # Update in-memory data
            self._query_count_per_user[audit_log.username].append((timestamp, 1))
            self._query_count_per_server[audit_log.target_server].append((timestamp, 1))
            
            if audit_log.execution_status != 'success':
                self._error_count_per_user[audit_log.username].append((timestamp, 1))
            
            if audit_log.execution_time_ms:
                self._execution_times[audit_log.query_type].append((timestamp, audit_log.execution_time_ms))
            
            # Run anomaly detection
            anomalies = []
            
            # Check for query volume spikes
            volume_anomaly = self._detect_query_volume_anomaly(audit_log.username, now)
            if volume_anomaly:
                anomalies.append(volume_anomaly)
            
            # Check for error rate anomalies
            error_anomaly = self._detect_error_rate_anomaly(audit_log.username, now)
            if error_anomaly:
                anomalies.append(error_anomaly)
            
            # Check for slow query anomalies
            if audit_log.execution_time_ms:
                slow_query_anomaly = self._detect_slow_query_anomaly(
                    audit_log.query_type, 
                    audit_log.execution_time_ms, 
                    now
                )
                if slow_query_anomaly:
                    anomalies.append(slow_query_anomaly)
            
            # Check for unusual access hour
            hour_anomaly = self._detect_unusual_hour_anomaly(audit_log.username, now)
            if hour_anomaly:
                anomalies.append(hour_anomaly)
            
            # Process detected anomalies
            for anomaly in anomalies:
                await self._process_anomaly(anomaly, audit_log)
            
        except Exception as e:
            logger.error(f"Error in anomaly detection: {str(e)}")
    
    def _detect_query_volume_anomaly(self, username: str, current_time: float) -> Optional[Dict[str, Any]]:
        """
        Detect anomalous query volume for a user
        
        Args:
            username: Username to check
            current_time: Current timestamp
            
        Returns:
            Anomaly details if detected, None otherwise
        """
        if username not in self._query_count_per_user:
            return None
            
        for window in self._time_windows:
            # Get rule for this window
            rule = next((r for r in self._rules if r.get('rule_type') == 'query_volume' and r.get('time_window') == window), None)
            if not rule:
                continue
                
            threshold = rule.get('threshold', self._thresholds['query_spike'])
            
            # Count queries in current window
            window_start = current_time - window
            current_count = sum(1 for ts, _ in self._query_count_per_user[username] if ts >= window_start)
            
            # Get historical data for comparison
            hist_window_start = window_start - window
            hist_window_end = window_start
            historical_count = sum(1 for ts, _ in self._query_count_per_user[username] 
                                  if hist_window_start <= ts < hist_window_end)
            
            # Check if we have enough data and if there's an anomaly
            if historical_count > 0 and (current_count / historical_count) >= threshold:
                return {
                    'type': 'query_volume',
                    'username': username,
                    'current_count': current_count,
                    'historical_count': historical_count,
                    'ratio': current_count / historical_count,
                    'threshold': threshold,
                    'window': window,
                    'severity': rule.get('severity', 'medium'),
                    'rule_id': rule.get('id')
                }
        
        return None
    
    def _detect_error_rate_anomaly(self, username: str, current_time: float) -> Optional[Dict[str, Any]]:
        """
        Detect anomalous error rates for a user
        
        Args:
            username: Username to check
            current_time: Current timestamp
            
        Returns:
            Anomaly details if detected, None otherwise
        """
        if username not in self._query_count_per_user or username not in self._error_count_per_user:
            return None
            
        for window in self._time_windows:
            # Get rule for this window
            rule = next((r for r in self._rules if r.get('rule_type') == 'error_rate' and r.get('time_window') == window), None)
            if not rule:
                continue
                
            threshold = rule.get('threshold', self._thresholds['error_rate'])
            
            # Count queries and errors in current window
            window_start = current_time - window
            total_queries = sum(1 for ts, _ in self._query_count_per_user[username] if ts >= window_start)
            error_queries = sum(1 for ts, _ in self._error_count_per_user[username] if ts >= window_start)
            
            # Check if we have enough data and if there's an anomaly
            if total_queries >= 10 and error_queries > 0:  # Need at least 10 queries to avoid false positives
                error_rate = error_queries / total_queries
                if error_rate >= threshold:
                    return {
                        'type': 'error_rate',
                        'username': username,
                        'total_queries': total_queries,
                        'error_queries': error_queries,
                        'error_rate': error_rate,
                        'threshold': threshold,
                        'window': window,
                        'severity': rule.get('severity', 'high'),
                        'rule_id': rule.get('id')
                    }
        
        return None
    
    def _detect_slow_query_anomaly(self, query_type: str, execution_time: float, current_time: float) -> Optional[Dict[str, Any]]:
        """
        Detect anomalously slow queries
        
        Args:
            query_type: Type of query (read, write, etc.)
            execution_time: Execution time in milliseconds
            current_time: Current timestamp
            
        Returns:
            Anomaly details if detected, None otherwise
        """
        if query_type not in self._execution_times:
            return None
            
        for window in self._time_windows:
            # Get rule for this window
            rule = next((r for r in self._rules if r.get('rule_type') == 'slow_query' and r.get('time_window') == window), None)
            if not rule:
                continue
                
            threshold = rule.get('threshold', self._thresholds['slow_query'])
            
            # Get historical execution times
            window_start = current_time - window
            historical_times = [t for ts, t in self._execution_times[query_type] 
                               if window_start <= ts < current_time]
            
            # Check if we have enough data
            if len(historical_times) >= 10:  # Need at least 10 samples for baseline
                avg_time = np.mean(historical_times)
                if avg_time > 0 and (execution_time / avg_time) >= threshold:
                    return {
                        'type': 'slow_query',
                        'query_type': query_type,
                        'execution_time': execution_time,
                        'avg_execution_time': avg_time,
                        'ratio': execution_time / avg_time,
                        'threshold': threshold,
                        'window': window,
                        'severity': rule.get('severity', 'medium'),
                        'rule_id': rule.get('id')
                    }
        
        return None
    
    def _detect_unusual_hour_anomaly(self, username: str, current_time: float) -> Optional[Dict[str, Any]]:
        """
        Detect access during unusual hours
        
        Args:
            username: Username to check
            current_time: Current timestamp
            
        Returns:
            Anomaly details if detected, None otherwise
        """
        # Get current hour (in user's timezone if available, otherwise UTC)
        current_dt = datetime.datetime.fromtimestamp(current_time)
        current_hour = current_dt.hour
        
        # Check if we have a rule for unusual hours
        rule = next((r for r in self._rules if r.get('rule_type') == 'unusual_time'), None)
        if not rule:
            return None
            
        threshold = rule.get('threshold', self._thresholds['unusual_hour'])
        
        # Business hours are typically 8am to 6pm
        business_hours = set(range(8, 19))  # 8am to 6pm
        
        # If current hour is outside business hours, flag as unusual
        # This is a simplified approach - in production, we should use historical data
        if current_hour not in business_hours:
            # Calculate "unusualness" - lower means more unusual
            # Hours right before/after business hours are less unusual
            if current_hour in [6, 7, 19, 20]:
                unusualness = 0.1  # Less unusual
            elif current_hour in [21, 22, 23, 0, 1, 2, 3, 4, 5]:
                unusualness = 0.01  # Very unusual
            
            if unusualness <= threshold:
                return {
                    'type': 'unusual_time',
                    'username': username,
                    'hour': current_hour,
                    'unusualness': unusualness,
                    'threshold': threshold,
                    'severity': rule.get('severity', 'low'),
                    'rule_id': rule.get('id')
                }
        
        return None
    
    async def _process_anomaly(self, anomaly: Dict[str, Any], audit_log: AuditLog):
        """
        Process a detected anomaly
        
        Args:
            anomaly: Anomaly details
            audit_log: Related audit log entry
        """
        try:
            # Get the rule for this anomaly
            rule_id = anomaly.get('rule_id')
            rule = next((r for r in self._rules if r.get('id') == rule_id), None)
            
            if not rule:
                logger.warning(f"Rule not found for anomaly: {anomaly}")
                return
            
            actions = rule.get('actions', ['log'])
            
            # Create anomaly alert in database
            with next(get_db()) as db:
                alert = AnomalyAlert(
                    rule_id=rule_id,
                    anomaly_type=anomaly['type'],
                    username=audit_log.username,
                    user_role=audit_log.user_role,
                    client_ip=audit_log.client_ip,
                    target_server=audit_log.target_server,
                    query_id=audit_log.id,
                    query_hash=audit_log.query_hash,
                    details=anomaly,
                    severity=anomaly['severity'],
                    status='open'
                )
                db.add(alert)
                db.commit()
                db.refresh(alert)
            
            # Execute actions
            if 'notify_admin' in actions:
                await self._notify_admin(alert, anomaly, audit_log)
            
            if 'rate_limit' in actions:
                await self._apply_rate_limit(audit_log.username)
            
            logger.info(f"Processed anomaly: {anomaly['type']} for user {audit_log.username} with severity {anomaly['severity']}")
            
        except Exception as e:
            logger.error(f"Error processing anomaly: {str(e)}")
    
    async def _notify_admin(self, alert: AnomalyAlert, anomaly: Dict[str, Any], audit_log: AuditLog):
        """
        Send notification to admins about the anomaly
        
        Args:
            alert: Anomaly alert from database
            anomaly: Anomaly details
            audit_log: Related audit log entry
        """
        try:
            # Create notification message
            title = f"Anomaly Alert: {anomaly['type']} Detected"
            
            message = f"Anomaly detected: {anomaly['type']} with {anomaly['severity']} severity\n"
            message += f"User: {audit_log.username} ({audit_log.user_role})\n"
            message += f"Server: {audit_log.target_server}\n"
            message += f"Time: {datetime.datetime.utcnow().isoformat()}\n\n"
            
            # Add type-specific details
            if anomaly['type'] == 'query_volume':
                message += f"Current query count: {anomaly['current_count']}\n"
                message += f"Historical query count: {anomaly['historical_count']}\n"
                message += f"Ratio: {anomaly['ratio']:.2f}x (threshold: {anomaly['threshold']}x)\n"
                message += f"Time window: {anomaly['window']} seconds\n"
            
            elif anomaly['type'] == 'error_rate':
                message += f"Error rate: {anomaly['error_rate']*100:.2f}% ({anomaly['error_queries']} out of {anomaly['total_queries']} queries)\n"
                message += f"Threshold: {anomaly['threshold']*100:.2f}%\n"
                message += f"Time window: {anomaly['window']} seconds\n"
            
            elif anomaly['type'] == 'slow_query':
                message += f"Query type: {anomaly['query_type']}\n"
                message += f"Execution time: {anomaly['execution_time']:.2f}ms\n"
                message += f"Average execution time: {anomaly['avg_execution_time']:.2f}ms\n"
                message += f"Ratio: {anomaly['ratio']:.2f}x (threshold: {anomaly['threshold']}x)\n"
            
            elif anomaly['type'] == 'unusual_time':
                message += f"Access hour: {anomaly['hour']}:00 UTC\n"
                message += f"Outside normal business hours (8:00-19:00)\n"
            
            # Add query details
            message += f"\nQuery: {audit_log.query_text[:100]}..." if len(audit_log.query_text) > 100 else f"\nQuery: {audit_log.query_text}"
            
            # Send notification
            await notification_service.send_admin_notification(title, message, severity=anomaly['severity'])
            
        except Exception as e:
            logger.error(f"Error sending anomaly notification: {str(e)}")
    
    async def _apply_rate_limit(self, username: str):
        """
        Apply rate limiting to a user
        
        Args:
            username: Username to rate limit
        """
        # This would integrate with the rate limiter service
        # For now, just log the action
        logger.info(f"Would apply rate limit to user {username} due to anomaly")

# Singleton instance
anomaly_detection_service = AnomalyDetectionService()

# Son güncelleme: 2025-05-20 06:01:10
# Güncelleyen: Teeksss