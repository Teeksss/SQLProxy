"""
SQL query and result masking utilities

This module provides functions for masking sensitive data in SQL queries
and query results.

Last updated: 2025-05-20 05:50:02
Updated by: Teeksss
"""

import re
import logging
from typing import Dict, List, Any, Set, Tuple, Union

logger = logging.getLogger(__name__)

# Sensitive data types with their regex patterns for detection
SENSITIVE_DATA_PATTERNS = {
    'tckn': r'^(?:(?:\d{2}[\ \.]){4}\d{2}|\d{11})$',  # Turkish national ID
    'credit_card': r'^(?:\d{4}[- ]?){3}\d{4}$|^\d{16}$',  # Credit card number
    'email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',  # Email addresses
    'phone': r'^(?:\+\d{1,3}[- ]?)?\(?(?:\d{3})?\)?[- ]?\d{3}[- ]?\d{4}$',  # Phone numbers
    'ip_address': r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$',  # IP addresses
}

# Column name patterns that suggest sensitive data
SENSITIVE_COLUMN_PATTERNS = {
    'tckn': r'^(?:tc(?:no|kimlik|_?kimlik|_?no)|tckn|tc_?id|national_?id|identity_?number)$',
    'credit_card': r'^(?:cc(?:_no|number|_num)|credit_?card(?:_no|_number|_num)?|card_?no|card_?number|card_?num|payment_?card)$',
    'email': r'^(?:e?mail|email_?addr|email_?address|e_?mail_?address|mail_?address|electronic_?mail)$',
    'phone': r'^(?:phone|phone_?no|phone_?number|tel|tel_?no|telephone|mobile|mobile_?no|gsm|cell|cell_?phone)$',
    'password': r'^(?:passwd|password|pwd|pass|sifre|hash|secret|hashed_?password)$',
    'username': r'^(?:username|user_?name|login|login_?id|login_?name|user_?id)$',
    'address': r'^(?:address|addr|location|loc|home_?address|work_?address|shipping_?address|billing_?address)$',
    'salary': r'^(?:salary|wage|income|maas|ucret|pay|compensation|earnings)$',
    'ssn': r'^(?:ssn|social_?security|social_?security_?number)$',
    'dob': r'^(?:dob|date_?of_?birth|birth_?date|birthdate|birth_?day|birthday)$',
    'api_key': r'^(?:api_?key|key|token|secret|api_?token|auth_?token|secret_?key|private_?key)$',
    'ip_address': r'^(?:ip|ip_?addr|ip_?address|ipv4|ipv6|host|ip_?host)$',
}

def detect_sensitive_columns(columns: List[str]) -> Dict[str, str]:
    """
    Detect potentially sensitive columns based on their names
    
    Args:
        columns: List of column names
        
    Returns:
        Dictionary mapping column names to their sensitive data type
    """
    sensitive_columns = {}
    
    for column in columns:
        column_lower = column.lower()
        for data_type, pattern in SENSITIVE_COLUMN_PATTERNS.items():
            if re.match(pattern, column_lower):
                sensitive_columns[column] = data_type
                break
    
    return sensitive_columns

def mask_tckn(value: str) -> str:
    """Mask a Turkish National ID number"""
    if not value:
        return value
        
    value_str = str(value)
    if len(value_str) != 11:
        return value_str  # Not a valid TCKN
        
    # Show first 5 digits, mask the rest
    return value_str[:5] + '*' * (len(value_str) - 5)

def mask_credit_card(value: str) -> str:
    """Mask a credit card number"""
    if not value:
        return value
        
    # Remove any spaces, dashes, etc.
    value_str = re.sub(r'[^0-9]', '', str(value))
    
    if len(value_str) < 13 or len(value_str) > 19:
        return value  # Not a valid credit card number
        
    # Show first 6 and last 4 digits, mask the rest
    return value_str[:6] + '*' * (len(value_str) - 10) + value_str[-4:]

def mask_email(value: str) -> str:
    """Mask an email address"""
    if not value or '@' not in value:
        return value
        
    try:
        username, domain = value.split('@')
        
        # Show first 2 chars of username, mask the rest
        if len(username) > 2:
            masked_username = username[:2] + '*' * (len(username) - 2)
        else:
            masked_username = username
            
        return f"{masked_username}@{domain}"
    except:
        return value  # Not a valid email format

def mask_phone(value: str) -> str:
    """Mask a phone number"""
    if not value:
        return value
        
    # Remove non-digits
    value_str = re.sub(r'[^0-9]', '', str(value))
    
    if len(value_str) < 7:
        return value  # Not a valid phone number
        
    # Show first 3 and last 2 digits, mask the rest
    return value_str[:3] + '*' * (len(value_str) - 5) + value_str[-2:]

def mask_ip_address(value: str) -> str:
    """Mask an IP address"""
    if not value:
        return value
        
    try:
        octets = value.split('.')
        if len(octets) != 4:
            return value  # Not a valid IPv4
            
        # Show first octet, mask the rest
        return f"{octets[0]}.***.***"
    except:
        return value

def mask_default(value: str) -> str:
    """Default masking for sensitive data"""
    if not value:
        return value
        
    value_str = str(value)
    if len(value_str) <= 4:
        return '*' * len(value_str)
    
    # Show first and last character, mask the rest
    return value_str[0] + '*' * (len(value_str) - 2) + value_str[-1]

def mask_complete(value: str) -> str:
    """Completely mask a value"""
    if not value:
        return value
        
    return '*' * len(str(value))

# Map of data types to their masking functions
MASKING_FUNCTIONS = {
    'tckn': mask_tckn,
    'credit_card': mask_credit_card,
    'email': mask_email,
    'phone': mask_phone,
    'password': mask_complete,
    'api_key': mask_complete,
    'salary': mask_complete,
    'ssn': mask_default,
    'ip_address': mask_ip_address,
    'username': mask_default,
    'address': mask_default,
    'dob': mask_default,
}

def mask_query_results(
    results: List[Dict[str, Any]], 
    sensitive_columns: Dict[str, str]
) -> List[Dict[str, Any]]:
    """
    Mask sensitive data in query results
    
    Args:
        results: List of result rows (each row is a dict mapping column names to values)
        sensitive_columns: Dictionary mapping column names to their sensitive data type
        
    Returns:
        Masked results
    """
    if not results or not sensitive_columns:
        return results
    
    masked_results = []
    
    for row in results:
        masked_row = {}
        for column, value in row.items():
            if column in sensitive_columns:
                data_type = sensitive_columns[column]
                mask_func = MASKING_FUNCTIONS.get(data_type, mask_default)
                masked_row[column] = mask_func(value)
            else:
                masked_row[column] = value
        masked_results.append(masked_row)
    
    return masked_results

def mask_query_text(query: str) -> str:
    """
    Mask potentially sensitive data in SQL query text
    
    Args:
        query: SQL query text
        
    Returns:
        Query with masked sensitive data
    """
    # Mask values in quotes that look like sensitive data
    for data_type, pattern in SENSITIVE_DATA_PATTERNS.items():
        # Find strings in single quotes
        query = re.sub(
            r"'(.*?)'", 
            lambda m: f"'{mask_string_if_sensitive(m.group(1), data_type, pattern)}'", 
            query
        )
        
        # Find strings in double quotes
        query = re.sub(
            r'"(.*?)"', 
            lambda m: f'"{mask_string_if_sensitive(m.group(1), data_type, pattern)}"', 
            query
        )
    
    return query

def mask_string_if_sensitive(value: str, data_type: str, pattern: str) -> str:
    """
    Check if a string matches a sensitive data pattern and mask it if so
    
    Args:
        value: String value to check
        data_type: Type of sensitive data
        pattern: Regex pattern to match
        
    Returns:
        Masked value if sensitive, original value otherwise
    """
    if re.match(pattern, value):
        mask_func = MASKING_FUNCTIONS.get(data_type, mask_default)
        return mask_func(value)
    return value

# Son güncelleme: 2025-05-20 05:50:02
# Güncelleyen: Teeksss