"""
Policy template service for SQL Proxy

Provides functionality for managing and evaluating authorization policy templates
that define what SQL operations are allowed based on roles and other criteria.

Last updated: 2025-05-20 07:43:54
Updated by: Teeksss
"""

import logging
import re
from typing import Dict, List, Any, Optional, Set, Tuple
from sqlalchemy.orm import Session

from app.models.policy import PolicyTemplate, PolicyRule
from app.services.sql_parser import SQLParser

logger = logging.getLogger(__name__)

class PolicyTemplateService:
    """
    Service for evaluating policy templates against SQL queries
    
    Provides functionality to determine if a SQL query is allowed based on
    policy templates defined in the system.
    """
    
    def __init__(self):
        """Initialize the policy template service"""
        self.sql_parser = SQLParser()
        
        # Cache of policy templates - will be populated on first use
        self.policy_cache = {}
        self.policy_cache_timestamp = 0
        
        logger.info("Policy template service initialized")
    
    def load_policies(self, db: Session) -> Dict[str, Dict[str, Any]]:
        """
        Load all policy templates from the database
        
        Args:
            db: Database session
            
        Returns:
            Dictionary of policy templates indexed by ID
        """
        # Get all active policy templates
        templates = db.query(PolicyTemplate).filter(
            PolicyTemplate.is_active == True
        ).all()
        
        # Get all rules for these templates
        template_ids = [t.id for t in templates]
        rules = db.query(PolicyRule).filter(
            PolicyRule.policy_id.in_(template_ids)
        ).all()
        
        # Group rules by policy ID
        rules_by_policy = {}
        for rule in rules:
            if rule.policy_id not in rules_by_policy:
                rules_by_policy[rule.policy_id] = []
            rules_by_policy[rule.policy_id].append(rule)
        
        # Build policy cache
        policies = {}
        for template in templates:
            policy_rules = rules_by_policy.get(template.id, [])
            
            policies[template.id] = {
                'id': template.id,
                'name': template.name,
                'description': template.description,
                'priority': template.priority,
                'applicable_roles': template.applicable_roles,
                'applicable_servers': template.applicable_servers,
                'rules': [
                    {
                        'id': rule.id,
                        'rule_type': rule.rule_type,
                        'action': rule.action,
                        'condition': rule.condition,
                        'error_message': rule.error_message
                    }
                    for rule in policy_rules
                ]
            }
        
        return policies
    
    def get_policy_for_role_and_server(
        self, 
        role: str, 
        server_alias: Optional[str], 
        db: Session
    ) -> Optional[Dict[str, Any]]:
        """
        Get the highest priority policy template applicable for a role and server
        
        Args:
            role: User role
            server_alias: Target server alias (or None)
            db: Database session
            
        Returns:
            Policy template dictionary or None if no matching policy
        """
        # Refresh cache if needed
        self._refresh_cache_if_needed(db)
        
        # Filter applicable policies
        applicable_policies = []
        
        for policy_id, policy in self.policy_cache.items():
            # Check if role matches
            role_matches = False
            applicable_roles = policy['applicable_roles']
            
            if not applicable_roles:  # Empty means all roles
                role_matches = True
            elif role in applicable_roles:
                role_matches = True
            
            # Check if server matches
            server_matches = False
            applicable_servers = policy['applicable_servers']
            
            if not applicable_servers:  # Empty means all servers
                server_matches = True
            elif server_alias and server_alias in applicable_servers:
                server_matches = True
            
            # If both match, this policy is applicable
            if role_matches and server_matches:
                applicable_policies.append(policy)
        
        # Sort by priority (higher number = higher priority)
        applicable_policies.sort(key=lambda p: p['priority'], reverse=True)
        
        # Return highest priority policy or None if no matching policy
        return applicable_policies[0] if applicable_policies else None
    
    def evaluate_policy(
        self, 
        policy: Dict[str, Any], 
        sql_query: str, 
        user_info: Dict[str, Any] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Evaluate a policy against a SQL query
        
        Args:
            policy: Policy template dictionary
            sql_query: SQL query to evaluate
            user_info: Additional user context information
            
        Returns:
            Tuple of (allowed, error_message)
        """
        if not policy or not sql_query:
            return False, "No policy or query provided"
        
        # Parse the SQL query
        parsed_query = self.sql_parser.parse_query(sql_query)
        
        if not parsed_query:
            return False, "Unable to parse SQL query"
        
        # Track if any rule explicitly allows the query
        allowed = False
        
        # Evaluate each rule
        for rule in policy['rules']:
            rule_type = rule['rule_type']
            action = rule['action']
            condition = rule['condition']
            error_message = rule['error_message']
            
            # Check if rule applies to this query
            rule_applies = self._check_rule_applies(rule_type, condition, parsed_query, user_info)
            
            if rule_applies:
                if action == 'deny':
                    # Deny rules take precedence
                    return False, error_message
                elif action == 'allow':
                    # Mark as allowed, but keep checking other rules
                    allowed = True
            
        # If we made it here, no deny rules matched
        # Return allowed if any rule explicitly allowed the query
        return allowed, None
    
    def _check_rule_applies(
        self, 
        rule_type: str, 
        condition: str, 
        parsed_query: Dict[str, Any], 
        user_info: Optional[Dict[str, Any]]
    ) -> bool:
        """
        Check if a rule applies to a specific query
        
        Args:
            rule_type: Type of rule (query_type, contains_table, etc.)
            condition: Rule condition to check
            parsed_query: Parsed SQL query
            user_info: Additional user context information
            
        Returns:
            True if the rule applies, False otherwise
        """
        try:
            if rule_type == 'query_type':
                # Check query type (SELECT, INSERT, UPDATE, DELETE, etc.)
                query_type = parsed_query.get('query_type', '').upper()
                condition_types = [t.strip().upper() for t in condition.split(',')]
                return query_type in condition_types
            
            elif rule_type == 'contains_table':
                # Check if query references specific tables
                tables = parsed_query.get('tables', [])
                condition_tables = [t.strip().lower() for t in condition.split(',')]
                return any(table.lower() in condition_tables for table in tables)
            
            elif rule_type == 'contains_column':
                # Check if query references specific columns
                columns = parsed_query.get('columns', [])
                condition_columns = [c.strip().lower() for c in condition.split(',')]
                return any(col.lower() in condition_columns for col in columns)
            
            elif rule_type == 'has_where_clause':
                # Check if query has a WHERE clause
                if condition.lower() == 'true':
                    # Require WHERE clause
                    return parsed_query.get('where', False)
                elif condition.lower() == 'false':
                    # Require NO WHERE clause
                    return not parsed_query.get('where', False)
            
            elif rule_type == 'has_limit_clause':
                # Check if query has a LIMIT clause
                if condition.lower() == 'true':
                    # Require LIMIT clause
                    return parsed_query.get('limit') is not None
                elif condition.lower() == 'false':
                    # Require NO LIMIT clause
                    return parsed_query.get('limit') is None
            
            elif rule_type == 'matches_regex':
                # Check if query matches a regex pattern
                return bool(re.search(condition, parsed_query.get('query_text', '')))
            
            elif rule_type == 'user_context' and user_info:
                # Check user context (e.g., department, project, etc.)
                if '=' in condition:
                    key, value = condition.split('=', 1)
                    return user_info.get(key.strip()) == value.strip()
            
            elif rule_type == 'max_limit':
                # Check if LIMIT is below a certain threshold
                limit = parsed_query.get('limit')
                if limit is not None and condition.isdigit():
                    return int(limit) <= int(condition)
            
            elif rule_type == 'time_of_day':
                # Check if current time is within allowed range
                # Implementation depends on how time of day is passed in user_info
                if user_info and 'current_hour' in user_info:
                    if '-' in condition:
                        start_hour, end_hour = map(int, condition.split('-'))
                        current_hour = user_info['current_hour']
                        return start_hour <= current_hour <= end_hour
            
            # Default: rule doesn't apply
            return False
        
        except Exception as e:
            logger.error(f"Error checking policy rule: {str(e)}")
            return False
    
    def _refresh_cache_if_needed(self, db: Session):
        """
        Refresh the policy cache if needed
        
        Args:
            db: Database session
        """
        # In a real implementation, you would check if the cache is stale
        # by comparing to the latest modification timestamp in the DB
        # For simplicity, we'll just reload the cache if it's empty
        if not self.policy_cache:
            self.policy_cache = self.load_policies(db)
            self.policy_cache_timestamp = int(time.time())
    
    def create_policy_template(
        self, 
        db: Session, 
        name: str, 
        description: str, 
        applicable_roles: List[str],
        applicable_servers: List[str],
        priority: int,
        created_by: str
    ) -> Optional[Dict[str, Any]]:
        """
        Create a new policy template
        
        Args:
            db: Database session
            name: Policy template name
            description: Policy template description
            applicable_roles: List of roles this policy applies to
            applicable_servers: List of servers this policy applies to
            priority: Priority of this policy
            created_by: Username of the creator
            
        Returns:
            Created policy template as dictionary or None if creation failed
        """
        try:
            # Create the policy template
            policy = PolicyTemplate(
                name=name,
                description=description,
                applicable_roles=applicable_roles,
                applicable_servers=applicable_servers,
                priority=priority,
                is_active=True,
                created_by=created_by
            )
            
            db.add(policy)
            db.commit()
            db.refresh(policy)
            
            # Clear cache to force reload
            self.policy_cache = {}
            
            return {
                'id': policy.id,
                'name': policy.name,
                'description': policy.description,
                'applicable_roles': policy.applicable_roles,
                'applicable_servers': policy.applicable_servers,
                'priority': policy.priority,
                'is_active': policy.is_active,
                'created_by': policy.created_by,
                'created_at': policy.created_at.isoformat(),
                'rules': []
            }
        
        except Exception as e:
            logger.error(f"Error creating policy template: {str(e)}")
            db.rollback()
            return None
    
    def add_rule_to_policy(
        self, 
        db: Session, 
        policy_id: int, 
        rule_type: str, 
        action: str, 
        condition: str, 
        error_message: str
    ) -> Optional[Dict[str, Any]]:
        """
        Add a rule to a policy template
        
        Args:
            db: Database session
            policy_id: ID of the policy template
            rule_type: Type of rule
            action: Rule action (allow, deny)
            condition: Rule condition
            error_message: Error message to display when rule is violated
            
        Returns:
            Created rule as dictionary or None if creation failed
        """
        try:
            # Create the rule
            rule = PolicyRule(
                policy_id=policy_id,
                rule_type=rule_type,
                action=action,
                condition=condition,
                error_message=error_message
            )
            
            db.add(rule)
            db.commit()
            db.refresh(rule)
            
            # Clear cache to force reload
            self.policy_cache = {}
            
            return {
                'id': rule.id,
                'policy_id': rule.policy_id,
                'rule_type': rule.rule_type,
                'action': rule.action,
                'condition': rule.condition,
                'error_message': rule.error_message
            }
        
        except Exception as e:
            logger.error(f"Error adding rule to policy: {str(e)}")
            db.rollback()
            return None

import time  # Import was missing

# Create a singleton instance
policy_template_service = PolicyTemplateService()

# Son güncelleme: 2025-05-20 07:43:54
# Güncelleyen: Teeksss