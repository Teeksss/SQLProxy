from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict, Any

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel

from app.core.config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/token")

class TokenData(BaseModel):
    username: str
    role: str
    email: Optional[str] = None

def create_access_token(data: Dict[str, Any]) -> Tuple[str, int]:
    """
    Create a new JWT token
    
    Args:
        data: Data to encode in the token
        
    Returns:
        Tuple of (token, expires_at_timestamp)
    """
    to_encode = data.copy()
    expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )
    
    # Return token and expiration timestamp
    return encoded_jwt, int(expire.timestamp())

def decode_token(token: str) -> TokenData:
    """
    Decode a JWT token
    
    Args:
        token: JWT token
        
    Returns:
        TokenData object with user information
    
    Raises:
        HTTPException: If token is invalid
    """
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        username: str = payload.get("sub")
        role: str = payload.get("role", "readonly")
        email: str = payload.get("email", "")
        
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        return TokenData(username=username, role=role, email=email)
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_user(token: str = Depends(oauth2_scheme)) -> TokenData:
    """
    Get the current user from the token
    
    Args:
        token: JWT token
        
    Returns:
        TokenData object with user information
    """
    return decode_token(token)

# Last updated: 2025-05-16 13:31:40
# Updated by: Teeksss