"""
Advanced Audit Trail System for SQL Proxy

This module provides comprehensive audit logging and tracking
for all system activities, with search and reporting capabilities.

Last updated: 2025-05-20 10:34:03
Updated by: Teeksss
"""

import logging
import json
import time
import threading
import queue
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models.audit import AuditTrail, AuditCategory, ActivityType
from app.db.session import get_db
from app.core.config import settings

logger = logging.getLogger(__name__)

class AuditTrailService:
    """
    Advanced audit trail service
    
    Provides audit logging capabilities with background processing
    and search functionality.
    """
    
    def __init__(self):
        """Initialize the audit trail service"""
        self.enabled = settings.AUDIT_TRAIL_ENABLED
        self.queue = queue.Queue(maxsize=1000)
        self.worker_thread = None
        self.running = False
        self.batch_size = settings.AUDIT_TRAIL_BATCH_SIZE
        self.batch_timeout = settings.AUDIT_TRAIL_BATCH_TIMEOUT
        self.sensitive_fields = settings.AUDIT_TRAIL_SENSITIVE_FIELDS
        
        # Start worker thread if enabled
        if self.enabled:
            self.start_worker()
    
    def start_worker(self):
        """Start the worker thread for processing audit logs"""
        if self.worker_thread and self.worker_thread.is_alive():
            return
        
        self.running = True
        self.worker_thread = threading.Thread(
            target=self._process_audit_queue,
            daemon=True
        )
        self.worker_thread.start()
        logger.info("Audit trail worker thread started")
    
    def stop_worker(self):
        """Stop the worker thread"""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
            self.worker_thread = None
        logger.info("Audit trail worker thread stopped")
    
    def log_activity(
        self,
        user: str,
        category: str,
        activity_type: str,
        target: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        session_id: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        db: Optional[Session] = None
    ) -> bool:
        """
        Log an audit activity
        
        Args:
            user: Username or system identity
            category: Audit category (user, query, system, etc.)
            activity_type: Type of activity
            target: Target object or entity
            details: Activity details
            ip_address: Client IP address
            session_id: User session ID
            success: Whether the activity was successful
            error_message: Error message if activity failed
            db: Database session (optional - if provided, log is created synchronously)
            
        Returns:
            True if log was created or queued, False otherwise
        """
        if not self.enabled:
            return False
        
        try:
            # Create audit record
            audit_data = {
                "user": user,
                "category": category,
                "activity_type": activity_type,
                "target": target,
                "details": self._mask_sensitive_data(details) if details else None,
                "ip_address": ip_address,
                "session_id": session_id,
                "success": success,
                "error_message": error_message,
                "created_at": datetime.utcnow()
            }
            
            # If database session provided, log synchronously
            if db:
                self._create_audit_log(audit_data, db)
                return True
            
            # Otherwise, queue for background processing
            try:
                self.queue.put(audit_data, block=False)
                return True
            except queue.Full:
                logger.warning("Audit log queue is full, dropping audit log")
                return False
            
        except Exception as e:
            logger.error(f"Error logging audit activity: {str(e)}")
            return False
    
    def _process_audit_queue(self):
        """Process audit logs from the queue in batches"""
        while self.running:
            try:
                batch = []
                timeout = self.batch_timeout
                start_time = time.time()
                
                # Collect batch of logs or until timeout
                while len(batch) < self.batch_size and time.time() - start_time < timeout:
                    try:
                        # Get next item from queue with timeout
                        remaining_timeout = max(0, timeout - (time.time() - start_time))
                        audit_data = self.queue.get(timeout=remaining_timeout)
                        batch.append(audit_data)
                        self.queue.task_done()
                    except queue.Empty:
                        break
                
                # Process batch if not empty
                if batch:
                    self._process_batch(batch)
            
            except Exception as e:
                logger.error(f"Error processing audit logs: {str(e)}")
                time.sleep(1)  # Avoid tight loop in error case
    
    def _process_batch(self, batch: List[Dict[str, Any]]):
        """
        Process a batch of audit logs
        
        Args:
            batch: List of audit log data
        """
        try:
            # Get database session
            db = next(get_db())
            
            # Create logs
            for audit_data in batch:
                self._create_audit_log(audit_data, db)
            
            # Commit batch
            db.commit()
            
        except Exception as e:
            logger.error(f"Error processing audit batch: {str(e)}")
            if 'db' in locals():
                db.rollback()
        finally:
            if 'db' in locals():
                db.close()
    
    def _create_audit_log(self, audit_data: Dict[str, Any], db: Session):
        """
        Create an audit log entry in the database
        
        Args:
            audit_data: Audit log data
            db: Database session
        """
        # Convert details to JSON if not None
        if audit_data["details"] is not None:
            audit_data["details_json"] = json.dumps(audit_data["details"])
        else:
            audit_data["details_json"] = None
        
        # Remove details (no longer needed)
        audit_data.pop("details", None)
        
        # Create audit log
        audit_log = AuditTrail(**audit_data)
        db.add(audit_log)
    
    def _mask_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Mask sensitive data in audit logs
        
        Args:
            data: Data to mask
            
        Returns:
            Data with sensitive fields masked
        """
        if not data:
            return data
        
        # Make a copy to avoid modifying the original
        masked_data = data.copy()
        
        # Iterate through all fields and sub-fields recursively
        self._process_dict_fields(masked_data)
        
        return masked_data
    
    def _process_dict_fields(self, data: Dict[str, Any]):
        """
        Process dictionary fields recursively for masking
        
        Args:
            data: Dictionary to process
        """
        for key, value in data.items():
            # Check if this field should be masked
            if key.lower() in self.sensitive_fields:
                data[key] = "********"
            elif isinstance(value, dict):
                # Process nested dictionaries
                self._process_dict_fields(value)
            elif isinstance(value, list):
                # Process list of dictionaries
                for item in value:
                    if isinstance(item, dict):
                        self._process_dict_fields(item)
    
    def search_audit_logs(
        self,
        db: Session,
        user: Optional[str] = None,
        category: Optional[str] = None,
        activity_type: Optional[str] = None,
        target: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        ip_address: Optional[str] = None,
        session_id: Optional[str] = None,
        success: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0,
        sort_by: str = "created_at",
        sort_desc: bool = True
    ) -> Tuple[List[AuditTrail], int]:
        """
        Search audit logs with filtering
        
        Args:
            db: Database session
            user: Filter by username
            category: Filter by category
            activity_type: Filter by activity type
            target: Filter by target
            start_date: Filter by start date
            end_date: Filter by end date
            ip_address: Filter by IP address
            session_id: Filter by session ID
            success: Filter by success status
            limit: Maximum number of results
            offset: Result offset for pagination
            sort_by: Field to sort by
            sort_desc: Whether to sort in descending order
            
        Returns:
            Tuple of (audit_logs, total_count)
        """
        try:
            # Create base query
            query = db.query(AuditTrail)
            count_query = db.query(AuditTrail)
            
            # Apply filters
            if user:
                query = query.filter(AuditTrail.user == user)
                count_query = count_query.filter(AuditTrail.user == user)
            
            if category:
                query = query.filter(AuditTrail.category == category)
                count_query = count_query.filter(AuditTrail.category == category)
            
            if activity_type:
                query = query.filter(AuditTrail.activity_type == activity_type)
                count_query = count_query.filter(AuditTrail.activity_type == activity_type)
            
            if target:
                query = query.filter(AuditTrail.target.like(f"%{target}%"))
                count_query = count_query.filter(AuditTrail.target.like(f"%{target}%"))
            
            if start_date:
                query = query.filter(AuditTrail.created_at >= start_date)
                count_query = count_query.filter(AuditTrail.created_at >= start_date)
            
            if end_date:
                query = query.filter(AuditTrail.created_at <= end_date)
                count_query = count_query.filter(AuditTrail.created_at <= end_date)
            
            if ip_address:
                query = query.filter(AuditTrail.ip_address == ip_address)
                count_query = count_query.filter(AuditTrail.ip_address == ip_address)
            
            if session_id:
                query = query.filter(AuditTrail.session_id == session_id)
                count_query = count_query.filter(AuditTrail.session_id == session_id)
            
            if success is not None:
                query = query.filter(AuditTrail.success == success)
                count_query = count_query.filter(AuditTrail.success == success)
            
            # Get total count
            total_count = count_query.count()
            
            # Apply sorting
            if sort_by and hasattr(AuditTrail, sort_by):
                sort_column = getattr(AuditTrail, sort_by)
                if sort_desc:
                    query = query.order_by(sort_column.desc())
                else:
                    query = query.order_by(sort_column)
            else:
                # Default sort by created_at desc
                query = query.order_by(AuditTrail.created_at.desc())
            
            # Apply pagination
            query = query.limit(limit).offset(offset)
            
            # Execute query
            results = query.all()
            
            return results, total_count
            
        except Exception as e:
            logger.error(f"Error searching audit logs: {str(e)}")
            return [], 0
    
    def get_audit_categories(self, db: Session) -> List[Dict[str, Any]]:
        """
        Get list of all audit categories and activity types
        
        Args:
            db: Database session
            
        Returns:
            List of categories with their activity types
        """
        try:
            # Query distinct categories
            categories = db.query(AuditCategory).all()
            
            result = []
            for category in categories:
                # Query activity types for this category
                activity_types = db.query(ActivityType).filter(
                    ActivityType.category_id == category.id
                ).all()
                
                # Format result
                result.append({
                    "id": category.id,
                    "name": category.name,
                    "description": category.description,
                    "activity_types": [
                        {
                            "id": a.id,
                            "name": a.name,
                            "description": a.description
                        }
                        for a in activity_types
                    ]
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting audit categories: {str(e)}")
            return []
    
    def get_audit_statistics(
        self,
        db: Session,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        Get statistics about audit logs
        
        Args:
            db: Database session
            days: Number of days to look back
            
        Returns:
            Dictionary of statistics
        """
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Get total count
            total_count = db.query(AuditTrail).filter(
                AuditTrail.created_at >= start_date
            ).count()
            
            # Get counts by category
            category_counts = {}
            categories = db.query(AuditCategory).all()
            
            for category in categories:
                count = db.query(AuditTrail).filter(
                    AuditTrail.category == category.name,
                    AuditTrail.created_at >= start_date
                ).count()
                
                category_counts[category.name] = count
            
            # Get counts by success
            success_count = db.query(AuditTrail).filter(
                AuditTrail.success == True,
                AuditTrail.created_at >= start_date
            ).count()
            
            failure_count = db.query(AuditTrail).filter(
                AuditTrail.success == False,
                AuditTrail.created_at >= start_date
            ).count()
            
            # Get daily activity counts
            daily_activity = db.execute(text("""
                SELECT 
                    DATE(created_at) as date, 
                    COUNT(*) as count 
                FROM 
                    audit_trail 
                WHERE 
                    created_at >= :start_date 
                GROUP BY 
                    DATE(created_at) 
                ORDER BY 
                    date
            """), {"start_date": start_date}).fetchall()
            
            # Format daily activity
            daily_counts = [
                {"date": str(row[0]), "count": row[1]}
                for row in daily_activity
            ]
            
            # Get most active users
            active_users = db.execute(text("""
                SELECT 
                    user, 
                    COUNT(*) as count 
                FROM 
                    audit_trail 
                WHERE 
                    created_at >= :start_date 
                GROUP BY 
                    user 
                ORDER BY 
                    count DESC 
                LIMIT 10
            """), {"start_date": start_date}).fetchall()
            
            # Format active users
            user_counts = [
                {"user": row[0], "count": row[1]}
                for row in active_users
            ]
            
            return {
                "total_count": total_count,
                "category_counts": category_counts,
                "success_count": success_count,
                "failure_count": failure_count,
                "success_rate": (success_count / total_count) if total_count > 0 else 0,
                "daily_activity": daily_counts,
                "active_users": user_counts,
                "period_days": days
            }
            
        except Exception as e:
            logger.error(f"Error getting audit statistics: {str(e)}")
            return {
                "error": str(e)
            }

# Create a singleton instance
audit_trail_service = AuditTrailService()

# Son güncelleme: 2025-05-20 10:34:03
# Güncelleyen: Teeksss