"""
Data Masking Service for SQL Proxy

This module provides functionality for masking sensitive data
in query results and managing masking rules.

Last updated: 2025-05-20 14:44:45
Updated by: Teeksss
"""

import re
import json
import logging
import hashlib
import random
import string
from typing import Dict, List, Any, Optional, Tuple, Set, Pattern, Union, Callable
from pathlib import Path
from datetime import datetime

from fastapi import Depends

from app.core.config import settings
from app.db.session import get_db
from app.models.masking import MaskingRule, MaskingType
from app.models.user import User
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

class MaskingPattern:
    """Predefined patterns for sensitive data detection"""
    
    # Credit card numbers
    CREDIT_CARD = r'\b(?:\d{4}[ -]?){3}\d{4}\b|\b\d{16}\b'
    
    # Social Security Numbers (SSN)
    SSN = r'\b\d{3}[-]?\d{2}[-]?\d{4}\b'
    
    # Email addresses
    EMAIL = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    
    # Phone numbers (various formats)
    PHONE = r'\b(?:\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'
    
    # IP addresses
    IP_ADDRESS = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
    
    # Dates in various formats
    DATE = r'\b\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4}\b|\b\d{4}[/.-]\d{1,2}[/.-]\d{1,2}\b'
    
    # Passport numbers (generic pattern)
    PASSPORT = r'\b[A-Za-z0-9]{6,9}\b'
    
    # Bank account numbers (generic pattern)
    BANK_ACCOUNT = r'\b\d{8,12}\b'
    
    # Names (more challenging, but this is a simple pattern)
    NAME = r'\b[A-Z][a-z]+ [A-Z][a-z]+\b'
    
    # Address (generic pattern - looks for 'Street', 'Avenue', etc.)
    ADDRESS = r'\b\d+\s+[A-Za-z]+\s+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Court|Ct|Way|Place|Pl|Terrace|Ter)\b'
    
    # National ID/Identification Numbers (generic pattern)
    NATIONAL_ID = r'\b[A-Za-z0-9]{5,12}\b'
    
    # URLs
    URL = r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+'
    
    # GPS coordinates
    GPS = r'\b-?\d{1,3}\.\d{6,},\s*-?\d{1,3}\.\d{6,}\b'

class DataMaskingService:
    """
    Service for masking sensitive data
    
    Provides functionality for detecting and masking sensitive data in query results
    according to predefined and custom rules.
    """
    
    def __init__(self):
        """Initialize data masking service"""
        self.enabled = settings.DATA_MASKING_ENABLED
        self.rules_path = Path(settings.DATA_MASKING_RULES_PATH)
        
        # Initialize masking rules
        self.global_rules = []
        self.column_rules = {}
        self.compiled_patterns = {}
        
        # Load masking rules
        self._load_masking_rules()
        
        # Set up common PII matchers
        self._setup_pii_matchers()
        
        logger.info(f"Data masking service initialized, enabled: {self.enabled}")
    
    def _setup_pii_matchers(self):
        """Set up matchers for common types of PII data"""
        
        self.pii_matchers = {
            "creditcard": {
                "pattern": re.compile(MaskingPattern.CREDIT_CARD),
                "mask_function": lambda match, _: self._mask_credit_card(match.group(0))
            },
            "ssn": {
                "pattern": re.compile(MaskingPattern.SSN),
                "mask_function": lambda match, _: "XXX-XX-" + match.group(0)[-4:]
            },
            "email": {
                "pattern": re.compile(MaskingPattern.EMAIL),
                "mask_function": lambda match, _: self._mask_email(match.group(0))
            },
            "phone": {
                "pattern": re.compile(MaskingPattern.PHONE),
                "mask_function": lambda match, _: self._mask_phone(match.group(0))
            },
            "ipaddress": {
                "pattern": re.compile(MaskingPattern.IP_ADDRESS),
                "mask_function": lambda match, _: "XXX.XXX.XXX.XXX"
            },
            "date": {
                "pattern": re.compile(MaskingPattern.DATE),
                "mask_function": lambda match, _: "XXXX-XX-XX"
            },
            "passport": {
                "pattern": re.compile(MaskingPattern.PASSPORT),
                "mask_function": lambda match, _: "XXXXXXXX"
            },
            "bankaccount": {
                "pattern": re.compile(MaskingPattern.BANK_ACCOUNT),
                "mask_function": lambda match, _: "XXXX" + match.group(0)[-4:]
            },
            "name": {
                "pattern": re.compile(MaskingPattern.NAME),
                "mask_function": lambda match, _: self._mask_name(match.group(0))
            },
            "address": {
                "pattern": re.compile(MaskingPattern.ADDRESS),
                "mask_function": lambda match, _: "[REDACTED ADDRESS]"
            },
            "nationalid": {
                "pattern": re.compile(MaskingPattern.NATIONAL_ID),
                "mask_function": lambda match, _: "XXX" + match.group(0)[-4:]
            },
            "url": {
                "pattern": re.compile(MaskingPattern.URL),
                "mask_function": lambda match, _: "[REDACTED URL]"
            },
            "gps": {
                "pattern": re.compile(MaskingPattern.GPS),
                "mask_function": lambda match, _: "[REDACTED GPS]"
            }
        }
    
    def _load_masking_rules(self) -> None:
        """Load masking rules from configuration"""
        try:
            # Clear existing rules
            self.global_rules = []
            self.column_rules = {}
            self.compiled_patterns = {}
            
            # Load from file if exists
            if self.rules_path.exists():
                with open(self.rules_path, 'r') as f:
                    rules_config = json.load(f)
                
                # Process global rules
                for rule in rules_config.get('global_rules', []):
                    self.global_rules.append({
                        'name': rule.get('name', 'Unnamed Rule'),
                        'pattern': rule.get('pattern', ''),
                        'type': rule.get('type', 'hash'),
                        'description': rule.get('description', ''),
                        'enabled': rule.get('enabled', True)
                    })
                    
                    # Compile pattern
                    pattern = rule.get('pattern', '')
                    if pattern and rule.get('enabled', True):
                        try:
                            self.compiled_patterns[rule['name']] = re.compile(pattern)
                        except re.error as e:
                            logger.error(f"Invalid regex pattern in rule '{rule['name']}': {e}")
                
                # Process column rules
                for rule in rules_config.get('column_rules', []):
                    column_name = rule.get('column_name', '').lower()
                    if not column_name:
                        continue
                    
                    if column_name not in self.column_rules:
                        self.column_rules[column_name] = []
                    
                    self.column_rules[column_name].append({
                        'name': rule.get('name', f'Column Rule: {column_name}'),
                        'type': rule.get('type', 'hash'),
                        'description': rule.get('description', ''),
                        'enabled': rule.get('enabled', True)
                    })
            
            logger.info(f"Loaded {len(self.global_rules)} global rules and {len(self.column_rules)} column rules")
                
        except Exception as e:
            logger.error(f"Error loading masking rules: {e}", exc_info=True)
            # Initialize with empty rules
            self.global_rules = []
            self.column_rules = {}
            self.compiled_patterns = {}
    
    def mask_query_results(
        self, 
        results: Dict[str, Any], 
        user: Optional[User] = None,
        role_permissions: Optional[Dict[str, List[str]]] = None
    ) -> Dict[str, Any]:
        """
        Apply masking to query results
        
        Args:
            results: Query results with 'columns' and 'data' fields
            user: Current user (for role-based masking)
            role_permissions: Mapping of roles to permitted unmasked columns
            
        Returns:
            Masked query results
        """
        if not self.enabled:
            return results
        
        if not results or 'columns' not in results or 'data' not in results:
            return results
        
        try:
            columns = results['columns']
            data = results['data']
            
            # Make a copy to avoid modifying the original
            masked_data = [list(row) for row in data]
            
            # Check which columns should be masked for this user
            columns_to_mask = self._get_columns_to_mask(columns, user, role_permissions)
            
            # Apply column-specific masking
            for row_idx, row in enumerate(masked_data):
                for col_idx, value in enumerate(row):
                    if value is None:
                        continue
                    
                    column_name = columns[col_idx].lower()
                    
                    # Apply column-specific rules if column should be masked
                    if column_name in columns_to_mask:
                        masked_value = self._apply_column_masking(value, column_name)
                        masked_data[row_idx][col_idx] = masked_value
                    
                    # Always apply global pattern-based rules for sensitive data detection
                    if isinstance(value, str):
                        masked_value = self._apply_global_masking(value)
                        masked_data[row_idx][col_idx] = masked_value
            
            # Return masked results
            return {
                'columns': results['columns'],
                'data': masked_data,
                'metadata': results.get('metadata', {})
            }
            
        except Exception as e:
            logger.error(f"Error masking query results: {e}", exc_info=True)
            # Return original results on error
            return results
    
    def _get_columns_to_mask(
        self, 
        columns: List[str], 
        user: Optional[User] = None,
        role_permissions: Optional[Dict[str, List[str]]] = None
    ) -> Set[str]:
        """
        Determine which columns should be masked for the current user
        
        Args:
            columns: List of column names
            user: Current user
            role_permissions: Mapping of roles to permitted unmasked columns
            
        Returns:
            Set of column names (lowercase) that should be masked
        """
        # If no user or no role permissions, mask all sensitive columns
        if not user or not role_permissions:
            return set(rule.lower() for rule in self.column_rules.keys())
        
        columns_to_mask = set()
        
        # Get user roles
        user_roles = [role.name for role in user.roles] if user.roles else []
        
        # If user is superuser, don't mask anything
        if user.is_superuser:
            return set()
        
        # For each column in column_rules, check if user has permission to see unmasked
        for column_name in self.column_rules.keys():
            column_name_lower = column_name.lower()
            
            # Check if any of the user's roles has permission for this column
            has_permission = False
            for role in user_roles:
                if role in role_permissions and column_name_lower in (col.lower() for col in role_permissions.get(role, [])):
                    has_permission = True
                    break
            
            if not has_permission:
                columns_to_mask.add(column_name_lower)
        
        return columns_to_mask
    
    def _apply_column_masking(self, value: Any, column_name: str) -> Any:
        """
        Apply column-specific masking rules
        
        Args:
            value: Value to mask
            column_name: Column name (lowercase)
            
        Returns:
            Masked value
        """
        # Skip if no rules for this column
        if column_name not in self.column_rules:
            return value
        
        # Apply each enabled rule
        masked_value = value
        for rule in self.column_rules[column_name]:
            if not rule.get('enabled', True):
                continue
            
            mask_type = rule.get('type', 'hash')
            
            if isinstance(masked_value, str):
                if mask_type == 'hash':
                    masked_value = self._hash_value(masked_value)
                elif mask_type == 'redact':
                    masked_value = '[REDACTED]'
                elif mask_type == 'partial':
                    masked_value = self._mask_partial(masked_value)
                elif mask_type == 'tokenize':
                    masked_value = self._tokenize_value(masked_value)
            
        return masked_value
    
    def _apply_global_masking(self, value: str) -> str:
        """
        Apply global pattern-based masking rules
        
        Args:
            value: String value to check and mask
            
        Returns:
            Masked value if matches any patterns, otherwise original value
        """
        # Skip non-string values
        if not isinstance(value, str):
            return value
        
        masked_value = value
        
        # Apply PII matchers
        for pii_type, matcher in self.pii_matchers.items():
            pattern = matcher["pattern"]
            mask_function = matcher["mask_function"]
            
            masked_value = pattern.sub(
                lambda match: mask_function(match, pii_type), 
                masked_value
            )
        
        # Apply custom global rules
        for rule_name, pattern in self.compiled_patterns.items():
            masked_value = pattern.sub(lambda match: f"[REDACTED {rule_name}]", masked_value)
        
        return masked_value
    
    def _hash_value(self, value: str) -> str:
        """
        Hash a value for masking
        
        Args:
            value: Value to hash
            
        Returns:
            Hashed value
        """
        return hashlib.sha256(value.encode()).hexdigest()[:10] + "..."
    
    def _mask_partial(self, value: str) -> str:
        """
        Partially mask a value (e.g., show first/last characters)
        
        Args:
            value: Value to mask
            
        Returns:
            Partially masked value
        """
        if len(value) <= 4:
            return "*" * len(value)
        
        return value[:2] + "*" * (len(value) - 4) + value[-2:]
    
    def _tokenize_value(self, value: str) -> str:
        """
        Tokenize a value (consistent replacement)
        
        Args:
            value: Value to tokenize
            
        Returns:
            Tokenized value
        """
        # Use a hash but with a fixed prefix for readability
        token_hash = hashlib.md5(value.encode()).hexdigest()[:8]
        return f"TOKEN_{token_hash}"
    
    def _mask_credit_card(self, cc_number: str) -> str:
        """
        Mask a credit card number
        
        Args:
            cc_number: Credit card number
            
        Returns:
            Masked credit card number
        """
        # Remove any spaces or dashes
        cc_clean = cc_number.replace(" ", "").replace("-", "")
        
        # Check if it's a valid length
        if len(cc_clean) < 13 or len(cc_clean) > 19:
            return "[INVALID CARD]"
        
        # Mask middle digits, keep first 6 and last 4
        first_six = cc_clean[:6]
        last_four = cc_clean[-4:]
        masked = first_six + "*" * (len(cc_clean) - 10) + last_four
        
        # Format for readability
        formatted = ""
        for i in range(0, len(masked), 4):
            formatted += masked[i:i+4] + " "
        
        return formatted.strip()
    
    def _mask_email(self, email: str) -> str:
        """
        Mask an email address
        
        Args:
            email: Email address
            
        Returns:
            Masked email address
        """
        parts = email.split("@")
        if len(parts) != 2:
            return "[INVALID EMAIL]"
        
        username, domain = parts
        if len(username) <= 2:
            masked_username = "*" * len(username)
        else:
            masked_username = username[0] + "*" * (len(username) - 2) + username[-1]
        
        domain_parts = domain.split(".")
        if len(domain_parts) < 2:
            return "[INVALID EMAIL]"
        
        domain_name = ".".join(domain_parts[:-1])
        tld = domain_parts[-1]
        
        masked_domain = domain_name[0] + "*" * (len(domain_name) - 1) + "." + tld
        
        return f"{masked_username}@{masked_domain}"
    
    def _mask_phone(self, phone: str) -> str:
        """
        Mask a phone number
        
        Args:
            phone: Phone number
            
        Returns:
            Masked phone number
        """
        # Remove all non-digit characters
        digits = re.sub(r'\D', '', phone)
        
        # Check if we have enough digits
        if len(digits) < 7:
            return "[INVALID PHONE]"
        
        # Keep country code if present (assuming anything before the last 10 digits)
        if len(digits) > 10:
            country_code = digits[:-10]
            main_number = digits[-10:]
            
            formatted = country_code + "-"
        else:
            main_number = digits
            formatted = ""
        
        # Format the last part as XXX-XXX-1234 (last 4 visible)
        formatted += "XXX-XXX-" + main_number[-4:]
        
        return formatted
    
    def _mask_name(self, name: str) -> str:
        """
        Mask a person's name
        
        Args:
            name: Person's name
            
        Returns:
            Masked name
        """
        parts = name.split()
        if len(parts) < 2:
            return "[REDACTED NAME]"
        
        # Mask all but first initial of first and last name
        masked_parts = []
        for part in parts:
            if len(part) > 0:
                masked_parts.append(part[0] + "." * (len(part) - 1))
            else:
                masked_parts.append("")
        
        return " ".join(masked_parts)
    
    async def get_masking_rules(self, db: Session) -> Dict[str, Any]:
        """
        Get all masking rules
        
        Args:
            db: Database session
            
        Returns:
            Dictionary of masking rules
        """
        try:
            # Query database rules
            db_rules = db.query(MaskingRule).all()
            
            # Convert to dictionary
            rules = {
                "global_rules": [],
                "column_rules": []
            }
            
            for rule in db_rules:
                rule_dict = {
                    "id": rule.id,
                    "name": rule.name,
                    "description": rule.description,
                    "enabled": rule.enabled,
                    "created_at": rule.created_at.isoformat() if rule.created_at else None,
                    "updated_at": rule.updated_at.isoformat() if rule.updated_at else None
                }
                
                if rule.rule_type == MaskingType.GLOBAL:
                    rule_dict["pattern"] = rule.pattern
                    rule_dict["type"] = rule.masking_method
                    rules["global_rules"].append(rule_dict)
                    
                elif rule.rule_type == MaskingType.COLUMN:
                    rule_dict["column_name"] = rule.column_name
                    rule_dict["type"] = rule.masking_method
                    rules["column_rules"].append(rule_dict)
            
            return rules
            
        except Exception as e:
            logger.error(f"Error getting masking rules: {e}", exc_info=True)
            raise
    
    async def create_masking_rule(
        self, 
        db: Session,
        name: str,
        rule_type: MaskingType,
        description: str,
        masking_method: str,
        pattern: Optional[str] = None,
        column_name: Optional[str] = None
    ) -> MaskingRule:
        """
        Create a new masking rule
        
        Args:
            db: Database session
            name: Rule name
            rule_type: Rule type (GLOBAL or COLUMN)
            description: Rule description
            masking_method: Masking method
            pattern: Regex pattern (for GLOBAL rules)
            column_name: Column name (for COLUMN rules)
            
        Returns:
            Created masking rule
        """
        try:
            # Validate rule
            if rule_type == MaskingType.GLOBAL and not pattern:
                raise ValueError("Pattern is required for global rules")
            
            if rule_type == MaskingType.COLUMN and not column_name:
                raise ValueError("Column name is required for column rules")
            
            # Create rule
            rule = MaskingRule(
                name=name,
                rule_type=rule_type,
                description=description,
                masking_method=masking_method,
                pattern=pattern,
                column_name=column_name,
                enabled=True,
                created_at=datetime.utcnow()
            )
            
            db.add(rule)
            db.commit()
            db.refresh(rule)
            
            # Reload masking rules
            self._load_masking_rules()
            
            return rule
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating masking rule: {e}", exc_info=True)
            raise
    
    async def update_masking_rule(
        self,
        db: Session,
        rule_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        masking_method: Optional[str] = None,
        pattern: Optional[str] = None,
        column_name: Optional[str] = None,
        enabled: Optional[bool] = None
    ) -> Optional[MaskingRule]:
        """
        Update an existing masking rule
        
        Args:
            db: Database session
            rule_id: Rule ID
            name: Rule name
            description: Rule description
            masking_method: Masking method
            pattern: Regex pattern (for GLOBAL rules)
            column_name: Column name (for COLUMN rules)
            enabled: Whether the rule is enabled
            
        Returns:
            Updated masking rule, or None if not found
        """
        try:
            # Get rule
            rule = db.query(MaskingRule).filter(MaskingRule.id == rule_id).first()
            if not rule:
                return None
            
            # Update fields if provided
            if name is not None:
                rule.name = name
            
            if description is not None:
                rule.description = description
            
            if masking_method is not None:
                rule.masking_method = masking_method
            
            if pattern is not None and rule.rule_type == MaskingType.GLOBAL:
                rule.pattern = pattern
            
            if column_name is not None and rule.rule_type == MaskingType.COLUMN:
                rule.column_name = column_name
            
            if enabled is not None:
                rule.enabled = enabled
            
            rule.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(rule)
            
            # Reload masking rules
            self._load_masking_rules()
            
            return rule
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating masking rule: {e}", exc_info=True)
            raise
    
    async def delete_masking_rule(self, db: Session, rule_id: int) -> bool:
        """
        Delete a masking rule
        
        Args:
            db: Database session
            rule_id: Rule ID
            
        Returns:
            True if deleted, False if not found
        """
        try:
            # Get rule
            rule = db.query(MaskingRule).filter(MaskingRule.id == rule_id).first()
            if not rule:
                return False
            
            # Delete rule
            db.delete(rule)
            db.commit()
            
            # Reload masking rules
            self._load_masking_rules()
            
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting masking rule: {e}", exc_info=True)
            raise
    
    async def test_masking_rule(
        self,
        rule_type: MaskingType,
        masking_method: str,
        pattern: Optional[str] = None,
        column_name: Optional[str] = None,
        test_data: List[str] = None
    ) -> Dict[str, Any]:
        """
        Test a masking rule against sample data
        
        Args:
            rule_type: Rule type (GLOBAL or COLUMN)
            masking_method: Masking method
            pattern: Regex pattern (for GLOBAL rules)
            column_name: Column name (for COLUMN rules)
            test_data: Sample data to test against
            
        Returns:
            Dictionary with test results
        """
        try:
            if not test_data:
                test_data = [
                    "John Doe",
                    "jane.doe@example.com",
                    "123-45-6789",
                    "4111 1111 1111 1111",
                    "123 Main St, Anytown, USA",
                    "192.168.1.1",
                    "2023-01-01",
                    "AB123456",
                    "987654321"
                ]
            
            results = []
            
            for item in test_data:
                # Skip non-string values
                if not isinstance(item, str):
                    continue
                
                # Apply masking based on rule type
                if rule_type == MaskingType.GLOBAL and pattern:
                    try:
                        compiled_pattern = re.compile(pattern)
                        masked = compiled_pattern.sub(f"[REDACTED]", item)
                        match_found = masked != item
                    except re.error as e:
                        results.append({
                            "original": item,
                            "masked": f"ERROR: Invalid pattern: {str(e)}",
                            "matched": False
                        })
                        continue
                        
                elif rule_type == MaskingType.COLUMN:
                    if masking_method == "hash":
                        masked = self._hash_value(item)
                    elif masking_method == "redact":
                        masked = "[REDACTED]"
                    elif masking_method == "partial":
                        masked = self._mask_partial(item)
                    elif masking_method == "tokenize":
                        masked = self._tokenize_value(item)
                    else:
                        masked = "[UNKNOWN MASKING METHOD]"
                    
                    match_found = True
                else:
                    masked = item
                    match_found = False
                
                results.append({
                    "original": item,
                    "masked": masked,
                    "matched": match_found
                })
            
            return {
                "rule_type": rule_type,
                "masking_method": masking_method,
                "pattern": pattern,
                "column_name": column_name,
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Error testing masking rule: {e}", exc_info=True)
            raise

# Initialize masking service
data_masking_service = DataMaskingService()

# Son güncelleme: 2025-05-20 14:44:45
# Güncelleyen: Teeksss