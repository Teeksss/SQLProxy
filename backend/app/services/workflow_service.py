"""
Workflow service for SQL Proxy

This service manages approval workflows, including rule evaluation
and workflow instance creation and progression.

Last updated: 2025-05-20 07:47:46
Updated by: Teeksss
"""

import logging
import re
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.approval import (
    ApprovalWorkflow, ApprovalStep, ApprovalInstance, StepInstance
)
from app.models.query import PendingApproval
from app.services.sql_parser import SQLParser

logger = logging.getLogger(__name__)

class WorkflowService:
    """
    Service for managing approval workflows
    
    Provides functionality to evaluate workflow rules, create workflow instances,
    and manage workflow progression.
    """
    
    def __init__(self, db: Session = None):
        """
        Initialize the workflow service
        
        Args:
            db: Optional database session
        """
        self.db = db
        self.sql_parser = SQLParser()
        logger.info("Workflow service initialized")
    
    def find_matching_workflow(
        self, 
        sql_query: str, 
        server_alias: str, 
        username: str,
        db: Session = None
    ) -> Optional[ApprovalWorkflow]:
        """
        Find the highest priority workflow that matches a query
        
        Args:
            sql_query: SQL query to evaluate
            server_alias: Target server alias
            username: Username of the requester
            db: Database session (if not provided at initialization)
            
        Returns:
            Matching ApprovalWorkflow or None if no match
        """
        # Use provided DB session or the one from initialization
        db_session = db or self.db
        if not db_session:
            logger.error("No database session provided")
            return None
        
        try:
            # Get all active workflows ordered by priority (highest first)
            workflows = db_session.query(ApprovalWorkflow).filter(
                ApprovalWorkflow.is_active == True
            ).order_by(ApprovalWorkflow.priority.desc()).all()
            
            # Parse the SQL query
            parsed_query = self.sql_parser.parse_query(sql_query)
            if not parsed_query:
                logger.warning(f"Unable to parse SQL query: {sql_query[:100]}...")
                return None
            
            # Evaluate each workflow's rule
            for workflow in workflows:
                if self.evaluate_rule(
                    workflow.rule_type,
                    workflow.rule_condition,
                    sql_query,
                    server_alias,
                    username,
                    parsed_query
                ):
                    return workflow
            
            # No matching workflow
            return None
        
        except Exception as e:
            logger.error(f"Error finding matching workflow: {str(e)}")
            return None
    
    def evaluate_rule(
        self, 
        rule_type: str, 
        rule_condition: str, 
        sql_query: str,
        server_alias: str = "",
        username: str = "",
        parsed_query: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Evaluate a workflow rule against a query
        
        Args:
            rule_type: Type of rule (table, schema, regex, etc.)
            rule_condition: Rule condition
            sql_query: SQL query to evaluate
            server_alias: Target server alias
            username: Username of the requester
            parsed_query: Optional pre-parsed query
            
        Returns:
            True if rule matches, False otherwise
        """
        try:
            # Parse query if not already parsed
            if not parsed_query:
                parsed_query = self.sql_parser.parse_query(sql_query)
                if not parsed_query:
                    logger.warning(f"Unable to parse SQL query for rule evaluation: {sql_query[:100]}...")
                    return False
            
            # Check rule type
            if rule_type == 'table':
                # Rule based on tables accessed
                tables = parsed_query.get('tables', [])
                condition_tables = [t.strip().lower() for t in rule_condition.split(',')]
                return any(table.lower() in condition_tables for table in tables)
            
            elif rule_type == 'schema':
                # Rule based on schema accessed
                # Extract schema from tables (assuming format "schema.table")
                schemas = []
                for table in parsed_query.get('tables', []):
                    if '.' in table:
                        schema = table.split('.')[0].lower()
                        schemas.append(schema)
                
                condition_schemas = [s.strip().lower() for s in rule_condition.split(',')]
                return any(schema in condition_schemas for schema in schemas)
            
            elif rule_type == 'server':
                # Rule based on target server
                condition_servers = [s.strip().lower() for s in rule_condition.split(',')]
                return server_alias.lower() in condition_servers
            
            elif rule_type == 'query_type':
                # Rule based on query type
                query_type = parsed_query.get('query_type', '').upper()
                condition_types = [t.strip().upper() for t in rule_condition.split(',')]
                return query_type in condition_types
            
            elif rule_type == 'user':
                # Rule based on requesting user
                condition_users = [u.strip().lower() for u in rule_condition.split(',')]
                return username.lower() in condition_users
            
            elif rule_type == 'role':
                # Rule based on user role
                # Note: This requires external role information
                # For example usage only, assuming role would be passed separately
                user_role = username.split(':')[1] if ':' in username else ''
                condition_roles = [r.strip().lower() for r in rule_condition.split(',')]
                return user_role.lower() in condition_roles
            
            elif rule_type == 'regex':
                # Rule based on regex pattern
                try:
                    pattern = re.compile(rule_condition, re.IGNORECASE)
                    return bool(pattern.search(sql_query))
                except Exception as re_error:
                    logger.error(f"Invalid regex pattern '{rule_condition}': {str(re_error)}")
                    return False
            
            elif rule_type == 'tables_modified':
                # Rule based on tables being modified (for UPDATE/INSERT/DELETE)
                query_type = parsed_query.get('query_type', '').upper()
                if query_type not in ['UPDATE', 'INSERT', 'DELETE', 'TRUNCATE']:
                    return False
                
                tables = parsed_query.get('tables', [])
                condition_tables = [t.strip().lower() for t in rule_condition.split(',')]
                return any(table.lower() in condition_tables for table in tables)
            
            # Unknown rule type
            logger.warning(f"Unknown rule type: {rule_type}")
            return False
        
        except Exception as e:
            logger.error(f"Error evaluating rule: {str(e)}")
            return False
    
    def create_workflow_instance(
        self, 
        workflow_id: int, 
        query_id: int,
        db: Session = None
    ) -> Optional[ApprovalInstance]:
        """
        Create a new workflow instance for a query
        
        Args:
            workflow_id: ID of the workflow to instantiate
            query_id: ID of the query pending approval
            db: Database session (if not provided at initialization)
            
        Returns:
            Created ApprovalInstance or None if creation failed
        """
        # Use provided DB session or the one from initialization
        db_session = db or self.db
        if not db_session:
            logger.error("No database session provided")
            return None
        
        try:
            # Get the workflow
            workflow = db_session.query(ApprovalWorkflow).filter(
                ApprovalWorkflow.id == workflow_id
            ).first()
            
            if not workflow:
                logger.error(f"Workflow with ID {workflow_id} not found")
                return None
            
            # Check if query exists
            query = db_session.query(PendingApproval).filter(
                PendingApproval.id == query_id
            ).first()
            
            if not query:
                logger.error(f"Query with ID {query_id} not found")
                return None
            
            # Check if an instance already exists for this query
            existing_instance = db_session.query(ApprovalInstance).filter(
                ApprovalInstance.query_id == query_id
            ).first()
            
            if existing_instance:
                logger.warning(f"Workflow instance already exists for query {query_id}")
                return existing_instance
            
            # Get workflow steps
            steps = db_session.query(ApprovalStep).filter(
                ApprovalStep.workflow_id == workflow_id
            ).order_by(ApprovalStep.step_order).all()
            
            if not steps:
                logger.error(f"No steps found for workflow {workflow_id}")
                return None
            
            # Create workflow instance
            instance = ApprovalInstance(
                workflow_id=workflow.id,
                workflow_name=workflow.name,
                query_id=query.id,
                current_step=1,  # Start with first step
                status='pending'
            )
            
            db_session.add(instance)
            db_session.flush()  # Get instance ID
            
            # Create step instances
            for step in steps:
                step_instance = StepInstance(
                    instance_id=instance.id,
                    step_name=step.name,
                    step_description=step.description,
                    approver_type=step.approver_type,
                    approver_value=step.approver_value,
                    step_order=step.step_order,
                    is_required=step.is_required,
                    status='pending'
                )
                
                db_session.add(step_instance)
            
            # Update query status
            query.status = 'approval_workflow'
            query.workflow_instance_id = instance.id
            
            # Commit changes
            db_session.commit()
            
            logger.info(f"Created workflow instance {instance.id} for query {query_id}")
            
            return instance
        
        except Exception as e:
            logger.error(f"Error creating workflow instance: {str(e)}")
            db_session.rollback()
            return None
    
    def advance_workflow(
        self, 
        instance_id: int, 
        approved: bool,
        approver: str,
        comment: str = "",
        db: Session = None
    ) -> Tuple[bool, str]:
        """
        Advance a workflow instance to the next step or complete it
        
        Args:
            instance_id: ID of the workflow instance
            approved: Whether the current step is approved or rejected
            approver: Username of the approver
            comment: Optional comment from the approver
            db: Database session (if not provided at initialization)
            
        Returns:
            Tuple of (success, message)
        """
        # Use provided DB session or the one from initialization
        db_session = db or self.db
        if not db_session:
            logger.error("No database session provided")
            return False, "No database session provided"
        
        try:
            # Get the workflow instance
            instance = db_session.query(ApprovalInstance).filter(
                ApprovalInstance.id == instance_id
            ).first()
            
            if not instance:
                return False, f"Workflow instance with ID {instance_id} not found"
            
            # Check if instance is already completed
            if instance.status in ['approved', 'rejected', 'cancelled']:
                return False, f"Workflow instance is already {instance.status}"
            
            # Get the current step instance
            current_step = db_session.query(StepInstance).filter(
                StepInstance.instance_id == instance_id,
                StepInstance.step_order == instance.current_step
            ).first()
            
            if not current_step:
                return False, f"Current step {instance.current_step} not found"
            
            # Update current step
            current_step.status = 'approved' if approved else 'rejected'
            current_step.approver_comment = comment
            current_step.approved_by = approver
            current_step.approved_at = datetime.utcnow()
            
            # Get the pending approval
            query = db_session.query(PendingApproval).filter(
                PendingApproval.id == instance.query_id
            ).first()
            
            if not query:
                return False, f"Query with ID {instance.query_id} not found"
            
            if not approved:
                # If step is rejected, reject the entire workflow
                instance.status = 'rejected'
                
                # Update the query
                query.status = 'rejected'
                query.rejected_by = approver
                query.rejected_at = datetime.utcnow()
                query.rejection_reason = comment
                
                db_session.commit()
                
                return True, "Workflow rejected"
            
            # Step was approved, check if there are more steps
            next_step = db_session.query(StepInstance).filter(
                StepInstance.instance_id == instance_id,
                StepInstance.step_order > instance.current_step,
                StepInstance.is_required == True  # Only required steps count
            ).order_by(StepInstance.step_order).first()
            
            if next_step:
                # Move to next step
                instance.current_step = next_step.step_order
                instance.updated_at = datetime.utcnow()
                
                # If this is the first step approval, update status
                if instance.status == 'pending':
                    instance.status = 'in_progress'
                
                db_session.commit()
                
                return True, f"Advanced to step {next_step.step_order}: {next_step.step_name}"
            
            # No more steps, workflow is completed
            instance.status = 'approved'
            
            # Update the query
            query.status = 'approved'
            query.approved_by = approver
            query.approved_at = datetime.utcnow()
            query.approver_comment = f"Approved through workflow: {instance.workflow_name}"
            
            db_session.commit()
            
            return True, "Workflow completed and approved"
        
        except Exception as e:
            logger.error(f"Error advancing workflow: {str(e)}")
            db_session.rollback()
            return False, f"Error: {str(e)}"

# Son güncelleme: 2025-05-20 07:47:46
# Güncelleyen: Teeksss