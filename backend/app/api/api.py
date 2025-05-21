"""
API Router for SQL Proxy

This module defines the API routes for the SQL Proxy application.

Last updated: 2025-05-21 07:07:17
Updated by: Teeksss
"""

from fastapi import APIRouter

from app.api.endpoints import login, users, utils, servers, queries, backups, powerbi, powerbi_data, powerbi_export, notifications, dashboards, dsn, audit, system

api_router = APIRouter()

# Login and authentication
api_router.include_router(login.router, tags=["login"])

# User management
api_router.include_router(users.router, prefix="/users", tags=["users"])

# Utility endpoints
api_router.include_router(utils.router, prefix="/utils", tags=["utils"])

# Server management
api_router.include_router(servers.router, prefix="/servers", tags=["servers"])

# Query management
api_router.include_router(queries.router, prefix="/queries", tags=["queries"])

# Backup management
api_router.include_router(backups.router, prefix="/backups", tags=["backups"])

# PowerBI endpoints
api_router.include_router(powerbi.router, prefix="/powerbi", tags=["powerbi"])
api_router.include_router(powerbi_data.router, prefix="/powerbi/data", tags=["powerbi"])
api_router.include_router(powerbi_export.router, prefix="/powerbi/export", tags=["powerbi"])

# Notification endpoints
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])

# Dashboard endpoints
api_router.include_router(dashboards.router, prefix="/dashboards", tags=["dashboards"])

# DSN endpoints
api_router.include_router(dsn.router, prefix="/dsn", tags=["dsn"])

# Audit endpoints
api_router.include_router(audit.router, prefix="/audit", tags=["audit"])

# System endpoints
api_router.include_router(system.router, prefix="/system", tags=["system"])

# Son güncelleme: 2025-05-21 07:07:17
# Güncelleyen: Teeksss