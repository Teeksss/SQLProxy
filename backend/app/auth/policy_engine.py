"""
Advanced Authorization Policy Engine for SQL Proxy

This module provides a powerful policy engine for fine-grained
authorization control, supporting complex rules and conditions.

Last updated: 2025-05-20 10:44:00
Updated by: Teeksss
"""

import logging
import json
import re
from typing import Dict, List, Any, Optional, Set, Union, Callable
from datetime import datetime, time, timedelta
import threading
import importlib
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.policy import AuthPolicy, PolicyRule, PolicyCondition
from app.models.user import User
from app.core.config import settings

logger = logging.getLogger(__name__)

@dataclass
class AuthorizationContext:
    """Authorization context for policy evaluation"""
    user: User
    action: str
    resource: str
    context: Dict[str, Any]
    server_alias: Optional[str] = None
    tables: Optional[List[str]] = None
    columns: Optional[List[str]] = None
    condition: Optional[str] = None
    client_ip: Optional[str] = None
    session_id: Optional[str] = None
    query_type: Optional[str] = None
    query_text: Optional[str] = None

@dataclass
class AuthorizationResult:
    """Result of authorization decision"""
    allowed: bool
    policy_id: Optional[int] = None
    policy_name: Optional[str] = None
    rule_id: Optional[int] = None
    rule_name: Optional[str] = None
    message: Optional[str] = None
    reason: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class PolicyEngine:
    """
    Advanced authorization policy engine
    
    Provides policy-based authorization decisions for SQL Proxy actions.
    """
    
    def __init__(self):
        """Initialize the policy engine"""
        self.policies = {}
        self.policy_lock = threading.RLock()
        self.policy_last_updated = datetime.min
        self.policy_update_interval = settings.POLICY_UPDATE_INTERVAL_SECONDS
        self.cache_enabled = settings.POLICY_CACHE_ENABLED
        self.custom_functions = {}
        
        # Register built-in condition functions
        self._register_builtin_functions()
        
        logger.info("Policy engine initialized")
    
    def _register_builtin_functions(self):
        """Register built-in condition functions"""
        self.register_function("in_time_window", self._in_time_window)
        self.register_function("match_ip_range", self._match_ip_range)
        self.register_function("match_regex", self._match_regex)
        self.register_function("is_weekend", self._is_weekend)
        self.register_function("is_business_hours", self._is_business_hours)
        self.register_function("has_role", self._has_role)
        self.register_function("table_in_list", self._table_in_list)
        self.register_function("all_tables_in_list", self._all_tables_in_list)
        self.register_function("any_table_in_list", self._any_table_in_list)
        self.register_function("column_in_list", self._column_in_list)
        self.register_function("has_where_clause", self._has_where_clause)
        self.register_function("row_limit_under", self._row_limit_under)
    
    def register_function(self, name: str, func: Callable):
        """
        Register a custom function for use in policy conditions
        
        Args:
            name: Function name
            func: Function implementation
        """
        self.custom_functions[name] = func
    
    def load_policies(self, db: Session):
        """
        Load authorization policies from database
        
        Args:
            db: Database session
        """
        try:
            # Check if policies need updating
            current_time = datetime.utcnow()
            
            with self.policy_lock:
                if (current_time - self.policy_last_updated).total_seconds() < self.policy_update_interval:
                    # Policies are fresh enough
                    return
            
            # Load policies
            policies = db.query(AuthPolicy).filter(AuthPolicy.is_active == True).all()
            
            # Build policy dictionary
            policy_dict = {}
            
            for policy in policies:
                # Load rules for this policy
                rules = db.query(PolicyRule).filter(
                    PolicyRule.policy_id == policy.id,
                    PolicyRule.is_active == True
                ).order_by(PolicyRule.priority).all()
                
                # Process rules
                processed_rules = []
                
                for rule in rules:
                    # Load conditions for this rule
                    conditions = db.query(PolicyCondition).filter(
                        PolicyCondition.rule_id == rule.id,
                        PolicyCondition.is_active == True
                    ).all()
                    
                    # Process conditions
                    processed_conditions = []
                    
                    for condition in conditions:
                        processed_conditions.append({
                            "id": condition.id,
                            "field": condition.field,
                            "operator": condition.operator,
                            "value": condition.value,
                            "function": condition.function,
                            "parameters": json.loads(condition.parameters) if condition.parameters else {},
                            "description": condition.description
                        })
                    
                    # Add processed rule
                    processed_rules.append({
                        "id": rule.id,
                        "name": rule.name,
                        "description": rule.description,
                        "priority": rule.priority,
                        "effect": rule.effect,
                        "conditions": processed_conditions,
                        "message": rule.message,
                        "all_conditions_required": rule.all_conditions_required,
                        "is_active": rule.is_active,
                        "metadata": json.loads(rule.metadata) if rule.metadata else {}
                    })
                
                # Add processed policy
                policy_dict[policy.id] = {
                    "id": policy.id,
                    "name": policy.name,
                    "description": policy.description,
                    "resource_type": policy.resource_type,
                    "priority": policy.priority,
                    "rules": processed_rules,
                    "default_effect": policy.default_effect,
                    "is_active": policy.is_active,
                    "metadata": json.loads(policy.metadata) if policy.metadata else {}
                }
            
            # Update policies with lock
            with self.policy_lock:
                self.policies = policy_dict
                self.policy_last_updated = current_time
            
            logger.info(f"Loaded {len(policies)} authorization policies with {sum(len(p['rules']) for p in policy_dict.values())} rules")
            
        except Exception as e:
            logger.error(f"Error loading authorization policies: {str(e)}")
    
    def evaluate(self, context: AuthorizationContext, db: Session) -> AuthorizationResult:
        """
        Evaluate authorization policies for a request
        
        Args:
            context: Authorization context
            db: Database session
            
        Returns:
            Authorization result
        """
        # Ensure policies are loaded
        if not self.policies:
            self.load_policies(db)
        
        # Filter policies relevant to this resource type
        relevant_policies = [
            policy for policy in self.policies.values()
            if policy["resource_type"] == context.resource or policy["resource_type"] == '*'
        ]
        
        # Sort policies by priority (higher priority first)
        relevant_policies.sort(key=lambda p: p["priority"], reverse=True)
        
        # Evaluate policies
        for policy in relevant_policies:
            result = self._evaluate_policy(policy, context)
            
            if result is not None:
                return result
        
        # No policy matched, default to deny
        return AuthorizationResult(
            allowed=False,
            message="No matching policy found",
            reason="default_deny"
        )
    
    def _evaluate_policy(self, policy: Dict[str, Any], context: AuthorizationContext) -> Optional[AuthorizationResult]:
        """
        Evaluate a single policy
        
        Args:
            policy: Policy to evaluate
            context: Authorization context
            
        Returns:
            Authorization result or None if no rules matched
        """
        # Sort rules by priority (higher priority first)
        rules = sorted(policy["rules"], key=lambda r: r["priority"], reverse=True)
        
        for rule in rules:
            # Check if rule applies to this action
            if not self._rule_applies_to_action(rule, context.action):
                continue
            
            # Evaluate rule conditions
            matches = self._evaluate_rule_conditions(rule, context)
            
            if matches:
                # Rule matched, return result
                allowed = rule["effect"] == "allow"
                
                return AuthorizationResult(
                    allowed=allowed,
                    policy_id=policy["id"],
                    policy_name=policy["name"],
                    rule_id=rule["id"],
                    rule_name=rule["name"],
                    message=rule["message"],
                    reason=f"rule_{rule['id']}",
                    metadata=rule["metadata"]
                )
        
        # No rules matched, use policy default
        if policy["default_effect"] is not None:
            return AuthorizationResult(
                allowed=policy["default_effect"] == "allow",
                policy_id=policy["id"],
                policy_name=policy["name"],
                message=f"Default policy effect: {policy['default_effect']}",
                reason="policy_default"
            )
        
        # No default effect, policy doesn't match
        return None
    
    def _rule_applies_to_action(self, rule: Dict[str, Any], action: str) -> bool:
        """
        Check if a rule applies to an action
        
        Args:
            rule: Rule to check
            action: Action to check
            
        Returns:
            True if rule applies to action
        """
        # Check if rule has an action condition
        for condition in rule["conditions"]:
            if condition["field"] == "action":
                # Direct action match
                if condition["operator"] == "eq" and condition["value"] == action:
                    return True
                
                # Action in list
                if condition["operator"] == "in" and action in condition["value"].split(","):
                    return True
                
                # Action matches regex
                if condition["operator"] == "regex" and re.match(condition["value"], action):
                    return True
        
        # No action condition means rule applies to all actions
        return True
    
    def _evaluate_rule_conditions(self, rule: Dict[str, Any], context: AuthorizationContext) -> bool:
        """
        Evaluate rule conditions
        
        Args:
            rule: Rule to evaluate
            context: Authorization context
            
        Returns:
            True if conditions match
        """
        # If no conditions, rule matches
        if not rule["conditions"]:
            return True
        
        # Evaluate each condition
        condition_results = []
        
        for condition in rule["conditions"]:
            result = self._evaluate_condition(condition, context)
            condition_results.append(result)
        
        # Determine overall result
        if rule["all_conditions_required"]:
            # All conditions must match
            return all(condition_results)
        else:
            # At least one condition must match
            return any(condition_results)
    
    def _evaluate_condition(self, condition: Dict[str, Any], context: AuthorizationContext) -> bool:
        """
        Evaluate a single condition
        
        Args:
            condition: Condition to evaluate
            context: Authorization context
            
        Returns:
            True if condition matches
        """
        # If condition has a function, call it
        if condition["function"]:
            return self._call_condition_function(
                condition["function"],
                context,
                condition["parameters"]
            )
        
        # Get field value from context
        field_value = self._get_context_field(condition["field"], context)
        
        # If field not found in context, condition fails
        if field_value is None:
            return False
        
        # Get condition value
        condition_value = condition["value"]
        
        # Evaluate based on operator
        operator = condition["operator"]
        
        if operator == "eq":
            return str(field_value) == str(condition_value)
        
        elif operator == "neq":
            return str(field_value) != str(condition_value)
        
        elif operator == "in":
            if isinstance(condition_value, str):
                values = [v.strip() for v in condition_value.split(",")]
                return str(field_value) in values
            return False
        
        elif operator == "not_in":
            if isinstance(condition_value, str):
                values = [v.strip() for v in condition_value.split(",")]
                return str(field_value) not in values
            return False
        
        elif operator == "contains":
            return str(condition_value) in str(field_value)
        
        elif operator == "not_contains":
            return str(condition_value) not in str(field_value)
        
        elif operator == "starts_with":
            return str(field_value).startswith(str(condition_value))
        
        elif operator == "ends_with":
            return str(field_value).endswith(str(condition_value))
        
        elif operator == "regex":
            try:
                return bool(re.match(condition_value, str(field_value)))
            except:
                return False
        
        elif operator == "gt":
            try:
                return float(field_value) > float(condition_value)
            except:
                return False
        
        elif operator == "gte":
            try:
                return float(field_value) >= float(condition_value)
            except:
                return False
        
        elif operator == "lt":
            try:
                return float(field_value) < float(condition_value)
            except:
                return False
        
        elif operator == "lte":
            try:
                return float(field_value) <= float(condition_value)
            except:
                return False
        
        # Unknown operator
        logger.warning(f"Unknown condition operator: {operator}")
        return False
    
    def _get_context_field(self, field: str, context: AuthorizationContext) -> Any:
        """
        Get a field value from the context
        
        Args:
            field: Field name
            context: Authorization context
            
        Returns:
            Field value or None if not found
        """
        # Check direct attributes first
        if hasattr(context, field):
            return getattr(context, field)
        
        # Check nested attributes
        parts = field.split('.')
        
        if parts[0] == 'user' and len(parts) > 1 and context.user:
            if hasattr(context.user, parts[1]):
                return getattr(context.user, parts[1])
        
        # Check context dictionary
        if field in context.context:
            return context.context[field]
        
        # Field not found
        return None
    
    def _call_condition_function(
        self,
        function_name: str,
        context: AuthorizationContext,
        parameters: Dict[str, Any]
    ) -> bool:
        """
        Call a condition function
        
        Args:
            function_name: Function name
            context: Authorization context
            parameters: Function parameters
            
        Returns:
            Function result
        """
        # Check if function exists
        if function_name not in self.custom_functions:
            logger.warning(f"Unknown condition function: {function_name}")
            return False
        
        # Call function
        try:
            return self.custom_functions[function_name](context, parameters)
        except Exception as e:
            logger.error(f"Error calling condition function {function_name}: {str(e)}")
            return False
    
    # Built-in condition functions
    
    def _in_time_window(self, context: AuthorizationContext, parameters: Dict[str, Any]) -> bool:
        """
        Check if current time is within a time window
        
        Args:
            context: Authorization context
            parameters: Function parameters
            
        Returns:
            True if time is within window
        """
        try:
            # Get parameters
            start_time = parameters.get("start_time")
            end_time = parameters.get("end_time")
            
            if not start_time or not end_time:
                return False
            
            # Parse time strings
            try:
                start = datetime.strptime(start_time, "%H:%M").time()
                end = datetime.strptime(end_time, "%H:%M").time()
            except ValueError:
                logger.error(f"Invalid time format for in_time_window: {start_time} - {end_time}")
                return False
            
            # Get current time
            now = datetime.utcnow().time()
            
            # Handle overnight windows (e.g., 22:00 - 06:00)
            if start > end:
                return now >= start or now <= end
            else:
                return start <= now <= end
            
        except Exception as e:
            logger.error(f"Error in in_time_window function: {str(e)}")
            return False
    
    def _match_ip_range(self, context: AuthorizationContext, parameters: Dict[str, Any]) -> bool:
        """
        Check if client IP is within a range
        
        Args:
            context: Authorization context
            parameters: Function parameters
            
        Returns:
            True if IP is within range
        """
        try:
            # Get parameters
            ip_ranges = parameters.get("ip_ranges", [])
            
            if not ip_ranges or not context.client_ip:
                return False
            
            # Convert IP to integer
            client_ip = context.client_ip.strip()
            ip_parts = client_ip.split('.')
            
            if len(ip_parts) != 4:
                return False
            
            client_ip_int = (int(ip_parts[0]) << 24) + (int(ip_parts[1]) << 16) + \
                         (int(ip_parts[2]) << 8) + int(ip_parts[3])
            
            # Check if IP is in any range
            for ip_range in ip_ranges:
                if '-' in ip_range:
                    # Range specified as start-end
                    start_ip, end_ip = ip_range.split('-')
                    
                    # Convert start IP to integer
                    start_parts = start_ip.strip().split('.')
                    if len(start_parts) != 4:
                        continue
                    
                    start_ip_int = (int(start_parts[0]) << 24) + (int(start_parts[1]) << 16) + \
                                (int(start_parts[2]) << 8) + int(start_parts[3])
                    
                    # Convert end IP to integer
                    end_parts = end_ip.strip().split('.')
                    if len(end_parts) != 4:
                        continue
                    
                    end_ip_int = (int(end_parts[0]) << 24) + (int(end_parts[1]) << 16) + \
                              (int(end_parts[2]) << 8) + int(end_parts[3])
                    
                    # Check if IP is in range
                    if start_ip_int <= client_ip_int <= end_ip_int:
                        return True
                
                elif '/' in ip_range:
                    # Range specified as CIDR
                    network, bits = ip_range.split('/')
                    
                    # Convert network to integer
                    network_parts = network.strip().split('.')
                    if len(network_parts) != 4:
                        continue
                    
                    network_int = (int(network_parts[0]) << 24) + (int(network_parts[1]) << 16) + \
                               (int(network_parts[2]) << 8) + int(network_parts[3])
                    
                    # Calculate subnet mask
                    mask = (0xffffffff << (32 - int(bits))) & 0xffffffff
                    
                    # Check if IP is in network
                    if (client_ip_int & mask) == (network_int & mask):
                        return True
                else:
                    # Single IP
                    if ip_range.strip() == client_ip:
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error in match_ip_range function: {str(e)}")
            return False
    
    def _match_regex(self, context: AuthorizationContext, parameters: Dict[str, Any]) -> bool:
        """
        Check if a field matches a regex pattern
        
        Args:
            context: Authorization context
            parameters: Function parameters
            
        Returns:
            True if field matches regex
        """
        try:
            # Get parameters
            field = parameters.get("field")
            pattern = parameters.get("pattern")
            
            if not field or not pattern:
                return False
            
            # Get field value
            field_value = self._get_context_field(field, context)
            
            if field_value is None:
                return False
            
            # Check if field matches regex
            return bool(re.match(pattern, str(field_value)))
            
        except Exception as e:
            logger.error(f"Error in match_regex function: {str(e)}")
            return False
    
    def _is_weekend(self, context: AuthorizationContext, parameters: Dict[str, Any]) -> bool:
        """
        Check if current day is a weekend
        
        Args:
            context: Authorization context
            parameters: Function parameters
            
        Returns:
            True if current day is a weekend
        """
        try:
            # Get current day of week (0=Monday, 6=Sunday)
            day_of_week = datetime.utcnow().weekday()
            
            # Weekend is Saturday (5) and Sunday (6)
            return day_of_week >= 5
            
        except Exception as e:
            logger.error(f"Error in is_weekend function: {str(e)}")
            return False
    
    def _is_business_hours(self, context: AuthorizationContext, parameters: Dict[str, Any]) -> bool:
        """
        Check if current time is during business hours
        
        Args:
            context: Authorization context
            parameters: Function parameters
            
        Returns:
            True if current time is during business hours
        """
        try:
            # Get parameters (default: 9:00-17:00)
            start_hour = parameters.get("start_hour", 9)
            end_hour = parameters.get("end_hour", 17)
            business_days = parameters.get("business_days", [0, 1, 2, 3, 4])  # Monday-Friday
            
            # Get current time
            now = datetime.utcnow()
            day_of_week = now.weekday()
            current_hour = now.hour
            
            # Check if current day is a business day
            if day_of_week not in business_days:
                return False
            
            # Check if current hour is within business hours
            return start_hour <= current_hour < end_hour
            
        except Exception as e:
            logger.error(f"Error in is_business_hours function: {str(e)}")
            return False
    
    def _has_role(self, context: AuthorizationContext, parameters: Dict[str, Any]) -> bool:
        """
        Check if user has a specific role
        
        Args:
            context: Authorization context
            parameters: Function parameters
            
        Returns:
            True if user has role
        """
        try:
            # Get parameters
            roles = parameters.get("roles", [])
            
            if not roles or not context.user:
                return False
            
            # Convert to list if string
            if isinstance(roles, str):
                roles = [r.strip() for r in roles.split(",")]
            
            # Check if user role is in roles list
            return context.user.role in roles
            
        except Exception as e:
            logger.error(f"Error in has_role function: {str(e)}")
            return False
    
    def _table_in_list(self, context: AuthorizationContext, parameters: Dict[str, Any]) -> bool:
        """
        Check if a specific table is in allowed list
        
        Args:
            context: Authorization context
            parameters: Function parameters
            
        Returns:
            True if table is in list
        """
        try:
            # Get parameters
            table_name = parameters.get("table_name")
            allowed_tables = parameters.get("allowed_tables", [])
            
            if not table_name or not allowed_tables:
                return False
            
            # Convert to list if string
            if isinstance(allowed_tables, str):
                allowed_tables = [t.strip() for t in allowed_tables.split(",")]
            
            # Check if table is in allowed list
            return table_name in allowed_tables
            
        except Exception as e:
            logger.error(f"Error in table_in_list function: {str(e)}")
            return False
    
    def _all_tables_in_list(self, context: AuthorizationContext, parameters: Dict[str, Any]) -> bool:
        """
        Check if all tables in query are in allowed list
        
        Args:
            context: Authorization context
            parameters: Function parameters
            
        Returns:
            True if all tables are in list
        """
        try:
            # Get parameters
            allowed_tables = parameters.get("allowed_tables", [])
            
            if not allowed_tables or not context.tables:
                return False
            
            # Convert to list if string
            if isinstance(allowed_tables, str):
                allowed_tables = [t.strip() for t in allowed_tables.split(",")]
            
            # Check if all tables are in allowed list
            return all(table in allowed_tables for table in context.tables)
            
        except Exception as e:
            logger.error(f"Error in all_tables_in_list function: {str(e)}")
            return False
    
    def _any_table_in_list(self, context: AuthorizationContext, parameters: Dict[str, Any]) -> bool:
        """
        Check if any table in query is in allowed list
        
        Args:
            context: Authorization context
            parameters: Function parameters
            
        Returns:
            True if any table is in list
        """
        try:
            # Get parameters
            allowed_tables = parameters.get("allowed_tables", [])
            
            if not allowed_tables or not context.tables:
                return False
            
            # Convert to list if string
            if isinstance(allowed_tables, str):
                allowed_tables = [t.strip() for t in allowed_tables.split(",")]
            
            # Check if any table is in allowed list
            return any(table in allowed_tables for table in context.tables)
            
        except Exception as e:
            logger.error(f"Error in any_table_in_list function: {str(e)}")
            return False
    
    def _column_in_list(self, context: AuthorizationContext, parameters: Dict[str, Any]) -> bool:
        """
        Check if a specific column is in allowed list
        
        Args:
            context: Authorization context
            parameters: Function parameters
            
        Returns:
            True if column is in list
        """
        try:
            # Get parameters
            column_name = parameters.get("column_name")
            allowed_columns = parameters.get("allowed_columns", [])
            
            if not column_name or not allowed_columns:
                return False
            
            # Convert to list if string
            if isinstance(allowed_columns, str):
                allowed_columns = [c.strip() for c in allowed_columns.split(",")]
            
            # Check if column is in allowed list
            return column_name in allowed_columns
            
        except Exception as e:
            logger.error(f"Error in column_in_list function: {str(e)}")
            return False
    
    def _has_where_clause(self, context: AuthorizationContext, parameters: Dict[str, Any]) -> bool:
        """
        Check if query has a WHERE clause
        
        Args:
            context: Authorization context
            parameters: Function parameters
            
        Returns:
            True if query has WHERE clause
        """
        try:
            if not context.query_text:
                return False
            
            # Check if query has WHERE clause
            return bool(re.search(r'\bWHERE\b', context.query_text, re.IGNORECASE))
            
        except Exception as e:
            logger.error(f"Error in has_where_clause function: {str(e)}")
            return False
    
    def _row_limit_under(self, context: AuthorizationContext, parameters: Dict[str, Any]) -> bool:
        """
        Check if query has a LIMIT clause under specified limit
        
        Args:
            context: Authorization context
            parameters: Function parameters
            
        Returns:
            True if query has LIMIT clause under limit
        """
        try:
            # Get parameters
            max_limit = parameters.get("max_limit", 1000)
            
            if not context.query_text:
                return False
            
            # Check if query has LIMIT clause
            limit_match = re.search(r'\bLIMIT\s+(\d+)', context.query_text, re.IGNORECASE)
            
            if not limit_match:
                return False
            
            # Check if limit is under specified limit
            limit_value = int(limit_match.group(1))
            return limit_value <= max_limit
            
        except Exception as e:
            logger.error(f"Error in row_limit_under function: {str(e)}")
            return False

# Create singleton instance
policy_engine = PolicyEngine()

# Son güncelleme: 2025-05-20 10:44:00
# Güncelleyen: Teeksss