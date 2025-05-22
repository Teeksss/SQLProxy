from datetime import datetime, timedelta
from typing import Optional
import jwt
from fastapi import HTTPException, Security
from fastapi.security import OAuth2PasswordBearer
from .models import User, TokenData
from .utils import verify_password, get_password_hash

class AuthManager:
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        self.oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
        self.algorithm = "HS256"
        self.access_token_expire = timedelta(minutes=30)
        self.refresh_token_expire = timedelta(days=7)
        
    async def authenticate_user(self, username: str,
                              password: str) -> Optional[User]:
        """Kullanıcı doğrulaması yapar."""
        user = await self._get_user(username)
        if not user:
            return None
            
        if not verify_password(password, user.hashed_password):
            return None
            
        return user
        
    async def create_access_token(self, user: User) -> str:
        """Access token oluşturur."""
        expires = datetime.utcnow() + self.access_token_expire
        
        token_data = {
            "sub": user.username,
            "exp": expires,
            "type": "access"
        }
        
        return jwt.encode(
            token_data,
            self.secret_key,
            algorithm=self.algorithm
        )
        
    async def create_refresh_token(self, user: User) -> str:
        """Refresh token oluşturur."""
        expires = datetime.utcnow() + self.refresh_token_expire
        
        token_data = {
            "sub": user.username,
            "exp": expires,
            "type": "refresh"
        }
        
        return jwt.encode(
            token_data,
            self.secret_key,
            algorithm=self.algorithm
        )
        
    async def verify_token(self, token: str) -> TokenData:
        """Token doğrulaması yapar."""
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            
            username = payload.get("sub")
            if not username:
                raise HTTPException(401, "Invalid token")
                
            return TokenData(
                username=username,
                expires=payload.get("exp"),
                token_type=payload.get("type")
            )
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(401, "Token expired")
        except jwt.JWTError:
            raise HTTPException(401, "Invalid token")