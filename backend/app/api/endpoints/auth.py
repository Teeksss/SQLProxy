"""
Authentication API endpoints for SQL Proxy

This module provides API endpoints for user authentication and
authorization with JWT token handling.

Last updated: 2025-05-20 12:14:46
Updated by: Teeksss
"""

from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Response, Cookie, Header
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import jwt
from pydantic import BaseModel

from app.core.config import settings
from app.db.session import get_db
from app.models.user import User, UserSession
from app.services.auth import authenticate_user, create_access_token, verify_password, get_password_hash
from app.services.user import get_user_by_email, create_user, is_active_user
from app.services.email import send_password_reset_email, send_new_account_email
from app.api.deps import get_current_user, get_current_active_user
from app.schemas.user import UserCreate, UserLogin, UserResponse
from app.schemas.token import Token, TokenPayload
from app.security.rate_limit import rate_limiter
from app.security.oauth import get_oauth_providers, authenticate_oauth
from app.security.two_factor import verify_totp, generate_totp_secret, get_totp_uri

router = APIRouter()

class LoginForm(BaseModel):
    """Login form data"""
    username: str
    password: str
    remember_me: Optional[bool] = False
    totp_code: Optional[str] = None

class PasswordResetRequest(BaseModel):
    """Password reset request data"""
    email: str

class PasswordReset(BaseModel):
    """Password reset data"""
    token: str
    new_password: str

class TwoFactorSetup(BaseModel):
    """Two-factor authentication setup response"""
    secret: str
    uri: str
    qr_code_url: str

class TwoFactorVerify(BaseModel):
    """Two-factor verification data"""
    code: str

@router.post("/login", response_model=Token)
@rate_limiter(limit=10, period=60)  # 10 requests per minute
async def login_access_token(
    login_data: LoginForm,
    background_tasks: BackgroundTasks,
    response: Response,
    db: Session = Depends(get_db),
    user_agent: Optional[str] = Header(None),
    x_forwarded_for: Optional[str] = Header(None)
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    # Authenticate user
    user = authenticate_user(db, login_data.username, login_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    
    # Check if user is active
    if not is_active_user(user):
        raise HTTPException(status_code=401, detail="Inactive user")
    
    # Check 2FA if enabled
    if user.two_factor_enabled:
        if not login_data.totp_code:
            raise HTTPException(
                status_code=401,
                detail="Two-factor authentication code required",
                headers={"X-Requires-2FA": "true"},
            )
        
        # Verify TOTP code
        if not verify_totp(user.two_factor_secret, login_data.totp_code):
            raise HTTPException(status_code=401, detail="Invalid two-factor authentication code")
    
    # Create access token
    expiration = settings.ACCESS_TOKEN_EXPIRE_MINUTES
    if login_data.remember_me:
        expiration = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 30  # 30 days
    
    access_token = create_access_token(user.id, expires_delta=timedelta(minutes=expiration))
    
    # Create refresh token and session
    session_id = create_session(
        db=db,
        user_id=user.id,
        user_agent=user_agent,
        ip_address=x_forwarded_for,
        remember_me=login_data.remember_me
    )
    
    # Set session cookie
    cookie_max_age = 30 * 24 * 60 * 60 if login_data.remember_me else None  # 30 days or session
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=cookie_max_age
    )
    
    # Update user's last login
    user.last_login = datetime.utcnow()
    user.login_count += 1
    user.last_ip = x_forwarded_for
    db.commit()
    
    # Log authentication event
    background_tasks.add_task(
        log_authentication_event,
        user_id=user.id,
        success=True,
        ip_address=x_forwarded_for,
        user_agent=user_agent
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": expiration * 60,
        "user_id": user.id,
        "username": user.username
    }

@router.post("/oauth/{provider}")
async def oauth_login(
    provider: str,
    code: str,
    redirect_uri: str,
    background_tasks: BackgroundTasks,
    response: Response,
    db: Session = Depends(get_db),
    user_agent: Optional[str] = Header(None),
    x_forwarded_for: Optional[str] = Header(None)
) -> Any:
    """
    OAuth login with external provider
    """
    providers = get_oauth_providers()
    if provider not in providers:
        raise HTTPException(status_code=400, detail=f"Unsupported OAuth provider: {provider}")
    
    try:
        user_data = authenticate_oauth(provider, code, redirect_uri)
        
        # Find or create user
        user = get_user_by_email(db, email=user_data["email"])
        if not user:
            # Create new user from OAuth data
            user = create_user(
                db=db,
                user_in=UserCreate(
                    email=user_data["email"],
                    username=user_data.get("username", user_data["email"].split("@")[0]),
                    password=None,  # OAuth users don't need a password
                    full_name=user_data.get("name"),
                    is_active=True,
                    is_superuser=False
                ),
                is_oauth=True
            )
            
            # Send welcome email
            background_tasks.add_task(
                send_new_account_email,
                email_to=user.email,
                username=user.username,
                is_oauth=True,
                provider=provider
            )
        
        # Create access token
        access_token = create_access_token(user.id)
        
        # Create session
        session_id = create_session(
            db=db,
            user_id=user.id,
            user_agent=user_agent,
            ip_address=x_forwarded_for,
            oauth_provider=provider
        )
        
        # Set session cookie
        response.set_cookie(
            key="session_id",
            value=session_id,
            httponly=True,
            secure=True,
            samesite="lax"
        )
        
        # Update user's last login
        user.last_login = datetime.utcnow()
        user.login_count += 1
        user.last_ip = x_forwarded_for
        db.commit()
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user_id": user.id,
            "username": user.username
        }
        
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"OAuth authentication failed: {str(e)}")

@router.post("/refresh-token", response_model=Token)
async def refresh_token(
    response: Response,
    session_id: Optional[str] = Cookie(None),
    db: Session = Depends(get_db)
) -> Any:
    """
    Refresh access token using session cookie
    """
    if not session_id:
        raise HTTPException(status_code=401, detail="Session not found")
    
    # Find session
    session = db.query(UserSession).filter(
        UserSession.session_id == session_id,
        UserSession.is_active == True,
        UserSession.expires_at > datetime.utcnow()
    ).first()
    
    if not session:
        response.delete_cookie(key="session_id")
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    
    # Get user
    user = db.query(User).filter(User.id == session.user_id).first()
    if not user or not user.is_active:
        response.delete_cookie(key="session_id")
        raise HTTPException(status_code=401, detail="User not found or inactive")
    
    # Create new access token
    access_token = create_access_token(user.id)
    
    # Update session
    session.last_activity = datetime.utcnow()
    db.commit()
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "username": user.username
    }

@router.post("/logout")
async def logout(
    response: Response,
    session_id: Optional[str] = Cookie(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Logout user and invalidate session
    """
    # Delete session cookie
    response.delete_cookie(key="session_id")
    
    # If session_id is provided, invalidate it
    if session_id:
        session = db.query(UserSession).filter(
            UserSession.session_id == session_id,
            UserSession.user_id == current_user.id
        ).first()
        
        if session:
            session.is_active = False
            db.commit()
    
    return {"message": "Successfully logged out"}

@router.post("/register", response_model=UserResponse)
@rate_limiter(limit=5, period=3600)  # 5 requests per hour
async def register(
    user_in: UserCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
) -> Any:
    """
    Register a new user
    """
    # Check if user already exists
    user = get_user_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists"
        )
    
    # Create new user
    user = create_user(db=db, user_in=user_in)
    
    # Send welcome email
    background_tasks.add_task(
        send_new_account_email,
        email_to=user.email,
        username=user.username
    )
    
    return user

@router.post("/password-recovery")
@rate_limiter(limit=5, period=3600)  # 5 requests per hour
async def recover_password(
    request: PasswordResetRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Password recovery
    """
    user = get_user_by_email(db, email=request.email)
    
    # Always return success, even if user not found (security)
    if not user:
        return {"message": "If your email is registered, you will receive a password recovery link"}
    
    # Generate password reset token
    password_reset_token = create_access_token(
        user.id,
        expires_delta=timedelta(hours=24),
        scope="password_reset"
    )
    
    # Send password reset email
    background_tasks.add_task(
        send_password_reset_email,
        email_to=user.email,
        username=user.username,
        token=password_reset_token
    )
    
    return {"message": "If your email is registered, you will receive a password recovery link"}

@router.post("/reset-password")
@rate_limiter(limit=5, period=3600)  # 5 requests per hour
async def reset_password(
    reset: PasswordReset,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Reset password
    """
    try:
        # Decode token
        payload = jwt.decode(
            reset.token,
            settings.SECRET_KEY,
            algorithms=[settings.SECURITY_ALGORITHM]
        )
        token_data = TokenPayload(**payload)
        
        # Check if token is for password reset
        if token_data.scope != "password_reset":
            raise HTTPException(status_code=400, detail="Invalid token")
        
        # Get user
        user = db.query(User).filter(User.id == token_data.sub).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Update password
        user.hashed_password = get_password_hash(reset.new_password)
        user.password_changed_at = datetime.utcnow()
        db.commit()
        
        # Invalidate all sessions
        db.query(UserSession).filter(
            UserSession.user_id == user.id,
            UserSession.is_active == True
        ).update({"is_active": False})
        db.commit()
        
        return {"message": "Password updated successfully"}
        
    except jwt.JWTError:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

@router.post("/2fa/setup", response_model=TwoFactorSetup)
async def setup_two_factor(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Set up two-factor authentication
    """
    # Generate new TOTP secret
    secret = generate_totp_secret()
    
    # Get TOTP URI
    uri = get_totp_uri(
        secret=secret,
        username=current_user.username,
        issuer=settings.SERVER_NAME
    )
    
    # Generate QR code URL
    qr_code_url = f"https://chart.googleapis.com/chart?chs=200x200&chld=M|0&cht=qr&chl={uri}"
    
    # Store secret temporarily (not activated yet)
    current_user.two_factor_secret = secret
    db.commit()
    
    return {
        "secret": secret,
        "uri": uri,
        "qr_code_url": qr_code_url
    }

@router.post("/2fa/verify")
async def verify_two_factor(
    verification: TwoFactorVerify,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Verify and activate two-factor authentication
    """
    # Check if 2FA setup is in progress
    if not current_user.two_factor_secret:
        raise HTTPException(status_code=400, detail="Two-factor authentication not set up")
    
    # Verify code
    if not verify_totp(current_user.two_factor_secret, verification.code):
        raise HTTPException(status_code=400, detail="Invalid verification code")
    
    # Activate 2FA
    current_user.two_factor_enabled = True
    db.commit()
    
    return {"message": "Two-factor authentication activated successfully"}

@router.post("/2fa/disable")
async def disable_two_factor(
    password: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Disable two-factor authentication
    """
    # Verify password
    if not verify_password(password, current_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid password")
    
    # Disable 2FA
    current_user.two_factor_enabled = False
    current_user.two_factor_secret = None
    db.commit()
    
    return {"message": "Two-factor authentication disabled successfully"}

@router.get("/sessions")
async def list_sessions(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    List active sessions for the current user
    """
    sessions = db.query(UserSession).filter(
        UserSession.user_id == current_user.id,
        UserSession.is_active == True,
        UserSession.expires_at > datetime.utcnow()
    ).all()
    
    return [
        {
            "id": session.id,
            "device_type": session.device_type,
            "ip_address": session.ip_address,
            "created_at": session.created_at,
            "last_activity": session.last_activity,
            "user_agent": session.user_agent
        }
        for session in sessions
    ]

@router.delete("/sessions/{session_id}")
async def revoke_session(
    session_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Revoke a specific session
    """
    session = db.query(UserSession).filter(
        UserSession.id == session_id,
        UserSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session.is_active = False
    db.commit()
    
    return {"message": "Session revoked successfully"}

@router.delete("/sessions/all")
async def revoke_all_sessions(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Revoke all sessions except the current one
    """
    # Get current session ID from cookie
    session_id = db.query(UserSession.id).filter(
        UserSession.user_id == current_user.id,
        UserSession.is_active == True
    ).first()[0]
    
    # Revoke all other sessions
    db.query(UserSession).filter(
        UserSession.user_id == current_user.id,
        UserSession.id != session_id,
        UserSession.is_active == True
    ).update({"is_active": False})
    
    db.commit()
    
    return {"message": "All other sessions revoked successfully"}

def create_session(
    db: Session, 
    user_id: int, 
    user_agent: Optional[str] = None, 
    ip_address: Optional[str] = None, 
    remember_me: bool = False,
    oauth_provider: Optional[str] = None
) -> str:
    """
    Create a new user session
    
    Args:
        db: Database session
        user_id: User ID
        user_agent: User agent string
        ip_address: IP address
        remember_me: Whether to extend session expiration
        oauth_provider: OAuth provider name if OAuth login
        
    Returns:
        Session ID
    """
    import secrets
    from user_agents import parse
    
    # Generate session ID
    session_id = secrets.token_urlsafe(32)
    
    # Parse user agent
    device_type = "Unknown"
    if user_agent:
        ua = parse(user_agent)
        if ua.is_mobile:
            device_type = "Mobile"
        elif ua.is_tablet:
            device_type = "Tablet"
        elif ua.is_pc:
            device_type = "Desktop"
    
    # Set expiration
    if remember_me:
        expires_at = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    else:
        expires_at = datetime.utcnow() + timedelta(days=1)  # 1 day
    
    # Create session record
    session = UserSession(
        user_id=user_id,
        session_id=session_id,
        user_agent=user_agent,
        ip_address=ip_address,
        device_type=device_type,
        expires_at=expires_at
    )
    
    db.add(session)
    db.commit()
    
    return session_id

def log_authentication_event(
    user_id: int,
    success: bool,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> None:
    """
    Log authentication event
    
    Args:
        user_id: User ID
        success: Whether authentication was successful
        ip_address: IP address
        user_agent: User agent string
    """
    # This would typically log to a secure audit log or security monitoring system
    logger.info(
        f"Authentication {'success' if success else 'failure'} for user {user_id} "
        f"from IP {ip_address or 'unknown'} with UA {user_agent or 'unknown'}"
    )
    
    # In a real implementation, this might:
    # 1. Send to a SIEM system
    # 2. Send to a security monitoring service
    # 3. Trigger alerts for suspicious activity
    
    # For this example, we'll just log it
    pass

# Son güncelleme: 2025-05-20 12:14:46
# Güncelleyen: Teeksss