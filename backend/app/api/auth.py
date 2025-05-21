from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.auth.ldap import LDAPAuthenticator, LDAPConfig
from app.auth.jwt import generate_token, get_current_user, TokenData
from app.core.config import settings
from app.db.session import get_db

router = APIRouter()

# Initialize LDAP authenticator
ldap_config = LDAPConfig(
    server_uri=settings.LDAP_SERVER_URI,
    base_dn=settings.LDAP_BASE_DN,
    user_search_base=settings.LDAP_USER_SEARCH_BASE,
    group_search_base=settings.LDAP_GROUP_SEARCH_BASE,
    role_mappings=settings.LDAP_ROLE_MAPPINGS
)
ldap_authenticator = LDAPAuthenticator(ldap_config)

@router.post("/token", response_model=dict)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    # Authenticate with LDAP
    user = ldap_authenticator.authenticate(form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Generate JWT token
    token = generate_token(user)
    
    return {
        "access_token": token.access_token,
        "token_type": token.token_type,
        "expires_at": token.expires_at,
        "user": {
            "username": user.username,
            "email": user.email,
            "display_name": user.display_name,
            "role": user.role
        }
    }

@router.get("/users/me", response_model=dict)
async def read_users_me(current_user: TokenData = Depends(get_current_user)):
    """
    Get current user
    """
    return {
        "username": current_user.username,
        "role": current_user.role,
        "exp": current_user.exp
    }

@router.post("/ldap/test-connection", response_model=dict)
async def test_ldap_connection():
    """
    Test LDAP connection
    """
    success = ldap_authenticator.connect()
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LDAP connection failed"
        )
    
    return {"status": "ok", "message": "LDAP connection successful"}