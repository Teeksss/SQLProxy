"""
Data Masking and Sensitive Data Protection for SQL Proxy

This module provides data masking and protection capabilities for
sensitive data flowing through SQL Proxy.

Last updated: 2025-05-20 11:04:28
Updated by: Teeksss
"""

import re
import logging
import hashlib
import uuid
import json
from typing import Dict, List, Any, Optional, Union, Tuple, Set
from enum import Enum
import threading

from app.core.config import settings

logger = logging.getLogger(__name__)

class MaskingType(str, Enum):
    """Types of data masking"""
    FULL = "full"                 # Replace entire value with mask
    PARTIAL = "partial"           # Replace part of value with mask
    HASH = "hash"                 # Replace with cryptographic hash
    TOKENIZE = "tokenize"         # Replace with token
    REDACT = "redact"             # Remove entirely
    PSEUDONYMIZE = "pseudonymize" # Replace with consistent pseudonym
    GENERALIZE = "generalize"     # Replace with more general value
    FORMAT_PRESERVING = "format_preserving"  # Preserve format but change value
    NULLIFY = "nullify"           # Replace with NULL
    CUSTOM = "custom"             # Use custom function

class DataCategory(str, Enum):
    """Categories of sensitive data"""
    PII = "pii"                   # Personally Identifiable Information
    PHI = "phi"                   # Protected Health Information
    PCI = "pci"                   # Payment Card Industry Data
    CREDENTIALS = "credentials"   # Credentials (passwords, API keys)
    FINANCIAL = "financial"       # Financial data
    LOCATION = "location"         # Location data
    CONFIDENTIAL = "confidential" # General confidential data
    CUSTOM = "custom"             # Custom category

class MaskingRule:
    """Rule defining how to mask specific data"""
    
    def __init__(
        self,
        table_name: str,
        column_name: str,
        masking_type: MaskingType,
        data_category: DataCategory,
        pattern: Optional[str] = None,
        replacement: Optional[str] = None,
        condition: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
        description: Optional[str] = None,
        priority: int = 0
    ):
        """
        Initialize masking rule
        
        Args:
            table_name: Database table name (can be regex pattern)
            column_name: Column name to mask (can be regex pattern)
            masking_type: Type of masking to apply
            data_category: Category of sensitive data
            pattern: Regex pattern to identify sensitive data
            replacement: Replacement text for masked data
            condition: SQL-like condition for when to apply rule
            options: Additional options for masking
            description: Human-readable description of rule
            priority: Rule priority (higher numbers take precedence)
        """
        self.table_name = table_name
        self.column_name = column_name
        self.masking_type = masking_type
        self.data_category = data_category
        self.pattern = pattern
        self.replacement = replacement
        self.condition = condition
        self.options = options or {}
        self.description = description
        self.priority = priority
        
        # Compile regex patterns for performance
        self._table_regex = re.compile(table_name, re.IGNORECASE) if table_name else None
        self._column_regex = re.compile(column_name, re.IGNORECASE) if column_name else None
        self._pattern_regex = re.compile(pattern, re.IGNORECASE) if pattern else None
    
    def matches_table_column(self, table: str, column: str) -> bool:
        """
        Check if rule matches table and column
        
        Args:
            table: Table name
            column: Column name
            
        Returns:
            True if rule matches
        """
        table_match = self._table_regex.search(table) if self._table_regex else True
        column_match = self._column_regex.search(column) if self._column_regex else True
        
        return bool(table_match and column_match)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert rule to dictionary
        
        Returns:
            Dictionary representation
        """
        return {
            "table_name": self.table_name,
            "column_name": self.column_name,
            "masking_type": self.masking_type,
            "data_category": self.data_category,
            "pattern": self.pattern,
            "replacement": self.replacement,
            "condition": self.condition,
            "options": self.options,
            "description": self.description,
            "priority": self.priority
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'MaskingRule':
        """
        Create rule from dictionary
        
        Args:
            data: Dictionary data
            
        Returns:
            MaskingRule instance
        """
        return MaskingRule(
            table_name=data.get("table_name", ""),
            column_name=data.get("column_name", ""),
            masking_type=data.get("masking_type", MaskingType.FULL),
            data_category=data.get("data_category", DataCategory.PII),
            pattern=data.get("pattern"),
            replacement=data.get("replacement"),
            condition=data.get("condition"),
            options=data.get("options", {}),
            description=data.get("description"),
            priority=data.get("priority", 0)
        )

class DataMaskingService:
    """
    Data masking service
    
    Manages and applies data masking rules to protect sensitive data
    """
    
    def __init__(self):
        """Initialize data masking service"""
        self.rules = []
        self.tokenization_map = {}
        self.pseudonym_map = {}
        self.custom_maskers = {}
        self.lock = threading.RLock()
        
        # Regular expressions for detecting common sensitive data
        self.data_detectors = {
            "credit_card": re.compile(r'\b(?:\d{4}[-\s]?){3}\d{4}\b'),
            "email": re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            "phone": re.compile(r'\b(\+\d{1,2}\s?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'),
            "ssn": re.compile(r'\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b'),
            "ip_address": re.compile(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'),
            "date_of_birth": re.compile(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b')
        }
        
        # Load rules from configuration
        self._load_rules_from_config()
        
        # Register custom maskers
        self._register_custom_maskers()
        
        logger.info(f"Data masking service initialized with {len(self.rules)} rules")
    
    def _load_rules_from_config(self):
        """Load masking rules from configuration"""
        rules_config = settings.DATA_MASKING_RULES
        
        if not rules_config:
            return
        
        try:
            # Load rules from file or embedded config
            if isinstance(rules_config, str) and rules_config.endswith(('.json', '.yaml', '.yml')):
                self._load_rules_from_file(rules_config)
            elif isinstance(rules_config, list):
                for rule_data in rules_config:
                    rule = MaskingRule.from_dict(rule_data)
                    self.rules.append(rule)
        except Exception as e:
            logger.error(f"Error loading masking rules: {str(e)}")
    
    def _load_rules_from_file(self, file_path: str):
        """
        Load masking rules from file
        
        Args:
            file_path: Path to rules file
        """
        try:
            with open(file_path, 'r') as f:
                if file_path.endswith('.json'):
                    rules_data = json.load(f)
                elif file_path.endswith(('.yaml', '.yml')):
                    import yaml
                    rules_data = yaml.safe_load(f)
                else:
                    raise ValueError(f"Unsupported file format: {file_path}")
            
            for rule_data in rules_data:
                rule = MaskingRule.from_dict(rule_data)
                self.rules.append(rule)
                
        except Exception as e:
            logger.error(f"Error loading masking rules from file {file_path}: {str(e)}")
    
    def _register_custom_maskers(self):
        """Register custom masking functions"""
        # Register standard maskers
        self.custom_maskers.update({
            "credit_card_masker": self._mask_credit_card,
            "email_masker": self._mask_email,
            "phone_masker": self._mask_phone,
            "address_masker": self._mask_address,
            "name_masker": self._mask_name,
            "ip_masker": self._mask_ip
        })
        
        # Register custom maskers from configuration
        custom_maskers = settings.CUSTOM_DATA_MASKERS
        if custom_maskers:
            for name, module_path in custom_maskers.items():
                try:
                    module_parts = module_path.split(".")
                    function_name = module_parts[-1]
                    module_path = ".".join(module_parts[:-1])
                    
                    module = __import__(module_path, fromlist=[function_name])
                    function = getattr(module, function_name)
                    
                    self.custom_maskers[name] = function
                    logger.info(f"Registered custom masker: {name}")
                except Exception as e:
                    logger.error(f"Error registering custom masker {name}: {str(e)}")
    
    def add_rule(self, rule: MaskingRule) -> None:
        """
        Add a new masking rule
        
        Args:
            rule: Masking rule to add
        """
        with self.lock:
            self.rules.append(rule)
            
            # Sort rules by priority
            self.rules.sort(key=lambda r: r.priority, reverse=True)
    
    def remove_rule(self, table_name: str, column_name: str) -> bool:
        """
        Remove a masking rule
        
        Args:
            table_name: Table name pattern
            column_name: Column name pattern
            
        Returns:
            True if rule was removed
        """
        with self.lock:
            for i, rule in enumerate(self.rules):
                if rule.table_name == table_name and rule.column_name == column_name:
                    self.rules.pop(i)
                    return True
            
            return False
    
    def get_rules(self) -> List[Dict[str, Any]]:
        """
        Get all masking rules
        
        Returns:
            List of rule dictionaries
        """
        with self.lock:
            return [rule.to_dict() for rule in self.rules]
    
    def mask_query_results(
        self, 
        results: Dict[str, Any],
        table_mapping: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """
        Apply masking to query results
        
        Args:
            results: Query results to mask
            table_mapping: Mapping of column names to table names
            
        Returns:
            Masked query results
        """
        if not results or "columns" not in results or "data" not in results:
            return results
        
        columns = results["columns"]
        data = results["data"]
        
        # Optimization for empty results
        if not columns or not data:
            return results
        
        # Determine which columns need masking
        masking_rules_by_column = {}
        
        for col_idx, column in enumerate(columns):
            if not table_mapping:
                # Without table mapping, use column name only matching
                applicable_rules = [
                    rule for rule in self.rules 
                    if rule.matches_table_column("", column)
                ]
            else:
                # With table mapping, use table and column matching
                table = table_mapping.get(column, "")
                applicable_rules = [
                    rule for rule in self.rules
                    if rule.matches_table_column(table, column)
                ]
            
            if applicable_rules:
                # Sort by priority and take the highest
                applicable_rules.sort(key=lambda r: r.priority, reverse=True)
                masking_rules_by_column[col_idx] = applicable_rules[0]
        
        # If no columns need masking, return original results
        if not masking_rules_by_column:
            return results
        
        # Apply masking to data
        masked_data = []
        
        for row in data:
            masked_row = list(row)
            
            for col_idx, rule in masking_rules_by_column.items():
                if col_idx < len(masked_row):
                    # Apply masking to this cell
                    original_value = masked_row[col_idx]
                    masked_value = self._apply_masking_rule(original_value, rule)
                    masked_row[col_idx] = masked_value
            
            masked_data.append(masked_row)
        
        # Create masked results
        masked_results = results.copy()
        masked_results["data"] = masked_data
        
        return masked_results
    
    def detect_sensitive_data(self, text: str) -> List[Dict[str, Any]]:
        """
        Detect sensitive data in a string using predefined patterns
        
        Args:
            text: Text to analyze
            
        Returns:
            List of detected sensitive data items with type and value
        """
        if not text or not isinstance(text, str):
            return []
        
        results = []
        
        # Check for each type of sensitive data
        for data_type, pattern in self.data_detectors.items():
            matches = pattern.finditer(text)
            
            for match in matches:
                results.append({
                    "type": data_type,
                    "value": match.group(0),
                    "start": match.start(),
                    "end": match.end()
                })
        
        return results
    
    def mask_sensitive_data(self, text: str) -> str:
        """
        Mask sensitive data in a string using predefined patterns
        
        Args:
            text: Text to mask
            
        Returns:
            Text with sensitive data masked
        """
        if not text or not isinstance(text, str):
            return text
        
        # Detect sensitive data
        sensitive_data = self.detect_sensitive_data(text)
        
        # Sort by position (in reverse to avoid shifting indices)
        sensitive_data.sort(key=lambda x: x["start"], reverse=True)
        
        # Apply masking
        for item in sensitive_data:
            data_type = item["type"]
            value = item["value"]
            start = item["start"]
            end = item["end"]
            
            # Apply appropriate masking based on data type
            if data_type == "credit_card":
                masked_value = self._mask_credit_card(value)
            elif data_type == "email":
                masked_value = self._mask_email(value)
            elif data_type == "phone":
                masked_value = self._mask_phone(value)
            elif data_type == "ssn":
                masked_value = "XXX-XX-XXXX"
            elif data_type == "ip_address":
                masked_value = "XXX.XXX.XXX.XXX"
            elif data_type == "date_of_birth":
                masked_value = "XX/XX/XXXX"
            else:
                masked_value = "XXXXXXXX"
            
            # Replace in text
            text = text[:start] + masked_value + text[end:]
        
        return text
    
    def _apply_masking_rule(self, value: Any, rule: MaskingRule) -> Any:
        """
        Apply masking rule to a value
        
        Args:
            value: Original value
            rule: Masking rule to apply
            
        Returns:
            Masked value
        """
        # Handle NULL/None values
        if value is None:
            return None
        
        # Convert to string for processing (except for nullify which keeps original type)
        if rule.masking_type != MaskingType.NULLIFY:
            value = str(value)
        
        # Apply masking based on type
        if rule.masking_type == MaskingType.FULL:
            return self._apply_full_mask(value, rule)
        elif rule.masking_type == MaskingType.PARTIAL:
            return self._apply_partial_mask(value, rule)
        elif rule.masking_type == MaskingType.HASH:
            return self._apply_hash_mask(value, rule)
        elif rule.masking_type == MaskingType.TOKENIZE:
            return self._apply_tokenization(value, rule)
        elif rule.masking_type == MaskingType.REDACT:
            return "[REDACTED]"
        elif rule.masking_type == MaskingType.PSEUDONYMIZE:
            return self._apply_pseudonymization(value, rule)
        elif rule.masking_type == MaskingType.GENERALIZE:
            return self._apply_generalization(value, rule)
        elif rule.masking_type == MaskingType.FORMAT_PRESERVING:
            return self._apply_format_preserving(value, rule)
        elif rule.masking_type == MaskingType.NULLIFY:
            return None
        elif rule.masking_type == MaskingType.CUSTOM:
            return self._apply_custom_mask(value, rule)
        else:
            # Default fallback - full masking
            return self._apply_full_mask(value, rule)
    
    def _apply_full_mask(self, value: str, rule: MaskingRule) -> str:
        """
        Apply full masking to a value
        
        Args:
            value: Original value
            rule: Masking rule
            
        Returns:
            Masked value
        """
        # Use replacement if specified, otherwise use default mask
        if rule.replacement:
            return rule.replacement
        
        # Use options for mask character if specified
        mask_char = rule.options.get("mask_char", "X")
        
        # Replace entire value with mask character
        return mask_char * len(value)
    
    def _apply_partial_mask(self, value: str, rule: MaskingRule) -> str:
        """
        Apply partial masking to a value
        
        Args:
            value: Original value
            rule: Masking rule
            
        Returns:
            Partially masked value
        """
        # Get options
        mask_char = rule.options.get("mask_char", "X")
        start_chars = rule.options.get("start_chars", 0)
        end_chars = rule.options.get("end_chars", 0)
        
        # Apply pattern-based masking if pattern is specified
        if rule.pattern and rule._pattern_regex:
            return rule._pattern_regex.sub(lambda m: mask_char * len(m.group(0)), value)
        
        # Handle case where value is too short for the specified options
        if len(value) <= (start_chars + end_chars):
            return mask_char * len(value)
        
        # Create partially masked value
        masked_value = (
            value[:start_chars] + 
            mask_char * (len(value) - start_chars - end_chars) + 
            (value[-end_chars:] if end_chars > 0 else "")
        )
        
        return masked_value
    
    def _apply_hash_mask(self, value: str, rule: MaskingRule) -> str:
        """
        Apply hash masking to a value
        
        Args:
            value: Original value
            rule: Masking rule
            
        Returns:
            Hashed value
        """
        # Get options
        hash_algo = rule.options.get("hash_algorithm", "sha256")
        salt = rule.options.get("salt", settings.SECRET_KEY)
        prefix = rule.options.get("prefix", "")
        
        # Apply salting if enabled
        salted_value = f"{salt}{value}" if salt else value
        
        # Hash the value
        if hash_algo == "md5":
            hash_obj = hashlib.md5(salted_value.encode())
        elif hash_algo == "sha1":
            hash_obj = hashlib.sha1(salted_value.encode())
        else:  # Default to SHA-256
            hash_obj = hashlib.sha256(salted_value.encode())
        
        hashed_value = hash_obj.hexdigest()
        
        # Add prefix if specified
        if prefix:
            hashed_value = f"{prefix}{hashed_value}"
        
        return hashed_value
    
    def _apply_tokenization(self, value: str, rule: MaskingRule) -> str:
        """
        Apply tokenization to a value
        
        Args:
            value: Original value
            rule: Masking rule
            
        Returns:
            Tokenized value
        """
        with self.lock:
            # Check if value is already tokenized
            for token, original in self.tokenization_map.items():
                if original == value:
                    return token
            
            # Generate a new token
            prefix = rule.options.get("prefix", "TKN_")
            token = f"{prefix}{uuid.uuid4().hex[:8]}"
            
            # Store in tokenization map
            self.tokenization_map[token] = value
            
            return token
    
    def _apply_pseudonymization(self, value: str, rule: MaskingRule) -> str:
        """
        Apply pseudonymization to a value
        
        Args:
            value: Original value
            rule: Masking rule
            
        Returns:
            Pseudonymized value
        """
        category = rule.data_category
        
        with self.lock:
            # Create category map if it doesn't exist
            if category not in self.pseudonym_map:
                self.pseudonym_map[category] = {}
            
            category_map = self.pseudonym_map[category]
            
            # Check if value is already pseudonymized
            if value in category_map:
                return category_map[value]
            
            # Generate a pseudonym based on the data category
            if category == DataCategory.PII:
                # Names
                if rule.column_name.lower() in ('name', 'first_name', 'firstname', 'last_name', 'lastname'):
                    pseudonym = self._generate_pseudonym_name(value, rule)
                # Emails
                elif 'email' in rule.column_name.lower():
                    pseudonym = self._generate_pseudonym_email(value, rule)
                # Phone
                elif 'phone' in rule.column_name.lower() or 'tel' in rule.column_name.lower():
                    pseudonym = self._generate_pseudonym_phone(value, rule)
                # Default
                else:
                    pseudonym = f"Person_{len(category_map) + 1}"
            
            elif category == DataCategory.PHI:
                # Patient ID
                if 'id' in rule.column_name.lower() or 'patient' in rule.column_name.lower():
                    pseudonym = f"Patient_{len(category_map) + 1}"
                # Default
                else:
                    pseudonym = f"Medical_{len(category_map) + 1}"
            
            elif category == DataCategory.PCI:
                # Credit card
                if 'card' in rule.column_name.lower() or 'cc' in rule.column_name.lower():
                    pseudonym = self._generate_pseudonym_credit_card(value, rule)
                # Default
                else:
                    pseudonym = f"Card_{len(category_map) + 1}"
            
            elif category == DataCategory.LOCATION:
                pseudonym = f"Location_{len(category_map) + 1}"
            
            else:
                # Default pseudonym
                pseudonym = f"Pseudonym_{len(category_map) + 1}"
            
            # Store in pseudonym map
            category_map[value] = pseudonym
            
            return pseudonym
    
    def _generate_pseudonym_name(self, value: str, rule: MaskingRule) -> str:
        """Generate a pseudonym for a name"""
        common_names = [
            "John Smith", "Jane Doe", "Alex Johnson", "Sam Williams", 
            "Taylor Brown", "Jordan Davis", "Casey Miller", "Pat Wilson",
            "Terry Moore", "Jamie Anderson", "Chris Taylor", "Jesse Thomas"
        ]
        
        # Select a name based on the hash of the original value (for consistency)
        hash_value = hash(value) % len(common_names)
        return common_names[hash_value]
    
    def _generate_pseudonym_email(self, value: str, rule: MaskingRule) -> str:
        """Generate a pseudonym for an email"""
        common_domains = ["example.com", "example.org", "example.net", "mail.test"]
        
        # Select a domain based on the hash of the original value
        hash_value = hash(value)
        domain_idx = hash_value % len(common_domains)
        
        # Create a username
        username = f"user{abs(hash_value) % 10000}"
        
        return f"{username}@{common_domains[domain_idx]}"
    
    def _generate_pseudonym_phone(self, value: str, rule: MaskingRule) -> str:
        """Generate a pseudonym for a phone number"""
        # Create a phone number with area code 555 (reserved for fictional use)
        hash_value = abs(hash(value)) % 10000
        return f"(555) 555-{hash_value:04d}"
    
    def _generate_pseudonym_credit_card(self, value: str, rule: MaskingRule) -> str:
        """Generate a pseudonym for a credit card"""
        # Create a fictional credit card with prefix 9999
        hash_value = abs(hash(value)) % 1000000
        return f"9999-9999-9999-{hash_value:04d}"
    
    def _apply_generalization(self, value: str, rule: MaskingRule) -> str:
        """
        Apply generalization to a value
        
        Args:
            value: Original value
            rule: Masking rule
            
        Returns:
            Generalized value
        """
        category = rule.data_category
        
        # Apply generalization based on data category and options
        if category == DataCategory.PII:
            # Age
            if rule.column_name.lower() in ('age', 'years'):
                try:
                    age = int(value)
                    bin_size = rule.options.get("bin_size", 10)
                    lower_bound = (age // bin_size) * bin_size
                    upper_bound = lower_bound + bin_size - 1
                    return f"{lower_bound}-{upper_bound}"
                except (ValueError, TypeError):
                    return "UNKNOWN"
            
            # Date of birth
            elif 'birth' in rule.column_name.lower() or 'dob' in rule.column_name.lower():
                return self._generalize_date(value, rule)
            
            # Default
            else:
                return "GENERALIZED"
        
        elif category == DataCategory.LOCATION:
            # ZIP code
            if 'zip' in rule.column_name.lower() or 'postal' in rule.column_name.lower():
                # Keep only first 3 digits
                if len(value) >= 5:
                    digits_to_keep = rule.options.get("digits_to_keep", 3)
                    return value[:digits_to_keep] + "XX"
                else:
                    return "XXXXX"
            
            # Address
            elif 'address' in rule.column_name.lower() or 'street' in rule.column_name.lower():
                return "ADDRESS"
            
            # City
            elif 'city' in rule.column_name.lower():
                return "CITY"
            
            # State/Province
            elif 'state' in rule.column_name.lower() or 'province' in rule.column_name.lower():
                return "STATE"
            
            # Country
            elif 'country' in rule.column_name.lower():
                return "COUNTRY"
            
            # Default
            else:
                return "LOCATION"
        
        elif category == DataCategory.FINANCIAL:
            # Income
            if 'income' in rule.column_name.lower() or 'salary' in rule.column_name.lower():
                try:
                    income = float(value.replace(',', '').replace('$', ''))
                    bin_size = rule.options.get("bin_size", 10000)
                    lower_bound = (income // bin_size) * bin_size
                    upper_bound = lower_bound + bin_size - 1
                    return f"${lower_bound:,.0f}-${upper_bound:,.0f}"
                except (ValueError, TypeError):
                    return "UNKNOWN"
            
            # Default
            else:
                return "FINANCIAL_DATA"
        
        else:
            # Default generalization
            return "GENERALIZED_DATA"
    
    def _generalize_date(self, value: str, rule: MaskingRule) -> str:
        """Generalize a date value"""
        import datetime
        
        try:
            # Try different date formats
            for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%d-%m-%Y", "%m-%d-%Y"]:
                try:
                    date = datetime.datetime.strptime(value, fmt).date()
                    break
                except ValueError:
                    continue
            else:
                # No format matched
                return "DATE"
            
            # Generalize based on options
            generalize_level = rule.options.get("generalize_level", "month")
            
            if generalize_level == "year":
                return str(date.year)
            elif generalize_level == "month":
                return f"{date.year}-{date.month:02d}"
            elif generalize_level == "quarter":
                quarter = (date.month - 1) // 3 + 1
                return f"{date.year}-Q{quarter}"
            elif generalize_level == "decade":
                decade = (date.year // 10) * 10
                return f"{decade}s"
            else:
                # Default to year
                return str(date.year)
                
        except Exception:
            return "DATE"
    
    def _apply_format_preserving(self, value: str, rule: MaskingRule) -> str:
        """
        Apply format-preserving masking to a value
        
        Args:
            value: Original value
            rule: Masking rule
            
        Returns:
            Masked value with preserved format
        """
        # Get options
        preserve_regex = rule.options.get("preserve_regex", r"[^a-zA-Z0-9]")
        mask_char = rule.options.get("mask_char", "X")
        
        # Compile regex if needed
        if isinstance(preserve_regex, str):
            preserve_pattern = re.compile(preserve_regex)
        else:
            preserve_pattern = preserve_regex
        
        # Create format-preserving mask
        char_classes = []
        
        for char in value:
            if preserve_pattern.match(char):
                # Keep special characters
                char_classes.append(char)
            elif char.isdigit():
                # Replace digits with a random digit
                char_classes.append(str(hash(char + value) % 10))
            elif char.isupper():
                # Replace uppercase with uppercase mask character
                char_classes.append(mask_char.upper())
            elif char.islower():
                # Replace lowercase with lowercase mask character
                char_classes.append(mask_char.lower())
            else:
                # Replace with mask character
                char_classes.append(mask_char)
        
        return "".join(char_classes)
    
    def _apply_custom_mask(self, value: str, rule: MaskingRule) -> str:
        """
        Apply custom masking function to a value
        
        Args:
            value: Original value
            rule: Masking rule
            
        Returns:
            Masked value
        """
        # Get custom function from options
        custom_function = rule.options.get("function")
        
        if not custom_function:
            logger.warning(f"Custom masking rule without function specified: {rule.to_dict()}")
            return "[MASKED]"
        
        # Look up custom function
        if custom_function in self.custom_maskers:
            try:
                return self.custom_maskers[custom_function](value, rule.options)
            except Exception as e:
                logger.error(f"Error applying custom masker {custom_function}: {str(e)}")
                return "[ERROR]"
        else:
            logger.warning(f"Custom masking function not found: {custom_function}")
            return "[UNKNOWN_MASKER]"
    
    def _mask_credit_card(self, value: str, options: Dict[str, Any] = None) -> str:
        """Mask a credit card number"""
        options = options or {}
        
        # Default: keep first 6 and last 4 digits
        visible_first = options.get("visible_first", 6)
        visible_last = options.get("visible_last", 4)
        mask_char = options.get("mask_char", "X")
        
        # Remove non-digit characters
        digits = re.sub(r"\D", "", value)
        
        # Check if length is sufficient
        if len(digits) <= (visible_first + visible_last):
            return mask_char * len(digits)
        
        # Mask middle digits
        masked = (
            digits[:visible_first] + 
            mask_char * (len(digits) - visible_first - visible_last) + 
            digits[-visible_last:]
        )
        
        # Format the result to match the input format
        if re.match(r"^\d{4}-\d{4}-\d{4}-\d{4}$", value):
            # Format as XXXX-XXXX-XXXX-XXXX
            return f"{masked[:4]}-{masked[4:8]}-{masked[8:12]}-{masked[12:]}"
        elif re.match(r"^\d{4}\s\d{4}\s\d{4}\s\d{4}$", value):
            # Format as XXXX XXXX XXXX XXXX
            return f"{masked[:4]} {masked[4:8]} {masked[8:12]} {masked[12:]}"
        else:
            # Return as is
            return masked
    
    def _mask_email(self, value: str, options: Dict[str, Any] = None) -> str:
        """Mask an email address"""
        options = options or {}
        
        # Default: mask username portion but keep domain
        mask_username = options.get("mask_username", True)
        mask_domain = options.get("mask_domain", False)
        mask_char = options.get("mask_char", "x")
        
        # Check if valid email format
        email_parts = value.split("@")
        if len(email_parts) != 2:
            return mask_char * len(value)
        
        username, domain = email_parts
        
        # Mask username if needed
        if mask_username:
            if len(username) <= 2:
                masked_username = mask_char * len(username)
            else:
                masked_username = username[0] + mask_char * (len(username) - 2) + username[-1]
        else:
            masked_username = username
        
        # Mask domain if needed
        if mask_domain:
            domain_parts = domain.split(".")
            domain_name = ".".join(domain_parts[:-1])
            tld = domain_parts[-1]
            
            masked_domain = mask_char * len(domain_name) + "." + tld
        else:
            masked_domain = domain
        
        return f"{masked_username}@{masked_domain}"
    
    def _mask_phone(self, value: str, options: Dict[str, Any] = None) -> str:
        """Mask a phone number"""
        options = options or {}
        
        # Default: keep country code and last 2 digits
        keep_country_code = options.get("keep_country_code", True)
        visible_last = options.get("visible_last", 2)
        mask_char = options.get("mask_char", "X")
        
        # Remove non-digit characters
        digits = re.sub(r"\D", "", value)
        
        # Handle different formats
        if len(digits) <= 4:
            # Very short number, mask it all
            return mask_char * len(digits)
        
        # Extract country code if present
        country_code = ""
        number = digits
        
        if digits.startswith("00") or digits.startswith("+"):
            # International format with 00 or +
            if digits.startswith("00"):
                country_end = 4  # 00XX
            else:
                country_end = 3  # +XX
            
            if keep_country_code:
                country_code = digits[:country_end]
                number = digits[country_end:]
            else:
                number = digits
        elif len(digits) > 10 and keep_country_code:
            # Assume first 1-3 digits are country code
            country_code = digits[:min(3, len(digits) - 7)]
            number = digits[min(3, len(digits) - 7):]
        
        # Mask the number
        if len(number) <= visible_last:
            masked_number = mask_char * len(number)
        else:
            masked_number = mask_char * (len(number) - visible_last) + number[-visible_last:]
        
        # Format result based on input format
        if "-" in value:
            # Format with hyphens
            if len(masked_number) == 10:
                return f"{country_code}{masked_number[:3]}-{masked_number[3:6]}-{masked_number[6:]}"
            else:
                return f"{country_code}{masked_number}"
        elif " " in value:
            # Format with spaces
            if len(masked_number) == 10:
                return f"{country_code}{masked_number[:3]} {masked_number[3:6]} {masked_number[6:]}"
            else:
                return f"{country_code}{masked_number}"
        elif "(" in value and ")" in value:
            # Format with parentheses for area code
            if len(masked_number) == 10:
                return f"{country_code}({masked_number[:3]}) {masked_number[3:6]}-{masked_number[6:]}"
            else:
                return f"{country_code}{masked_number}"
        else:
            # No special formatting
            return f"{country_code}{masked_number}"
    
    def _mask_address(self, value: str, options: Dict[str, Any] = None) -> str:
        """Mask an address"""
        options = options or {}
        
        # Default: replace with generic text
        replacement = options.get("replacement", "[ADDRESS REDACTED]")
        
        return replacement
    
    def _mask_name(self, value: str, options: Dict[str, Any] = None) -> str:
        """Mask a person's name"""
        options = options or {}
        
        # Default: keep initials
        keep_initials = options.get("keep_initials", True)
        mask_char = options.get("mask_char", "X")
        
        if not keep_initials:
            return mask_char * len(value)
        
        # Split into words and mask each word
        words = value.split()
        masked_words = []
        
        for word in words:
            if len(word) <= 1:
                masked_words.append(word)
            else:
                masked_words.append(word[0] + mask_char * (len(word) - 1))
        
        return " ".join(masked_words)
    
    def _mask_ip(self, value: str, options: Dict[str, Any] = None) -> str:
        """Mask an IP address"""
        options = options or {}
        
        # Default: mask last octet only
        mask_level = options.get("mask_level", 1)  # Number of octets to mask from the end
        mask_char = options.get("mask_char", "X")
        
        # Check if valid IP format
        octets = value.split(".")
        if len(octets) != 4:
            return mask_char * len(value)
        
        # Mask the specified number of octets from the end
        masked_octets = octets.copy()
        for i in range(1, min(mask_level + 1, 5)):
            masked_octets[-i] = "XXX"
        
        return ".".join(masked_octets)

# Create singleton instance
data_masking_service = DataMaskingService()

# Son güncelleme: 2025-05-20 11:04:28
# Güncelleyen: Teeksss