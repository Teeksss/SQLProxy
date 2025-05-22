from typing import Dict, Optional
from cryptography.fernet import Fernet
import jwt
from datetime import datetime, timedelta
from .audit_logger import AuditLogger
from .access_control import AccessControl

class SecurityManager:
    def __init__(self, config: Dict):
        self.config = config
        self.fernet = Fernet(config['encryption_key'])
        self.audit = AuditLogger()
        self.access_control = AccessControl()
        
    async def authenticate(self, credentials: Dict) -> Optional[Dict]:
        """User authentication."""
        try:
            # Multi-factor authentication
            if not await self._verify_mfa(credentials):
                return None
                
            # Generate JWT token
            token = self._generate_token(credentials['username'])
            
            # Log authentication
            await self.audit.log_auth_event(
                username=credentials['username'],
                success=True
            )
            
            return {
                'token': token,
                'expires_at': datetime.utcnow() + timedelta(hours=1)
            }
            
        except Exception as e:
            await self.audit.log_auth_event(
                username=credentials.get('username'),
                success=False,
                error=str(e)
            )
            return None
            
    async def authorize(self, token: str, resource: str,
                       action: str) -> bool:
        """Resource authorization."""
        try:
            # Verify token
            payload = jwt.decode(
                token,
                self.config['jwt_secret'],
                algorithms=['HS256']
            )
            
            # Check permissions
            if not await self.access_control.check_permission(
                user=payload['sub'],
                resource=resource,
                action=action
            ):
                return False
                
            # Log access
            await self.audit.log_access_event(
                username=payload['sub'],
                resource=resource,
                action=action
            )
            
            return True
            
        except Exception as e:
            await self.audit.log_access_event(
                username='unknown',
                resource=resource,
                action=action,
                error=str(e)
            )
            return False