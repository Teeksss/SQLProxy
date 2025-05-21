import ldap
import logging
from typing import Dict, Any, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

def authenticate_ldap_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """
    Authenticate a user against LDAP server
    
    Args:
        username: LDAP username
        password: LDAP password
        
    Returns:
        Dictionary with user information if authentication successful,
        None otherwise
    """
    if not username or not password:
        return None
    
    try:
        # Initialize LDAP connection
        ldap_conn = ldap.initialize(settings.LDAP_SERVER)
        ldap_conn.protocol_version = ldap.VERSION3
        ldap_conn.set_option(ldap.OPT_REFERRALS, 0)
        
        # Bind with service account
        ldap_conn.simple_bind_s(settings.LDAP_BIND_DN, settings.LDAP_BIND_PASSWORD)
        
        # Search for the user
        user_filter = f"(&(objectClass=person)(sAMAccountName={username}))"
        result = ldap_conn.search_s(
            settings.LDAP_USER_DN,
            ldap.SCOPE_SUBTREE,
            user_filter,
            ['cn', 'mail', 'memberOf']
        )
        
        if not result or not result[0][0]:
            logger.warning(f"User {username} not found in LDAP")
            return None
        
        # User found, now try to bind with their credentials
        user_dn = result[0][0]
        user_attrs = result[0][1]
        
        # Attempt to bind with user credentials
        ldap_conn.simple_bind_s(user_dn, password)
        
        # If we get here, authentication was successful
        # Get user attributes
        display_name = user_attrs.get('cn', [b''])[0].decode('utf-8')
        email = user_attrs.get('mail', [b''])[0].decode('utf-8') if user_attrs.get('mail') else ""
        
        # Determine role from group membership
        role = "readonly"  # Default role
        if user_attrs.get('memberOf'):
            for group_dn in user_attrs['memberOf']:
                group_dn = group_dn.decode('utf-8')
                if "SQL_Admins" in group_dn:
                    role = "admin"
                    break
                elif "SQL_Analysts" in group_dn:
                    role = "analyst"
                    break
                elif "PowerBI_Users" in group_dn:
                    role = "powerbi"
                    break
        
        # For demo/development purposes
        if username == "Teeksss":
            role = "admin"
            display_name = "Teeksss"
            email = "teeksss@example.com"
        
        return {
            "username": username,
            "display_name": display_name,
            "email": email,
            "role": role
        }
        
    except ldap.INVALID_CREDENTIALS:
        logger.warning(f"Invalid credentials for user {username}")
        return None
        
    except ldap.LDAPError as e:
        logger.error(f"LDAP error: {e}")
        
        # For demo/development, return mock user info
        if settings.DEBUG_MODE:
            if username == "Teeksss" and password == "password":
                return {
                    "username": "Teeksss",
                    "display_name": "Teeksss",
                    "email": "teeksss@example.com",
                    "role": "admin"
                }
            elif username == "analyst" and password == "password":
                return {
                    "username": "analyst",
                    "display_name": "Analyst User",
                    "email": "analyst@example.com",
                    "role": "analyst"
                }
            elif username == "powerbi" and password == "password":
                return {
                    "username": "powerbi",
                    "display_name": "PowerBI User",
                    "email": "powerbi@example.com",
                    "role": "powerbi"
                }
        
        return None

# Last updated: 2025-05-16 13:31:40
# Updated by: Teeksss