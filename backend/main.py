import uvicorn
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import logging
import os
import uuid
from typing import Dict, List, Any, Optional

from app.core.config import settings
from app.db.session import get_db, initialize_db
from app.auth.jwt import create_access_token, get_current_user, TokenData
from app.auth.ldap import authenticate_ldap_user
from app.models.user import User
from app.services.notification_service import notification_service
from app.services.data_masking import data_masking_service
from app.services.query_timeout_service import query_timeout_service

# Import routers
from app.api import servers, queries, admin, whitelist, users, powerbi

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="SQL Proxy API",
    description="API for SQL Proxy service with LDAP authentication and query management",
    version="1.0.1",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Application startup event
@app.on_event("startup")
async def startup_event():
    logger.info("Starting SQL Proxy API service")
    initialize_db()

# Application shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down SQL Proxy API service")

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "SQL Proxy API Service",
        "version": "1.0.1",
        "documentation": "/api/docs",
        "health_status": "healthy",
        "server_time": "2025-05-16 13:44:50Z"
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "1.0.1",
        "server_time": "2025-05-16 13:44:50Z"
    }

# Authentication endpoint
@app.post(f"{settings.API_V1_STR}/auth/token", response_model=Dict[str, Any])
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    try:
        # Authenticate with LDAP
        ldap_user = authenticate_ldap_user(form_data.username, form_data.password)
        
        if not ldap_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Get or create the user in the local database
        db_user = db.query(User).filter(User.username == ldap_user["username"]).first()
        
        if not db_user:
            db_user = User(
                username=ldap_user["username"],
                email=ldap_user.get("email", ""),
                display_name=ldap_user.get("display_name", ldap_user["username"]),
                role=ldap_user.get("role", "readonly"),
                is_active=True
            )
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
        
        # Create access token
        access_token, expires_at = create_access_token(
            data={"sub": db_user.username, "role": db_user.role, "email": db_user.email}
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_at": expires_at,
            "user": {
                "username": db_user.username,
                "displayName": db_user.display_name,
                "email": db_user.email,
                "role": db_user.role
            }
        }
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )

# Get current user info endpoint
@app.get(f"{settings.API_V1_STR}/auth/users/me", response_model=Dict[str, Any])
async def read_users_me(current_user: TokenData = Depends(get_current_user)):
    return {
        "username": current_user.username,
        "role": current_user.role,
        "email": current_user.email,
    }

# Include routers
app.include_router(
    servers.router,
    prefix=f"{settings.API_V1_STR}/servers",
    tags=["Servers"]
)

app.include_router(
    queries.router,
    prefix=f"{settings.API_V1_STR}/queries",
    tags=["Queries"]
)

app.include_router(
    whitelist.router,
    prefix=f"{settings.API_V1_STR}/whitelist",
    tags=["Whitelist"]
)

app.include_router(
    users.router,
    prefix=f"{settings.API_V1_STR}/users",
    tags=["Users"]
)

app.include_router(
    admin.router,
    prefix=f"{settings.API_V1_STR}/admin",
    tags=["Admin"]
)

# PowerBI router
app.include_router(
    powerbi.router,
    prefix=f"{settings.API_V1_STR}/powerbi",
    tags=["PowerBI"]
)

# Run application when invoked directly
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        reload=settings.DEBUG_MODE
    )

# Son güncelleme: 2025-05-16 13:44:50
# Güncelleyen: Teeksss